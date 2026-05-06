'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Sparkles, Eye, EyeOff, Mail, Lock } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isDevMode, setIsDevMode] = useState(false);

  useEffect(() => {
    const devMode = localStorage.getItem('dev_mode') !== 'false';
    setIsDevMode(devMode);
    if (devMode) {
      setEmail('dev@example.com');
      setPassword('123456');
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const result = await login({ email, password });
    if (result.success) {
      router.push('/dashboard');
    } else {
      setError(result.error || '登录失败');
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* 左侧品牌区 */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-gradient-to-br from-primary/10 via-background to-primary/5 items-center justify-center p-12">
        <div className="max-w-md space-y-8">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
              <Sparkles className="h-6 w-6 text-primary" />
            </div>
            <h1 className="text-3xl font-bold">智创笔记</h1>
          </div>
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold text-foreground/90">
              AI 驱动的多平台内容创作系统
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              基于三层 Agent 架构，为企业提供小红书、公众号、抖音等平台的智能内容创作服务。
              从素材检索到合规审核，一站式完成高质量内容生产。
            </p>
          </div>
          <div className="grid grid-cols-3 gap-4 pt-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-primary">8+</p>
              <p className="text-xs text-muted-foreground mt-1">标题策略</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-primary">5维</p>
              <p className="text-xs text-muted-foreground mt-1">AI味评分</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-primary">3级</p>
              <p className="text-xs text-muted-foreground mt-1">合规校验</p>
            </div>
          </div>
        </div>
      </div>

      {/* 右侧登录表单 */}
      <div className="flex w-full lg:w-1/2 items-center justify-center p-8">
        <div className="w-full max-w-sm space-y-8">
          {/* 移动端 Logo */}
          <div className="lg:hidden flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <h1 className="text-2xl font-bold">智创笔记</h1>
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-bold">登录</h2>
            <p className="text-muted-foreground">
              登录您的账户以开始创作
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm">邮箱</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-sm">密码</Label>
                <button type="button" className="text-xs text-primary hover:underline cursor-pointer">
                  忘记密码？
                </button>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <Button type="submit" className="w-full" size="lg" disabled={isLoading}>
              {isLoading ? '登录中...' : '登录'}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            还没有账户？{' '}
            <button className="text-primary hover:underline font-medium">
              联系管理员开通
            </button>
          </p>

          {isDevMode && (
            <div className="rounded-lg bg-muted/50 border p-3 text-center text-xs text-muted-foreground">
              开发模式已启用 — 任意邮箱密码即可登录
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
