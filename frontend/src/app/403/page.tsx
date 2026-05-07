'use client';

import Link from 'next/link';
import { ShieldX, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function ForbiddenPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="flex flex-col items-center gap-6 text-center">
        <div className="rounded-full bg-destructive/10 p-6">
          <ShieldX className="h-16 w-16 text-destructive" />
        </div>
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">403 - 无权访问</h1>
          <p className="text-muted-foreground max-w-md">
            抱歉，您没有权限访问此页面。该页面仅限平台管理员使用。
          </p>
        </div>
        <Button render={<Link href="/dashboard" />}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回工作台
        </Button>
      </div>
    </div>
  );
}
