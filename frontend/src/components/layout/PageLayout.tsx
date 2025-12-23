import React from 'react';
import clsx from 'clsx';

export type PageTheme = 'plain' | 'slate' | 'slate-blue' | 'slate-indigo';

const themeClass: Record<PageTheme, string> = {
  plain: 'bg-transparent',
  // Neutral default with subtle depth
  slate: 'bg-gradient-to-br from-slate-50 via-white to-slate-100',
  // Used for Trust-like sections: still subtle, but with a blue hint
  'slate-blue': 'bg-gradient-to-br from-slate-50 via-white to-blue-50',
  // Subtle indigo hint for finance/utility modals
  'slate-indigo': 'bg-gradient-to-br from-slate-50 via-white to-indigo-50',
};

type PageLayoutProps = {
  children: React.ReactNode;
  /**
   * Controls the background theme. Keep this small and intentional to avoid layout drift.
   */
  theme?: PageTheme;
  /**
   * When true, ensures the page area is at least viewport height.
   * Note: ModernLayout already provides a min height; this is mainly for standalone sections.
   */
  minHeightScreen?: boolean;
  /**
   * Optional extra classes for the outer wrapper.
   */
  className?: string;
};

export default function PageLayout({
  children,
  theme = 'slate',
  minHeightScreen = false,
  className,
}: PageLayoutProps) {
  return (
    <div
      className={clsx(
        'w-full',
        themeClass[theme],
        minHeightScreen && 'min-h-screen',
        className
      )}
    >
      {children}
    </div>
  );
}


