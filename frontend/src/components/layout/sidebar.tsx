'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useSidebarStore } from '@/stores/sidebar-store';
import { useUserStore } from '@/stores/user-store';
import { useIsDesktop } from '@/hooks/use-media-query';
import {
  LayoutDashboard,
  PenLine,
  BookOpen,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip';
import { UsageQuota } from '@/components/shared/usage-quota';

const navItems = [
  { title: '工作台', href: '/dashboard', icon: LayoutDashboard },
  { title: '创作中心', href: '/create', icon: PenLine },
  { title: '知识库', href: '/knowledge', icon: BookOpen },
  { title: '数据看板', href: '/analytics', icon: BarChart3 },
  { title: '设置', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { isCollapsed, toggleCollapse, close } = useSidebarStore();
  const { version, quota } = useUserStore();
  const isDesktop = useIsDesktop();

  // On mobile, sidebar is always expanded (not collapsed)
  const collapsed = isDesktop && isCollapsed;

  return (
    <aside
      className={cn(
        'flex flex-col h-screen border-r border-sidebar-border bg-sidebar transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      <div className="flex items-center justify-between p-4 border-b border-sidebar-border">
        {!collapsed && (
          <Link href="/dashboard" className="flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-sidebar-primary" />
            <span className="font-semibold text-sidebar-foreground">智创笔记</span>
          </Link>
        )}
        {isDesktop && (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleCollapse}
            className="h-8 w-8 text-sidebar-foreground hover:bg-sidebar-accent"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        )}
      </div>

      <ScrollArea className="flex-1 py-2">
        <nav className="space-y-1 px-2">
          <TooltipProvider delay={0}>
            {navItems.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
              const Icon = item.icon;

              const linkContent = (
                <Link
                  href={item.href}
                  onClick={() => {
                    if (!isDesktop) close();
                  }}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
                    isActive
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                  )}
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  {!collapsed && <span>{item.title}</span>}
                </Link>
              );

              if (collapsed) {
                return (
                  <Tooltip key={item.href}>
                    <TooltipTrigger render={linkContent} />
                    <TooltipContent side="right">{item.title}</TooltipContent>
                  </Tooltip>
                );
              }

              return <div key={item.href}>{linkContent}</div>;
            })}
          </TooltipProvider>
        </nav>
      </ScrollArea>

      {/* Bottom info */}
      <div className="border-t border-sidebar-border p-3 space-y-3">
        {!collapsed && (
          <UsageQuota
            used={quota.used}
            total={quota.monthly_limit}
            label="本月创作额度"
          />
        )}
        <div
          className={cn(
            'flex items-center text-xs text-muted-foreground',
            collapsed ? 'justify-center' : 'justify-between'
          )}
        >
          {collapsed ? (
            <TooltipProvider delay={0}>
              <Tooltip>
                <TooltipTrigger render={<span>{version}</span>} />
                <TooltipContent side="right">智创笔记 {version}</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ) : (
            <>
              <span>智创笔记</span>
              <span>{version}</span>
            </>
          )}
        </div>
      </div>
    </aside>
  );
}
