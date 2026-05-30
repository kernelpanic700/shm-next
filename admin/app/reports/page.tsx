'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, Users, CreditCard, TrendingUp, DollarSign, Activity } from 'lucide-react';
import { useAbonents } from '@/lib/hooks/use-abonents';
import { useTariffs } from '@/lib/hooks/use-tariffs';
import { usePayments } from '@/lib/hooks/use-payments';
import { useSpoolTasks } from '@/lib/hooks/use-spool-tasks';
import { Skeleton } from '@/components/ui/skeleton';
import { format } from 'date-fns';
import { de, enUS, ru } from 'date-fns/locale';
import { useTranslation } from 'react-i18next';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Abonent, SpoolTask } from '@/lib/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const getDateLocale = (language: string) => {
  if (language.startsWith('de')) return de;
  if (language.startsWith('en')) return enUS;
  return ru;
};

export default function ReportsPage() {
  const { t, i18n } = useTranslation();
  const [period, setPeriod] = useState('month');

  const { data: abonents = [], isLoading: abonentsLoading } = useAbonents();
  const { data: tariffs = [], isLoading: tariffsLoading } = useTariffs();
  const { data: payments = [], isLoading: paymentsLoading } = usePayments();
  const { data: tasks = [], isLoading: tasksLoading } = useSpoolTasks();

  const isLoading = abonentsLoading || tariffsLoading || paymentsLoading || tasksLoading;
  const dateLocale = getDateLocale(i18n.language);
  const numberLocale = i18n.language.startsWith('en') ? 'en-US' : i18n.language.startsWith('de') ? 'de-DE' : 'ru-RU';
  const periodOptions = useMemo(() => [
    { value: 'today', label: t('Today') },
    { value: 'week', label: t('Week') },
    { value: 'month', label: t('Month') },
    { value: 'quarter', label: t('Quarter') },
    { value: 'year', label: t('Year') },
  ], [t]);
  const statusLabels = useMemo<Record<string, string>>(() => ({
    ACTIVE: t('Active'),
    INACTIVE: t('Inactive'),
    BLOCKED: t('Blocked'),
    SUSPENDED: t('Suspended'),
  }), [t]);

  const metrics = useMemo(() => {
    const totalAbonents = abonents.length;
    const activeAbonents = abonents.filter((a: Abonent) => a.status === 'ACTIVE' || a.status === 'active').length;
    const totalBalance = abonents.reduce((sum, a) => sum + parseFloat(String(a.balance || 0)), 0);
    const totalPayments = payments.reduce((sum, p) => sum + parseFloat(String(p.amount || 0)), 0);
    const pendingTasks = tasks.filter((t: SpoolTask) => t.status === 'NEW' || t.status === 'PROCESSING').length;
    const arpu = totalAbonents > 0 ? totalPayments / totalAbonents : 0;

    return {
      totalAbonents,
      activeAbonents,
      totalBalance,
      totalPayments,
      pendingTasks,
      arpu,
    };
  }, [abonents, payments, tasks]);

  const dailyData = useMemo(() => {
    const days = 30;
    const data = [];
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const dateStr = format(date, 'yyyy-MM-dd');
      
      const dayPayments = payments.filter(p => p.created_at.startsWith(dateStr));
      const dayBalance = abonents.length > 0 
        ? abonents.reduce((sum, a) => sum + parseFloat(String(a.balance || 0)), 0) / abonents.length 
        : 0;
      
      data.push({
        date: format(date, 'dd.MM', { locale: dateLocale }),
        balance: Math.round(dayBalance * 100) / 100,
        payments: dayPayments.reduce((sum, p) => sum + parseFloat(String(p.amount || 0)), 0),
      });
    }
    return data;
  }, [payments, abonents, dateLocale]);

  const statusData = useMemo(() => {
    const statusMap: Record<string, number> = {};
    abonents.forEach(a => {
      const status = a.status.toUpperCase();
      statusMap[status] = (statusMap[status] || 0) + 1;
    });
    return Object.entries(statusMap).map(([name, value]) => ({ name: statusLabels[name] || name, value }));
  }, [abonents, statusLabels]);

  const topTariffs = useMemo(() => {
    return tariffs.slice(0, 5).map(t => ({
      name: t.name,
      price: t.price,
    }));
  }, [tariffs]);

  const exportCSV = () => {
    const csvContent = [
      [t('Metric'), t('Value')],
      [t('TotalAbonents'), metrics.totalAbonents],
      [t('ActiveAbonents'), metrics.activeAbonents],
      [t('TotalBalance'), metrics.totalBalance],
      [t('TotalPayments'), metrics.totalPayments],
      [t('PendingTasks'), metrics.pendingTasks],
      ['ARPU', metrics.arpu.toFixed(2)],
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `report-${format(new Date(), 'yyyy-MM-dd')}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (isLoading) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <h2 className="text-3xl font-bold tracking-tight">{t('ReportsTitle')}</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">{t('ReportsTitle')}</h2>
        <div className="flex gap-2">
          <select
            className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
          >
            {periodOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <Button variant="outline" onClick={exportCSV}>
            <Download className="mr-2 h-4 w-4" />
            {t('ExportCSV')}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('TotalAbonents')}</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalAbonents}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('ActiveAbonents')}</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{metrics.activeAbonents}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('TotalBalance')}</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalBalance.toLocaleString(numberLocale)} ₽</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('PaymentsForPeriod')}</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalPayments.toLocaleString(numberLocale)} ₽</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('PendingTasks')}</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{metrics.pendingTasks}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ARPU</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.arpu.toFixed(2)} ₽</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t('BalancePaymentsDynamics')}</CardTitle>
            <CardDescription>{t('Last30Days')}</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="balance" stroke="#8884d8" name={t('Balance')} />
                <Line type="monotone" dataKey="payments" stroke="#82ca9d" name={t('Payments')} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('StatusDistribution')}</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${percent ? (percent * 100).toFixed(0) : 0}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('TopTariffs')}</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topTariffs}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="price" fill="#8884d8" name={t('Price')} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
