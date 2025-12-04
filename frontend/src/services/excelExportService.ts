/**
 * Excel Export Service
 * Handles comprehensive data export to Excel with multiple worksheets
 */

import * as XLSX from 'xlsx';
import { dashboardService } from './dashboardService';

export interface ExcelExportData {
  transactions: any[];
  clients: any[];
  analytics: any;
  systemPerformance: any;
  exchangeRates: any;
  commissionAnalytics: any;
}

export class ExcelExportService {
  /**
   * Generate comprehensive Excel report with multiple worksheets
   */
  static async generateComprehensiveReport(timeRange: string = 'all'): Promise<void> {
    try {
      console.log('🔄 Generating comprehensive Excel report...');
      
      // Fetch all data in parallel
      const [
        dashboardStats,
        systemPerformance,
        dataQuality,
        securityMetrics,
        commissionAnalytics,
        exchangeRates
      ] = await Promise.all([
        dashboardService.getDashboardStats(timeRange),
        dashboardService.getSystemPerformance(),
        dashboardService.getDataQuality(),
        dashboardService.getSecurityMetrics(),
        dashboardService.getCommissionAnalytics(timeRange),
        dashboardService.getExchangeRates()
      ]);

      // Create new workbook
      const workbook = XLSX.utils.book_new();

      // 1. Dashboard Overview Sheet
      this.addDashboardOverviewSheet(workbook, dashboardStats);

      // 2. Transactions Sheet
      this.addTransactionsSheet(workbook, dashboardStats?.recent_transactions || []);

      // 3. Analytics Sheet
      this.addAnalyticsSheet(workbook, dashboardStats);

      // 4. System Performance Sheet
      this.addSystemPerformanceSheet(workbook, systemPerformance);

      // 5. Exchange Rates Sheet
      this.addExchangeRatesSheet(workbook, exchangeRates);

      // 6. Commission Analytics Sheet
      this.addCommissionAnalyticsSheet(workbook, commissionAnalytics);

      // 7. Data Quality Sheet
      this.addDataQualitySheet(workbook, dataQuality);

      // 8. Security Metrics Sheet
      this.addSecurityMetricsSheet(workbook, securityMetrics);

      // Generate filename with timestamp
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      const filename = `PipLinePro_Report_${timeRange}_${timestamp}.xlsx`;

      // Save the workbook
      XLSX.writeFile(workbook, filename);
      
      console.log('✅ Excel report generated successfully:', filename);
    } catch (error) {
      console.error('❌ Error generating Excel report:', error);
      throw error;
    }
  }

  /**
   * Add Dashboard Overview Sheet
   */
  private static addDashboardOverviewSheet(workbook: XLSX.WorkBook, data: any): void {
    const overviewData = [
      ['PipLinePro Dashboard Overview'],
      ['Generated:', new Date().toLocaleString()],
      [''],
      ['Key Metrics'],
      ['Total Revenue', data?.total_revenue || 0],
      ['Total Transactions', data?.total_transactions || 0],
      ['Active Clients', data?.active_clients || 0],
      ['Average Transaction', data?.average_transaction || 0],
      [''],
      ['Revenue Breakdown'],
      ['Deposits', data?.total_deposits || 0],
      ['Withdrawals', data?.total_withdrawals || 0],
      ['Net Revenue', data?.net_revenue || 0],
      [''],
      ['Performance Metrics'],
      ['Success Rate', data?.success_rate || 0],
      ['Growth Rate', data?.growth_rate || 0],
      ['Client Satisfaction', data?.client_satisfaction || 0]
    ];

    const worksheet = XLSX.utils.aoa_to_sheet(overviewData);
    this.formatWorksheet(worksheet, 'A1:B20');
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Dashboard Overview');
  }

  /**
   * Add Transactions Sheet
   */
  private static addTransactionsSheet(workbook: XLSX.WorkBook, transactions: any[]): void {
    if (!transactions || transactions.length === 0) {
      const emptyData = [['No transaction data available']];
      const worksheet = XLSX.utils.aoa_to_sheet(emptyData);
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Transactions');
      return;
    }

    // Prepare transaction data
    const transactionData = [
      ['Transaction ID', 'Client Name', 'Amount', 'Currency', 'Status', 'Date', 'PSP', 'Category']
    ];

    transactions.forEach(transaction => {
      transactionData.push([
        transaction.id || '',
        transaction.client_name || '',
        transaction.amount || 0,
        transaction.currency || 'TL',
        transaction.status || '',
        transaction.date ? new Date(transaction.date).toLocaleDateString() : '',
        transaction.psp || '',
        transaction.category || ''
      ]);
    });

    const worksheet = XLSX.utils.aoa_to_sheet(transactionData);
    this.formatWorksheet(worksheet, 'A1:H' + (transactions.length + 1));
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Transactions');
  }

