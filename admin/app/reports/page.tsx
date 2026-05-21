'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Download, Calendar, Users, CreditCard, TrendingUp, DollarSign, Activity } from 'lucide-react';
import { useAbonents } from '@/lib/hooks/use-abonents';
import { useTariffs } from '@/lib/hooks/use-tariffs';
import { usePayments } from '@/lib/hooks/use-payments';
import { useSpoolTasks } from '@/lib/hooks/use-spool-tasks';
import { Skeleton } from '@/components/ui/skeleton';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
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

const periodOptions = [
  { value: 'today', label: 'Сегодня' },
  { value: 'week', label: 'Неделя' },
  { value: 'month', label: 'Месяц' },
  { value: 'quarter', label: 'Квартал' },
  { value: 'year', label: 'Год' },
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export default function ReportsPage() {
  const [period, setPeriod] = useState('month');
  const [customDateFrom, setCustomDateFrom] = useState('');
  const [customDateTo, setCustomDateTo] = useState('');

  const { data: abonents = [], isLoading: abonentsLoading } = useAbonents();
  const { data: tariffs = [], isLoading: tariffsLoading } = useTariffs();
  const { data: payments = [], isLoading: paymentsLoading } = usePayments();
  const { data: tasks = [], isLoading: tasksLoading } = useSpoolTasks();

  const isLoading = abonentsLoading || tariffsLoading || paymentsLoading || tasksLoading;

  // Метрики
  const metrics = useMemo(() => {
    const totalAbonents = abonents.length;
    const activeAbonents = abonents.filter(a => a.status === 'ACTIVE' || a.status === 'active').length;
    const totalBalance = abonents.reduce((sum, a) => sum + parseFloat(String(a.balance || 0)), 0);
    const totalPayments = payments.reduce((sum, p) => sum + parseFloat(String(p.amount || 0)), 0);
    const pendingTasks = tasks.filter(t => t.status === 'NEW' || t.status === 'PROCESSING').length;
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

  // Данные для графиков
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
        date: format(date, 'dd.MM', { locale: ru }),
        balance: Math.round(dayBalance * 100) / 100,
        payments: dayPayments.reduce((sum, p) => sum + parseFloat(String(p.amount || 0)), 0),
      });
    }
    return data;
  }, [payments, abonents]);

  // Распределение по статусам
  const statusData = useMemo(() => {
    const statusMap: Record<string, number> = {};
    abonents.forEach(a => {
      const status = a.status.toUpperCase();
      statusMap[status] = (statusMap[status] || 0) + 1;
    });
    return Object.entries(statusMap).map(([name, value]) => ({ name, value }));
  }, [abonents]);

  // Топ тарифы
  const topTariffs = useMemo(() => {
    return tariffs.slice(0, 5).map(t => ({
      name: t.name,
      price: t.price,
    }));
  }, [tariffs]);

  const exportCSV = () => {
    const csvContent = [
      ['Метрика', 'Значение'],
      ['Всего абонентов', metrics.totalAbonents],
      ['Активных абонентов', metrics.activeAbonents],
      ['Общий баланс', metrics.totalBalance],
      ['Сумма платежей', metrics.totalPayments],
      ['Задач в SPOOL', metrics.pendingTasks],
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
        <h2 className="text-3xl font-bold tracking-tight">Отчёты</h2>
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
        <h2 className="text-3xl font-bold tracking-tight">Отчёты</h2>
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
            Экспорт CSV
          </Button>
        </div>
      </div>

      {/* Метрики */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Всего абонентов</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalAbonents}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Активных абонентов</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{metrics.activeAbonents}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Общий баланс</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalBalance.toLocaleString('ru-RU')} ₽</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Платежи за период</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totalPayments.toLocaleString('ru-RU')} ₽</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Задач в SPOOL</CardTitle>
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

      {/* Графики */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Динамика баланса и платежей</CardTitle>
            <CardDescription>Последние 30 дней</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="balance" stroke="#8884d8" name="Баланс" />
                <Line type="monotone" dataKey="payments" stroke="#82ca9d" name="Платежи" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Распределение по статусам</CardTitle>
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
          <CardTitle>Топ тарифы</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topTariffs}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="price" fill="#8884d8" name="Цена" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}