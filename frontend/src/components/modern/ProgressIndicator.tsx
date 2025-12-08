import React from 'react';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  XCircle,
  ArrowRight
} from 'lucide-react';

interface Step {
  id: string;
  title: string;
  description?: string;
  status: 'completed' | 'current' | 'upcoming' | 'error';
  timestamp?: Date;
}

interface ProgressIndicatorProps {
  steps: Step[];
  orientation?: 'horizontal' | 'vertical';
  showTimestamps?: boolean;
  className?: string;
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  steps,
  orientation = 'horizontal',
  showTimestamps = false,
  className = ''
}) => {
  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'current':
        return <Clock className="w-5 h-5 text-gray-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'upcoming':
        return <div className="w-5 h-5 rounded-full border-2 border-muted-foreground" />;
      default:
        return <div className="w-5 h-5 rounded-full border-2 border-muted-foreground" />;
    }
  };

  const getStepColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'current':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'upcoming':
        return 'text-muted-foreground bg-muted border-border';
      default:
        return 'text-muted-foreground bg-muted border-border';
    }
  };

  const getConnectorColor = (currentStatus: string, nextStatus: string) => {
    if (currentStatus === 'completed') {
      return 'bg-green-500';
    }
    if (currentStatus === 'current') {
      return 'bg-gray-500';
    }
    if (currentStatus === 'error') {
      return 'bg-red-500';
    }
    return 'bg-muted-foreground';
  };

  if (orientation === 'vertical') {
    return (
      <div className={`space-y-4 ${className}`}>
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-start gap-4">
            <div className="flex flex-col items-center">
              <div className={`p-2 rounded-full border ${getStepColor(step.status)}`}>
                {getStepIcon(step.status)}
              </div>
              {index < steps.length - 1 && (
                <div 
                  className={`w-0.5 h-8 mt-2 ${getConnectorColor(step.status, steps[index + 1]?.status)}`}
                />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h4 className={`font-medium ${step.status === 'upcoming' ? 'text-muted-foreground' : 'text-foreground'}`}>
                  {step.title}
                </h4>
                {step.status === 'current' && (
                  <Badge variant="outline" className="text-gray-600 border-gray-200">
                    In Progress
                  </Badge>
                )}
                {step.status === 'error' && (
                  <Badge variant="destructive">
                    Error
                  </Badge>
                )}
              </div>
              {step.description && (
                <p className="text-sm text-muted-foreground mt-1">
                  {step.description}
                </p>
              )}
              {showTimestamps && step.timestamp && (
                <p className="text-xs text-muted-foreground mt-1">
                  {step.timestamp.toLocaleString()}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <Card className={className}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center text-center">
                <div className={`p-3 rounded-full border ${getStepColor(step.status)} mb-2`}>
                  {getStepIcon(step.status)}
                </div>
                <h4 className={`text-sm font-medium ${step.status === 'upcoming' ? 'text-muted-foreground' : 'text-foreground'}`}>
                  {step.title}
                </h4>
                {step.description && (
                  <p className="text-xs text-muted-foreground mt-1 max-w-24">
                    {step.description}
                  </p>
                )}
                {showTimestamps && step.timestamp && (
                  <p className="text-xs text-muted-foreground mt-1">
                    {step.timestamp.toLocaleDateString()}
                  </p>
                )}
              </div>
              {index < steps.length - 1 && (
                <div className="flex-1 flex items-center justify-center mx-4">
                  <div 
                    className={`h-0.5 w-full ${getConnectorColor(step.status, steps[index + 1]?.status)}`}
                  />
                  <ArrowRight className="w-4 h-4 text-muted-foreground mx-2" />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

// Circular progress component
export const CircularProgress: React.FC<{
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  showValue?: boolean;
  label?: string;
  className?: string;
}> = ({
  value,
  max = 100,
  size = 120,
  strokeWidth = 8,
  showValue = true,
  label,
  className = ''
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const progress = (value / max) * circumference;
  const percentage = Math.round((value / max) * 100);

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="transform -rotate-90"
        >
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="hsl(var(--muted))"
            strokeWidth={strokeWidth}
            fill="none"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="hsl(var(--primary))"
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
            className="transition-all duration-300 ease-in-out"
          />
        </svg>
        {showValue && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl font-bold text-foreground">
              {percentage}%
            </span>
          </div>
        )}
      </div>
      {label && (
        <p className="text-sm text-muted-foreground mt-2 text-center">
          {label}
        </p>
      )}
    </div>
  );
};
