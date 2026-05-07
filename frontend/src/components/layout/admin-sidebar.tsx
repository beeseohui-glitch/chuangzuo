'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useSidebarStore } from '@/stores/sidebar-store';
import { useIsDesktop } from '@/hooks/use-media-query';
import {
  LayoutDashboard,
  Globe,
  Building2,
  FileText,
  ShieldCheck,
  Users,
  BarChart3,
  ChevronLeft,
  Shield,
  ArrowLeft,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip';

const navItems = [
  { title: '概览', href: '/admin', icon: LayoutDashboard },
  { title: '公共知识库', href: '/admin/knowledge/public', icon: Globe },
  { title: '行业知识库', href: '/admin/knowledge/industry', icon: Building2 },
  { title: '内置模板', href: '/admin/templates', icon: FileText },
  { title: '合规词库', href: '/admin/compliance', icon: ShieldCheck },
  { title: '租户管理', href: '/admin/tenants', icon: Users },
  { title: '数据统计', href: '/admin/stats', icon: BarChart3 },
];

export function AdminSidebar() {
  const pathname = usePathname();
  const { isCollapsed, toggleCollapse, close } = useSidebarStore();
  const isDesktop = useIsDesktop();
  const collapsed = isDesktop && isCollapsed;

  return (
    <aside
      className={cn(
        'flex flex-col h-screen border-r transition-all duration-300',
        'border-amber-200/20 bg-amber-950/10',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Brand header */}
      <div className="flex items-center justify-between p-4 border-b border-amber-200/20">
        {!collapsed && (
          <Link href="/admin" className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-amber-500" />
            <span className="font-semibold text-amber-100">平台管理后台</span>
          </Link>
        )}
        {collapsed && (
          <Shield className="h-6 w-6 text-amber-500 mx-auto" />
        )}
        {isDesktop && (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleCollapse}
            className={cn(
              'h-8 w-8 text-amber-200 hover:bg-amber-500/20',
              collapsed && 'hidden'
            )}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Nav links */}
      <ScrollArea className="flex-1 py-2">
        <nav className="space-y-1 px-2">
          <TooltipProvider delay={0}>
            {navItems.map((item) => {
              const isActive = item.href === '/admin'
                ? pathname === '/admin'
                : pathname.startsWith(item.href);
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
                      ? 'bg-amber-500/20 text-amber-100 font-medium'
                      : 'text-amber-200/70 hover:bg-amber-500/10 hover:text-amber-100'
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

      {/* Bottom: back to tenant + version */}
      <div className="border-t border-amber-200/20 p-3 space-y-2">
        {!collapsed && (
          <Link
            href="/dashboard"
            className="flex items-center gap-2 px-3 py-2 rounded-md text-sm text-amber-200/70 hover:bg-amber-500/10 hover:text-amber-100 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>返回租户后台</span>
          </Link>
        )}
        {collapsed && (
          <TooltipProvider delay={0}>
            <Tooltip>
              <TooltipTrigger
                render={
                  <Link
                    href="/dashboard"
                    className="flex items-center justify-center py-2 text-amber-200/70 hover:text-amber-100"
                  >
                    <ArrowLeft className="h-4 w-4" />
                  </Link>
                }
              />
              <TooltipContent side="right">返回租户后台</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
        <div
          className={cn(
            'flex items-center text-xs text-amber-200/50',
            collapsed ? 'justify-center' : 'justify-between'
          )}
        >
          {collapsed ? (
            <TooltipProvider delay={0}>
              <Tooltip>
                <TooltipTrigger render={<span>v2.2</span>} />
                <TooltipContent side="right">平台管理后台 v2.2</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ) : (
            <>
              <span>平台管理后台</span>
              <span>v2.2</span>
            </>
          )}
        </div>
      </div>
    </aside>
  );
}