  /**
   * Add Analytics Sheet
   */
  private static addAnalyticsSheet(workbook: XLSX.WorkBook, data: any): void {
    const analyticsData = [
      ['Analytics Summary'],
      ['Generated:', new Date().toLocaleString()],
      [''],
      ['Revenue Analytics'],
      ['Total Revenue', data?.total_revenue || 0],
      ['Monthly Growth', data?.monthly_growth || 0],
      ['Yearly Growth', data?.yearly_growth || 0],
      [''],
      ['Transaction Analytics'],
      ['Total Transactions', data?.total_transactions || 0],
      ['Successful Transactions', data?.successful_transactions || 0],
      ['Failed Transactions', data?.failed_transactions || 0],
      ['Success Rate', data?.success_rate || 0],
      [''],
      ['Client Analytics'],
      ['Total Clients', data?.total_clients || 0],
      ['Active Clients', data?.active_clients || 0],
      ['New Clients (30d)', data?.new_clients_30d || 0],
      ['Client Retention Rate', data?.client_retention_rate || 0]
    ];

    const worksheet = XLSX.utils.aoa_to_sheet(analyticsData);
    this.formatWorksheet(worksheet, 'A1:B20');
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Analytics');
  }

  /**
   * Add System Performance Sheet
   */
  private static addSystemPerformanceSheet(workbook: XLSX.WorkBook, data: any): void {
    const performanceData = [
      ['System Performance Metrics'],
      ['Generated:', new Date().toLocaleString()],
      [''],
      ['CPU Usage', data?.cpu_usage || 0, '%'],
      ['Memory Usage', data?.memory_usage || 0, '%'],
      ['Disk Usage', data?.disk_usage || 0, '%'],
      ['Network Latency', data?.network_latency || 0, 'ms'],
      [''],
      ['Database Performance'],
      ['Query Response Time', data?.db_query_time || 0, 'ms'],
      ['Connection Pool', data?.db_connections || 0, 'connections'],
      ['Cache Hit Rate', data?.cache_hit_rate || 0, '%'],
      [''],
      ['Application Metrics'],
      ['Response Time', data?.response_time || 0, 'ms'],
      ['Throughput', data?.throughput || 0, 'requests/min'],
      ['Error Rate', data?.error_rate || 0, '%'],
      ['Uptime', data?.uptime || 0, '%']
    ];

    const worksheet = XLSX.utils.aoa_to_sheet(performanceData);
    this.formatWorksheet(worksheet, 'A1:C20');
    XLSX.utils.book_append_sheet(workbook, worksheet, 'System Performance');
  }

  /**
   * Add Exchange Rates Sheet
   */
  private static addExchangeRatesSheet(workbook: XLSX.WorkBook, data: any): void {
    const ratesData = [
      ['Exchange Rates'],
      ['Generated:', new Date().toLocaleString()],
      [''],
      ['Currency Pair', 'Rate', 'Last Updated', 'Age (minutes)', 'Status']
    ];

    if (data?.success && data.rates) {
      Object.entries(data.rates).forEach(([key, rate]: [string, any]) => {
        ratesData.push([
          rate.currency_pair || key,
          rate.rate || 0,
          rate.last_updated || '',
          rate.age_minutes || 0,
          rate.is_stale ? 'Stale' : 'Fresh'
        ]);
      });
    } else {
      ratesData.push(['No exchange rate data available', '', '', '', '']);
    }

    const worksheet = XLSX.utils.aoa_to_sheet(ratesData);
    this.formatWorksheet(worksheet, 'A1:E10');
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Exchange Rates');
  }

  /**
   * Add Commission Analytics Sheet
   */
  private static addCommissionAnalyticsSheet(workbook: XLSX.WorkBook, data: any): void {
    const commissionData = [
      ['Commission Analytics'],
      ['Generated:', new Date().toLocaleString()],
      [''],
      ['PSP', 'Total Volume', 'Total Commission', 'Commission Rate', 'Transaction Count']
    ];

    if (data?.success && data.data?.psp_commission) {
      data.data.psp_commission.forEach((psp: any) => {
        commissionData.push([
          psp.psp || 'Unknown',
          psp.total_volume || 0,
          psp.total_commission || 0,
          psp.commission_rate || 0,
          psp.transaction_count || 0
        ]);
      });
    } else {
      commissionData.push(['No commission data available', '', '', '', '']);
    }

    const worksheet = XLSX.utils.aoa_to_sheet(commissionData);
    this.formatWorksheet(worksheet, 'A1:E20');
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Commission Analytics');
  }

