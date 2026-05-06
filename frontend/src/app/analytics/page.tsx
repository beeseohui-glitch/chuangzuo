'use client';

import dynamic from 'next/dynamic';

const AnalyticsContent = dynamic(() => import('./analytics-content'), {
  ssr: false,
  loading: () => (
    <div className="flex h-64 items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  ),
});

export default function AnalyticsPage() {
  return <AnalyticsContent />;
}
