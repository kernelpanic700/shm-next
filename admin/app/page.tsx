'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Users, CreditCard, FileText, TrendingUp } from 'lucide-react';
import Link from 'next/link';
import { useDashboardStats } from '@/lib/hooks/use-dashboard';
import { Skeleton } from '@/components/ui/skeleton';
import { useTranslation } from 'react-i18next';

export default function DashboardPage() {
  const { data: stats, isLoading, error } = useDashboardStats();
  const { t } = useTranslation();

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">{t('Dashboard')}</h2>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('TotalAbonents')}</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : error ? (
              <div className="text-2xl font-bold">--</div>
            ) : (
              <div className="text-2xl font-bold">{stats?.total_abonents?.toLocaleString() ?? 0}</div>
            )}
            <p className="text-xs text-muted-foreground">{t('SubscribersInSystem')}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('ActiveAbonents')}</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : error ? (
              <div className="text-2xl font-bold">--</div>
            ) : (
              <div className="text-2xl font-bold">{stats?.active_abonents?.toLocaleString() ?? 0}</div>
            )}
            <p className="text-xs text-muted-foreground">{t('CurrentlyActive')}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('TotalBalance')}</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : error ? (
              <div className="text-2xl font-bold">--</div>
            ) : (
              <div className="text-2xl font-bold">${stats?.total_balance?.toFixed(2) ?? '0.00'}</div>
            )}
            <p className="text-xs text-muted-foreground">{t('SubscriberBalances')}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('PendingTasks')}</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : error ? (
              <div className="text-2xl font-bold">--</div>
            ) : (
              <div className="text-2xl font-bold">{stats?.spool_tasks?.toLocaleString() ?? 0}</div>
            )}
            <p className="text-xs text-muted-foreground">{t('InSpoolQueue')}</p>
          </CardContent>
        </Card>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>{t('RecentActivity')}</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">{t('NoRecentActivity')}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>{t('QuickActions')}</CardTitle>
            <CardDescription>{t('CommonAdminTasks')}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2">
            <Link href="/abonents">
              <Button className="w-full justify-start" variant="outline">
                <Users className="mr-2 h-4 w-4" />
                {t('ManageAbonents')}
              </Button>
            </Link>
            <Link href="/tariffs">
              <Button className="w-full justify-start" variant="outline">
                <FileText className="mr-2 h-4 w-4" />
                {t('ManageTariffs')}
              </Button>
            </Link>
            <Link href="/payments">
              <Button className="w-full justify-start" variant="outline">
                <CreditCard className="mr-2 h-4 w-4" />
                {t('ViewPayments')}
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
