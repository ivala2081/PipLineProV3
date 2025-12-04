// Color Utility System
// Centralized color management for consistent UI/UX

export const colorTokens = {
  // Status Colors - Consistent across all components
  status: {
    success: {
      bg: 'bg-green-50',
      text: 'text-green-700',
      border: 'border-green-200',
      icon: 'text-green-600',
      dot: 'bg-green-500',
      progress: 'bg-green-500'
    },
    warning: {
      bg: 'bg-yellow-50',
      text: 'text-yellow-700',
      border: 'border-yellow-200',
      icon: 'text-yellow-600',
      dot: 'bg-yellow-500',
      progress: 'bg-yellow-500'
    },
    error: {
      bg: 'bg-red-50',
      text: 'text-red-700',
      border: 'border-red-200',
      icon: 'text-red-600',
      dot: 'bg-red-500',
      progress: 'bg-red-500'
    },
    info: {
      bg: 'bg-blue-50',
      text: 'text-blue-700',
      border: 'border-blue-200',
      icon: 'text-blue-600',
      dot: 'bg-blue-500',
      progress: 'bg-blue-500'
    },
    neutral: {
      bg: 'bg-gray-50',
      text: 'text-gray-700',
      border: 'border-gray-200',
      icon: 'text-gray-600',
      dot: 'bg-gray-500',
      progress: 'bg-gray-500'
    }
  },

  // System Health Colors
  health: {
    healthy: {
      bg: 'bg-green-50',
      text: 'text-green-700',
      border: 'border-green-200',
      dot: 'bg-green-500',
      progress: 'bg-green-500'
    },
    degraded: {
      bg: 'bg-yellow-50',
      text: 'text-yellow-700',
      border: 'border-yellow-200',
      dot: 'bg-yellow-500',
      progress: 'bg-yellow-500'
    },
    unhealthy: {
      bg: 'bg-red-50',
      text: 'text-red-700',
      border: 'border-red-200',
      dot: 'bg-red-500',
      progress: 'bg-red-500'
    }
  },

  // Performance Colors
  performance: {
    excellent: {
      bg: 'bg-green-50',
      text: 'text-green-700',
      progress: 'bg-green-500'
    },
    good: {
      bg: 'bg-blue-50',
      text: 'text-blue-700',
      progress: 'bg-blue-500'
    },
    fair: {
      bg: 'bg-yellow-50',
      text: 'text-yellow-700',
      progress: 'bg-yellow-500'
    },
    poor: {
      bg: 'bg-red-50',
      text: 'text-red-700',
      progress: 'bg-red-500'
    }
  },

  // Usage Level Colors
  usage: {
    low: {
      bg: 'bg-green-50',
      text: 'text-green-700',
      progress: 'bg-green-500'
    },
    medium: {
      bg: 'bg-yellow-50',
      text: 'text-yellow-700',
      progress: 'bg-yellow-500'
    },
    high: {
      bg: 'bg-red-50',
      text: 'text-red-700',
      progress: 'bg-red-500'
    }
  },

  // Priority Colors
  priority: {
    high: {
      bg: 'bg-red-50',
      text: 'text-red-700',
      border: 'border-red-200'
    },
    medium: {
      bg: 'bg-yellow-50',
      text: 'text-yellow-700',
      border: 'border-yellow-200'
    },
    low: {
      bg: 'bg-gray-50',
      text: 'text-gray-700',
      border: 'border-gray-200'
    }
  }
};

// Utility functions for consistent color application
export const getStatusColor = (status: 'success' | 'warning' | 'error' | 'info' | 'neutral') => {
  return colorTokens.status[status];
};

export const getHealthColor = (health: 'healthy' | 'degraded' | 'unhealthy') => {
  return colorTokens.health[health];
};

export const getPerformanceColor = (score: number) => {
  if (score >= 90) return colorTokens.performance.excellent;
  if (score >= 70) return colorTokens.performance.good;
  if (score >= 50) return colorTokens.performance.fair;
  return colorTokens.performance.poor;
};

export const getUsageColor = (usage: number) => {
  if (usage >= 90) return colorTokens.usage.high;
  if (usage >= 60) return colorTokens.usage.medium;
  return colorTokens.usage.low;
};

export const getPriorityColor = (priority: 'high' | 'medium' | 'low') => {
  return colorTokens.priority[priority];
};

// Consistent status text mapping
export const statusText = {
  system: {
    healthy: 'Healthy',
    degraded: 'Degraded',
    unhealthy: 'Unhealthy'
  },
  performance: {
    excellent: 'Excellent',
    good: 'Good',
    fair: 'Fair',
    poor: 'Poor'
  },
  usage: {
    low: 'Low',
    medium: 'Medium',
    high: 'High'
  },
  database: {
    fast: 'Fast',
    slow: 'Slow'
  }
};
