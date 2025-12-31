/**
 * Request Batching Utility
 * Batches multiple API requests into a single request to reduce network overhead
 */
import { ApiClient } from './apiClient';

export interface BatchedRequest {
  id: string;
  url: string;
  method: string;
  params?: Record<string, any>;
  resolve: (value: any) => void;
  reject: (error: any) => void;
}

export class RequestBatcher {
  private batch: BatchedRequest[] = [];
  private batchTimeout: number = 50; // ms - wait for more requests
  private maxBatchSize: number = 10;
  private timer: NodeJS.Timeout | null = null;
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient, batchTimeout: number = 50) {
    this.apiClient = apiClient;
    this.batchTimeout = batchTimeout;
  }

  /**
   * Add a request to the batch
   */
  public add<T>(
    url: string,
    method: string = 'GET',
    params?: Record<string, any>
  ): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const request: BatchedRequest = {
        id: `${Date.now()}-${Math.random()}`,
        url,
        method,
        params,
        resolve,
        reject,
      };

      this.batch.push(request);

      // If batch is full, execute immediately
      if (this.batch.length >= this.maxBatchSize) {
        this.executeBatch();
        return;
      }

      // Otherwise, schedule execution
      if (!this.timer) {
        this.timer = setTimeout(() => {
          this.executeBatch();
        }, this.batchTimeout);
      }
    });
  }

  /**
   * Execute all batched requests
   */
  private async executeBatch(): Promise<void> {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }

    if (this.batch.length === 0) {
      return;
    }

    const currentBatch = [...this.batch];
    this.batch = [];

    try {
      // Group requests by endpoint pattern
      const grouped = this.groupRequests(currentBatch);

      // Execute each group
      for (const [groupKey, requests] of Object.entries(grouped)) {
        await this.executeGroup(requests);
      }
    } catch (error) {
      // If batch execution fails, reject all requests
      currentBatch.forEach((request) => {
        request.reject(error);
      });
    }
  }

  /**
   * Group requests by endpoint pattern
   */
  private groupRequests(requests: BatchedRequest[]): Record<string, BatchedRequest[]> {
    const groups: Record<string, BatchedRequest[]> = {};

    requests.forEach((request) => {
      // Extract base path (e.g., /api/v1/transactions)
      const basePath = request.url.split('?')[0];
      const groupKey = `${request.method}:${basePath}`;

      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(request);
    });

    return groups;
  }

  /**
   * Execute a group of similar requests
   */
  private async executeGroup(requests: BatchedRequest[]): Promise<void> {
    if (requests.length === 1) {
      // Single request - execute normally
      const request = requests[0];
      try {
        const response = await this.apiClient.request(request.url, request.method, request.params);
        request.resolve(response);
      } catch (error) {
        request.reject(error);
      }
      return;
    }

    // Multiple requests - try to batch them
    // For GET requests, we can combine query params
    if (requests.every((r) => r.method === 'GET')) {
      await this.executeBatchGet(requests);
    } else {
      // For other methods, execute individually
      await Promise.all(
        requests.map(async (request) => {
          try {
            const response = await this.apiClient.request(
              request.url,
              request.method,
              request.params
            );
            request.resolve(response);
          } catch (error) {
            request.reject(error);
          }
        })
      );
    }
  }

  /**
   * Execute batched GET requests
   */
  private async executeBatchGet(requests: BatchedRequest[]): Promise<void> {
    // For now, execute in parallel (can be optimized further)
    await Promise.all(
      requests.map(async (request) => {
        try {
          const response = await this.apiClient.get(request.url, request.params);
          request.resolve(response);
        } catch (error) {
          request.reject(error);
        }
      })
    );
  }

  /**
   * Flush pending requests immediately
   */
  public flush(): void {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    this.executeBatch();
  }
}

// Global batcher instance
let globalBatcher: RequestBatcher | null = null;

export function getRequestBatcher(apiClient: ApiClient): RequestBatcher {
  if (!globalBatcher) {
    globalBatcher = new RequestBatcher(apiClient);
  }
  return globalBatcher;
}
