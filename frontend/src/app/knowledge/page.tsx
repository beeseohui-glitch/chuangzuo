'use client';

import dynamic from 'next/dynamic';

const KnowledgeContent = dynamic(() => import('./knowledge-content'), {
  ssr: false,
  loading: () => (
    <div className="flex h-64 items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  ),
});

export default function KnowledgePage() {
  return <KnowledgeContent />;
}
