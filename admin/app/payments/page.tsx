'use client';

export const dynamic = 'force-dynamic';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus } from 'lucide-react';
import { DataTable } from '@/components/ui/data-table';
import { usePayments } from '@/lib/hooks/use-payments';
import { useAbonents } from '@/lib/hooks/use-abonents';
import { ColumnDef } from '@tanstack/react-table';
import { Payment, Abonent } from '@/lib/api';
import { toast } from 'sonner';
import { Skeleton } from '@/components/ui/skeleton';
import { format } from 'date-fns';
import { de, enUS, ru } from 'date-fns/locale';
import { useTranslation } from 'react-i18next';

const getDateLocale = (language: string) => {
  if (language.startsWith('en')) return enUS;
  if (language.startsWith('de')) return de;
  return ru;
};

export default function PaymentsPage() {
  const { t, i18n } = useTranslation();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [minAmount, setMinAmount] = useState<string>('');
  const [maxAmount, setMaxAmount] = useState<string>('');

  const { data: payments = [], isLoading, isError, refetch } = usePayments();
  const { data: abonents = [] } = useAbonents();
  const numberLocale = i18n.language.startsWith('en') ? 'en-US' : 'ru-RU';
  const dateLocale = getDateLocale(i18n.language);
  const columns = useMemo<ColumnDef<Payment>[]>(() => [
    {
      accessorKey: 'id',
      header: 'ID',
      cell: ({ row }) => {
        const id = row.getValue('id') as string;
        return <span className="font-mono text-xs">{id.slice(0, 8)}...</span>;
      },
    },
    {
      accessorKey: 'abonent_id',
      header: t('Abonent'),
      cell: ({ row, table }) => {
        const abonentId = row.getValue('abonent_id') as string;
        const abonents = (table.options.meta as any)?.abonents as Abonent[] || [];
        const abonent = abonents.find((a: Abonent) => a.id === abonentId);
        return <span>{abonent?.full_name || abonent?.phone || abonentId.slice(0, 8)}</span>;
      },
    },
    {
      accessorKey: 'amount',
      header: t('Amount'),
      cell: ({ row }) => {
        const amount = parseFloat(String(row.getValue('amount') || 0));
        const currency = row.original.currency || 'RUB';
        return <span className="font-medium">{amount.toLocaleString(numberLocale, { minimumFractionDigits: 2 })} {currency}</span>;
      },
    },
    {
      accessorKey: 'status',
      header: t('Status'),
      cell: ({ row }) => {
        const status = row.getValue('status') as string;
        const statusMap: Record<string, { label: string; className: string }> = {
          NEW: { label: t('PaymentStatusNew'), className: 'bg-gray-100 text-gray-800' },
          PENDING: { label: t('PaymentStatusPending'), className: 'bg-yellow-100 text-yellow-800' },
          PROCESSING: { label: t('PaymentStatusProcessing'), className: 'bg-blue-100 text-blue-800' },
          COMPLETED: { label: t('PaymentStatusCompleted'), className: 'bg-green-100 text-green-800' },
          FAILED: { label: t('PaymentStatusFailed'), className: 'bg-red-100 text-red-800' },
          REFUNDED: { label: t('PaymentStatusRefunded'), className: 'bg-purple-100 text-purple-800' },
          CANCELLED: { label: t('PaymentStatusCancelled'), className: 'bg-gray-100 text-gray-800' },
        };
        const config = statusMap[status] || { label: status, className: 'bg-gray-100 text-gray-800' };
        return <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.className}`}>{config.label}</span>;
      },
    },
    {
      accessorKey: 'payment_method',
      header: t('PaymentMethod'),
      cell: ({ row }) => {
        const method = row.getValue('payment_method') as string;
        const methodMap: Record<string, string> = {
          card: t('PaymentMethodCard'),
          cash: t('PaymentMethodCash'),
          bank_transfer: t('PaymentMethodBankTransfer'),
          auto_debit: t('PaymentMethodAutoDebit'),
        };
        return methodMap[method] || method || '-';
      },
    },
    {
      accessorKey: 'created_at',
      header: t('Date'),
      cell: ({ row }) => {
        const date = row.getValue('created_at') as string;
        return format(new Date(date), 'dd MMM yyyy HH:mm', { locale: dateLocale });
      },
    },
  ], [dateLocale, numberLocale, t]);

  // Keep filters client-side until the payments API exposes matching query params.
  const filteredPayments = useMemo(() => {
    return payments.filter((payment) => {
      if (statusFilter !== 'all' && payment.status !== statusFilter) {
        return false;
      }
      if (dateFrom && new Date(payment.created_at) < new Date(dateFrom)) {
        return false;
      }
      if (dateTo && new Date(payment.created_at) > new Date(dateTo)) {
        return false;
      }
      const amount = parseFloat(String(payment.amount || 0));
      if (minAmount && amount < parseFloat(minAmount)) {
        return false;
      }
      if (maxAmount && amount > parseFloat(maxAmount)) {
        return false;
      }
      return true;
    });
  }, [payments, statusFilter, dateFrom, dateTo, minAmount, maxAmount]);

  if (isLoading) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <h2 className="text-3xl font-bold tracking-tight">{t('Payments')}</h2>
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex-1 p-8">
        <p className="text-destructive">{t('PaymentsLoadError')}</p>
        <Button variant="outline" onClick={() => refetch()} className="mt-4">{t('TryAgain')}</Button>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">{t('Payments')}</h2>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <Input
          placeholder={t('DateFromPlaceholder')}
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
        />
        <Input
          placeholder={t('DateToPlaceholder')}
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
        />
        <select 
          className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 appearance-none"
          value={statusFilter} 
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">{t('AllStatuses')}</option>
          <option value="NEW">{t('PaymentStatusNew')}</option>
          <option value="PENDING">{t('PaymentStatusPending')}</option>
          <option value="PROCESSING">{t('PaymentStatusProcessing')}</option>
          <option value="COMPLETED">{t('PaymentStatusCompleted')}</option>
          <option value="FAILED">{t('PaymentStatusFailed')}</option>
          <option value="REFUNDED">{t('PaymentStatusRefunded')}</option>
          <option value="CANCELLED">{t('PaymentStatusCancelled')}</option>
        </select>
        <Input
          placeholder={t('AmountFrom')}
          type="number"
          value={minAmount}
          onChange={(e) => setMinAmount(e.target.value)}
        />
        <Input
          placeholder={t('AmountTo')}
          type="number"
          value={maxAmount}
          onChange={(e) => setMaxAmount(e.target.value)}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('PaymentHistory')}</CardTitle>
          <CardDescription>{t('TotalPaymentsCount', { count: filteredPayments.length })}</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable 
            columns={columns} 
            data={filteredPayments} 
            searchKey="id"
            meta={{ abonents }}
          />
        </CardContent>
      </Card>
    </div>
  );
}
