import React from 'react';
import { useTranslation } from 'react-i18next';
import {
    RefreshCw,
    Eye,
    Calendar
} from 'lucide-react';
import {
    LineChart as RechartsLineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';
import { UnifiedSection } from '../../design-system/UnifiedSection';
import { UnifiedButton } from '../../design-system/UnifiedButton';

interface DashboardRevenueProps {
    revenueTrends: any;
    refreshing: boolean;
    onRefresh: () => void;
    onViewDetails: () => void;
    formatCurrency: (value: number, currency: string) => string;
}

export const DashboardRevenue: React.FC<DashboardRevenueProps> = ({
    revenueTrends,
    refreshing,
    onRefresh,
    onViewDetails,
    formatCurrency
}) => {
    const { t } = useTranslation();

    if (!revenueTrends) return null;

    return (
        <UnifiedSection title={t('dashboard.revenue_trends')} description={t('dashboard.performance_over_time')}>
            <div className='business-chart'>
                <div className='business-chart-header'>
                    <div>
                        <h3 className='business-chart-title'>{t('dashboard.revenue_trends')}</h3>
                        <p className='business-chart-subtitle'>{t('dashboard.revenue_performance_time')}</p>
                    </div>
                    <div className='business-chart-actions'>
                        <UnifiedButton
                            variant="outline"
                            size="sm"
                            onClick={onRefresh}
                            disabled={refreshing}
                            className="flex items-center gap-2"
                        >
                            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                            {refreshing ? t('common.refreshing') : t('common.refresh')}
                        </UnifiedButton>
                        <UnifiedButton
                            variant="outline"
                            size="sm"
                            onClick={onViewDetails}
                        >
                            <Eye className='w-4 h-4 mr-2' />
                            {t('dashboard.view_details')}
                        </UnifiedButton>
                    </div>
                </div>
                <div className='h-80'>
                    <ResponsiveContainer width="100%" height="100%">
                        <RechartsLineChart data={revenueTrends.data.daily_revenue}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis dataKey="date" stroke="#6b7280" fontSize={12} />
                            <YAxis stroke="#6b7280" fontSize={12} tickFormatter={(value) => formatCurrency(value, '₺')} />
                            <Tooltip
                                content={({ active, payload, label }) => {
                                    if (active && payload && payload.length) {
                                        const data = payload[0].payload;
                                        return (
                                            <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-4 min-w-[200px]">
                                                <div className="space-y-2">
                                                    <div className="flex items-center gap-2">
                                                        <Calendar className="h-4 w-4 text-slate-500" />
                                                        <span className="font-semibold text-slate-900">
                                                            {new Date(label).toLocaleDateString('en-US', {
                                                                weekday: 'long',
                                                                year: 'numeric',
                                                                month: 'long',
                                                                day: 'numeric'
                                                            })}
                                                        </span>
                                                    </div>

                                                    <div className="border-t border-slate-100 pt-2 space-y-1">
                                                        <div className="flex justify-between items-center">
                                                            <span className="text-sm text-slate-600">{t('dashboard.net_revenue')}:</span>
                                                            <span className={`font-semibold ${data.amount >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                                {formatCurrency(data.amount || 0, '₺')}
                                                            </span>
                                                        </div>

                                                        {data.deposits !== undefined && (
                                                            <div className="flex justify-between items-center">
                                                                <span className="text-sm text-slate-600">{t('dashboard.deposits')}:</span>
                                                                <span className="text-sm font-medium text-green-600">
                                                                    +{formatCurrency(data.deposits, '₺')}
                                                                </span>
                                                            </div>
                                                        )}

                                                        {data.withdrawals !== undefined && (
                                                            <div className="flex justify-between items-center">
                                                                <span className="text-sm text-slate-600">{t('dashboard.withdrawals')}:</span>
                                                                <span className="text-sm font-medium text-red-600">
                                                                    -{formatCurrency(data.withdrawals, '₺')}
                                                                </span>
                                                            </div>
                                                        )}

                                                        {data.transaction_count !== undefined && (
                                                            <div className="flex justify-between items-center">
                                                                <span className="text-sm text-slate-600">{t('dashboard.transactions')}:</span>
                                                                <span className="text-sm font-medium text-slate-700">
                                                                    {data.transaction_count}
                                                                </span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    }
                                    return null;
                                }}
                            />
                            <Line
                                type="monotone"
                                dataKey="amount"
                                stroke="#3b82f6"
                                strokeWidth={3}
                                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                                activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
                            />
                        </RechartsLineChart>
                    </ResponsiveContainer>
                </div>
                <div className='business-chart-legend'>
                    <div className='business-chart-legend-item'>
                        <div className='business-chart-legend-color bg-gray-500'></div>
                        <span className='business-chart-legend-label'>{t('dashboard.net_revenue')}</span>
                        <span className='business-chart-legend-value'>₺{revenueTrends.data.metrics.total_revenue?.toLocaleString()}</span>
                    </div>
                </div>
            </div>
        </UnifiedSection>
    );
};
