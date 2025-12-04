/**
 * Advanced Request Batching System
 * Reduces API calls by batching multiple requests into single calls
 */

interface BatchedRequest {
  id: string;
  url: string;
  options: RequestInit;
  timestamp: number;
  resolve: (value: any) => void;
  reject: (error: any) => void;
}

interface BatchConfig {
  maxBatchSize: number;
  batchDelay: number;
  maxWaitTime: number;
}

class RequestBatcher {
  private batches: Map<string, BatchedRequest[]> = new Map();
  private timers: Map<string, NodeJS.Timeout> = new Map();
  private config: BatchConfig;

  constructor(config: Partial<BatchConfig> = {}) {
    this.config = {
      maxBatchSize: 10,
      batchDelay: 50, // 50ms
      maxWaitTime: 200, // 200ms max wait
      ...config
    };
  }

  /**
   * Add a request to a batch
   */
  async batchRequest<T>(
    url: string,
    options: RequestInit = {},
    batchKey?: string
  ): Promise<T> {
    const key = batchKey || this.getBatchKey(url, options);
    
    return new Promise((resolve, reject) => {
      const request: BatchedRequest = {
        id: this.generateRequestId(),
        url,
        options,
        timestamp: Date.now(),
        resolve,
        reject
      };

      // Add to batch
      if (!this.batches.has(key)) {
        this.batches.set(key, []);
      }
      this.batches.get(key)!.push(request);

      // Set up batch execution
      this.scheduleBatch(key);

      // Set timeout for individual request
      setTimeout(() => {
        this.executeBatch(key);
      }, this.config.maxWaitTime);
    });
  }

  /**
   * Generate a unique batch key based on URL and method
   */
  private getBatchKey(url: string, options: RequestInit): string {
    const method = options.method || 'GET';
    const baseUrl = url.split('?')[0]; // Remove query params
    return `${method}:${baseUrl}`;
  }

  /**
   * Generate unique request ID
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Schedule batch execution
   */
  private scheduleBatch(key: string): void {
    // Clear existing timer
    if (this.timers.has(key)) {
      clearTimeout(this.timers.get(key)!);
    }

    // Set new timer
    const timer = setTimeout(() => {
      this.executeBatch(key);
    }, this.config.batchDelay);

    this.timers.set(key, timer);
  }

  /**
   * Execute a batch of requests
   */
  private async executeBatch(key: string): Promise<void> {
    const batch = this.batches.get(key);
    if (!batch || batch.length === 0) return;

    // Clear timer and remove batch
    if (this.timers.has(key)) {
      clearTimeout(this.timers.get(key)!);
      this.timers.delete(key);
    }
    this.batches.delete(key);

    // Execute requests in parallel
    const promises = batch.map(async (request) => {
      try {
        const response = await fetch(request.url, request.options);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        request.resolve(data);
      } catch (error) {
        request.reject(error);
      }
    });

    await Promise.allSettled(promises);
  }

  /**
   * Create a batched API client
   */
  createBatchedClient() {
    return {
      get: <T>(url: string, batchKey?: string) => 
        this.batchRequest<T>(url, { method: 'GET' }, batchKey),
      
      post: <T>(url: string, data?: any, batchKey?: string) =>
        this.batchRequest<T>(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: data ? JSON.stringify(data) : undefined
        }, batchKey),
      
      put: <T>(url: string, data?: any, batchKey?: string) =>
        this.batchRequest<T>(url, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: data ? JSON.stringify(data) : undefined
        }, batchKey),
      
      delete: <T>(url: string, batchKey?: string) =>
        this.batchRequest<T>(url, { method: 'DELETE' }, batchKey)
    };
  }

  /**
   * Get batch statistics
   */
  getStats() {
    const totalBatches = this.batches.size;
    const totalRequests = Array.from(this.batches.values())
      .reduce((sum, batch) => sum + batch.length, 0);
    
    return {
      activeBatches: totalBatches,
      pendingRequests: totalRequests,
      config: this.config
    };
  }

  /**
   * Clear all pending batches
   */
  clear(): void {
    // Clear all timers
    for (const timer of this.timers.values()) {
      clearTimeout(timer);
    }
    this.timers.clear();

    // Reject all pending requests
    for (const batch of this.batches.values()) {
      for (const request of batch) {
        request.reject(new Error('Batch cleared'));
      }
    }
    this.batches.clear();
  }
}

// Global request batcher instance
export const requestBatcher = new RequestBatcher({
  maxBatchSize: 15,
  batchDelay: 75, // 75ms for better batching
  maxWaitTime: 300 // 300ms max wait
});

// Export the class and instance
export default RequestBatcher;
export { RequestBatcher, type BatchedRequest, type BatchConfig };
