'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';
import { useUserStore } from '@/stores/user-store';
import { useSidebarStore } from '@/stores/sidebar-store';
import { useIsDesktop } from '@/hooks/use-media-query';
import { Sidebar } from './sidebar';
import { Header } from './header';
import { BottomNav } from './bottom-nav';
import { cn } from '@/lib/utils';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, checkAuth } = useAuthStore();
  const { setEnterprise, setQuota } = useUserStore();
  const { isOpen, close } = useSidebarStore();
  const isDesktop = useIsDesktop();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  // Close sidebar on mobile when navigating
  useEffect(() => {
    if (!isDesktop) {
      close();
    }
  }, [isDesktop, close]);

  // Initialize enterprise data in dev mode
  useEffect(() => {
    if (user?.enterprise_id) {
      setEnterprise({
        id: user.enterprise_id,
        name: '智创科技',
        plan: 'free',
        quota_monthly: 5,
        quota_used: 2,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
      setQuota({
        monthly_limit: 5,
        used: 2,
        reset_date: '2026-06-01',
      });
    }
  }, [user, setEnterprise, setQuota]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop sidebar */}
      {isDesktop && <Sidebar />}

      {/* Mobile sidebar overlay */}
      {!isDesktop && isOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/50"
            onClick={close}
          />
          <div className="fixed inset-y-0 left-0 z-50 w-64">
            <Sidebar />
          </div>
        </>
      )}

      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className={cn(
          'flex-1 overflow-y-auto',
          isDesktop ? 'p-6' : 'p-4 pb-20'
        )}>
          {children}
        </main>
      </div>

      {/* Bottom nav for mobile */}
      {!isDesktop && <BottomNav />}
    </div>
  );
}
