'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';
import { useSidebarStore } from '@/stores/sidebar-store';
import { useIsDesktop } from '@/hooks/use-media-query';
import { AdminSidebar } from '@/components/layout/admin-sidebar';
import { AdminHeader } from '@/components/layout/admin-header';
import { cn } from '@/lib/utils';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, checkAuth } = useAuthStore();
  const { isOpen, close } = useSidebarStore();
  const isDesktop = useIsDesktop();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Auto-close sidebar on mobile when switching to desktop
  useEffect(() => {
    if (isDesktop) close();
  }, [isDesktop, close]);

  // Route guard
  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    if (user && user.role !== 'platform_admin' && user.role !== 'platform_operator') {
      router.push('/403');
    }
  }, [isLoading, isAuthenticated, user, router]);

  // Loading
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber-500 border-t-transparent" />
      </div>
    );
  }

  // Not authenticated or not admin
  if (!isAuthenticated || !user || (user.role !== 'platform_admin' && user.role !== 'platform_operator')) {
    return null;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop sidebar */}
      {isDesktop && <AdminSidebar />}

      {/* Mobile sidebar overlay */}
      {!isDesktop && isOpen && (
        <>
          <div className="fixed inset-0 z-40 bg-black/50" onClick={close} />
          <div className="fixed inset-y-0 left-0 z-50 w-64">
            <AdminSidebar />
          </div>
        </>
      )}

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <AdminHeader />
        <main className={cn(
          'flex-1 overflow-auto',
          isDesktop ? 'p-6' : 'p-4 pb-20'
        )}>
          {children}
        </main>
      </div>
    </div>
  );
}
