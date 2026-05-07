'use client';

import dynamic from 'next/dynamic';

const NoteDetailContent = dynamic(() => import('./note-detail-content'), { ssr: false });

export default function NoteDetailPage() {
  return <NoteDetailContent />;
}