  /**
   * Add Data Quality Sheet
   */
  private static addDataQualitySheet(workbook: XLSX.WorkBook, data: any): void {
    const qualityData = [
      ['Data Quality Metrics'],
      ['Generated:', new Date().toLocaleString()],
      [''],
      ['Metric', 'Value', 'Status'],
      ['Data Completeness', data?.completeness || 0, '%'],
      ['Data Accuracy', data?.accuracy || 0, '%'],
      ['Data Consistency', data?.consistency || 0, '%'],
      ['Data Timeliness', data?.timeliness || 0, '%'],
      [''],
      ['Quality Issues'],
      ['Missing Values', data?.missing_values || 0],
      ['Duplicate Records', data?.duplicates || 0],
      ['Invalid Formats', data?.invalid_formats || 0],
      ['Data Conflicts', data?.conflicts || 0]
    ];

    const worksheet = XLSX.utils.aoa_to_sheet(qualityData);
    this.formatWorksheet(worksheet, 'A1:C15');
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Data Quality');
  }

  /**
   * Add Security Metrics Sheet
   */
  private static addSecurityMetricsSheet(workbook: XLSX.WorkBook, data: any): void {
    const securityData = [
      ['Security Metrics'],
      ['Generated:', new Date().toLocaleString()],
      [''],
      ['Metric', 'Today', 'This Week', 'This Month'],
      ['Failed Logins', data?.failed_logins?.today || 0, data?.failed_logins?.week || 0, data?.failed_logins?.month || 0],
      ['Blocked IPs', data?.blocked_ips?.today || 0, data?.blocked_ips?.week || 0, data?.blocked_ips?.month || 0],
      ['Security Alerts', data?.security_alerts?.today || 0, data?.security_alerts?.week || 0, data?.security_alerts?.month || 0],
      [''],
      ['Access Control'],
      ['Active Sessions', data?.active_sessions || 0],
      ['Admin Users', data?.admin_users || 0],
      ['Regular Users', data?.regular_users || 0],
      ['Locked Accounts', data?.locked_accounts || 0]
    ];

    const worksheet = XLSX.utils.aoa_to_sheet(securityData);
    this.formatWorksheet(worksheet, 'A1:D15');
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Security Metrics');
  }

  /**
   * Format worksheet with styling
   */
  private static formatWorksheet(worksheet: XLSX.WorkSheet, range: string): void {
    // Set column widths
    const cols = [
      { wch: 20 }, // Column A
      { wch: 15 }, // Column B
      { wch: 15 }, // Column C
      { wch: 15 }, // Column D
      { wch: 15 }  // Column E
    ];
    worksheet['!cols'] = cols;

    // Add borders and formatting
    const rangeObj = XLSX.utils.decode_range(range);
    for (let R = rangeObj.s.r; R <= rangeObj.e.r; ++R) {
      for (let C = rangeObj.s.c; C <= rangeObj.e.c; ++C) {
        const cellAddress = XLSX.utils.encode_cell({ r: R, c: C });
        if (!worksheet[cellAddress]) continue;
        
        worksheet[cellAddress].s = {
          border: {
            top: { style: 'thin' },
            bottom: { style: 'thin' },
            left: { style: 'thin' },
            right: { style: 'thin' }
          },
          alignment: { horizontal: 'center', vertical: 'center' }
        };
      }
    }
  }

  /**
   * Export specific data type to Excel
   */
  static async exportSpecificData(type: 'transactions' | 'clients' | 'analytics' | 'all', timeRange: string = 'all'): Promise<void> {
    switch (type) {
      case 'all':
        await this.generateComprehensiveReport(timeRange);
        break;
      case 'transactions':
        await this.exportTransactions(timeRange);
        break;
      case 'clients':
        await this.exportClients(timeRange);
        break;
      case 'analytics':
        await this.exportAnalytics(timeRange);
        break;
      default:
        throw new Error('Invalid export type');
    }
  }

  /**
   * Export only transactions
   */
  private static async exportTransactions(timeRange: string): Promise<void> {
    const data = await dashboardService.getDashboardStats(timeRange);
    const workbook = XLSX.utils.book_new();
    this.addTransactionsSheet(workbook, data?.recent_transactions || []);
    
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    XLSX.writeFile(workbook, `Transactions_${timeRange}_${timestamp}.xlsx`);
  }

  /**
   * Export only clients
   */
  private static async exportClients(timeRange: string): Promise<void> {
    // This would need to be implemented based on your clients API
    console.log('Client export not yet implemented');
  }

  /**
   * Export only analytics
   */
  private static async exportAnalytics(timeRange: string): Promise<void> {
    const data = await dashboardService.getDashboardStats(timeRange);
    const workbook = XLSX.utils.book_new();
    this.addAnalyticsSheet(workbook, data);
    
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    XLSX.writeFile(workbook, `Analytics_${timeRange}_${timestamp}.xlsx`);
  }
}

export default ExcelExportService;
