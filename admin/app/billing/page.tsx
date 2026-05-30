'use client';

export const dynamic = 'force-dynamic';

import { FormEvent, useCallback, useMemo, useState } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { format } from 'date-fns';
import { de, enUS, ru } from 'date-fns/locale';
import { Calendar, CreditCard, Play, RefreshCw, Send, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { DataTable } from '@/components/ui/data-table';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { useAbonents } from '@/lib/hooks/use-abonents';
import { useRunAbonentWithdraw, useRunBillingCycle } from '@/lib/hooks/use-billing';
import { useInvoiceAction, useInvoices, usePayInvoice } from '@/lib/hooks/use-invoices';
import { Abonent, Invoice } from '@/lib/api';

type InvoiceTableMeta = {
  abonents: Abonent[];
  onAction: (invoiceId: string, action: 'issue' | 'send' | 'cancel') => void;
  onPay: (invoiceId: string) => void;
  pendingId?: string;
};

const getDateLocale = (language: string) => {
  if (language.startsWith('en')) return enUS;
  if (language.startsWith('de')) return de;
  return ru;
};

export default function BillingPage() {
  const { t, i18n } = useTranslation();
  const [periodStart, setPeriodStart] = useState('');
  const [periodEnd, setPeriodEnd] = useState('');
  const [cycleLimit, setCycleLimit] = useState('100');
  const [withdrawAbonentId, setWithdrawAbonentId] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [invoiceAbonentFilter, setInvoiceAbonentFilter] = useState('all');

  const { data: abonents = [] } = useAbonents();
  const selectedWithdrawAbonentId = withdrawAbonentId || abonents[0]?.id || '';
  const invoiceFilters = useMemo(
    () => ({
      status: statusFilter === 'all' ? undefined : statusFilter,
      abonentId: invoiceAbonentFilter === 'all' ? undefined : invoiceAbonentFilter,
      perPage: 100,
    }),
    [invoiceAbonentFilter, statusFilter]
  );

  const { data: invoicePage, isLoading, isError, refetch } = useInvoices(invoiceFilters);
  const invoices = invoicePage?.items || [];
  const runCycle = useRunBillingCycle();
  const runWithdraw = useRunAbonentWithdraw();
  const invoiceAction = useInvoiceAction();
  const payInvoice = usePayInvoice();

  const pendingInvoiceId =
    invoiceAction.variables?.invoiceId || payInvoice.variables?.invoiceId;
  const dateLocale = getDateLocale(i18n.language);
  const formatInvoiceDate = useCallback((value?: string | null) => {
    if (!value) return '-';
    return format(new Date(value), 'dd MMM yyyy', { locale: dateLocale });
  }, [dateLocale]);
  const statusConfig = useMemo<Record<Invoice['status'], { label: string; className: string }>>(() => ({
    DRAFT: { label: t('InvoiceStatusDraft'), className: 'bg-gray-100 text-gray-800' },
    ISSUED: { label: t('InvoiceStatusIssued'), className: 'bg-blue-100 text-blue-800' },
    SENT: { label: t('InvoiceStatusSent'), className: 'bg-cyan-100 text-cyan-800' },
    PAID: { label: t('InvoiceStatusPaid'), className: 'bg-green-100 text-green-800' },
    OVERDUE: { label: t('InvoiceStatusOverdue'), className: 'bg-red-100 text-red-800' },
    CANCELLED: { label: t('InvoiceStatusCancelled'), className: 'bg-gray-100 text-gray-700' },
  }), [t]);
  const invoiceColumns = useMemo<ColumnDef<Invoice>[]>(() => [
    {
      accessorKey: 'id',
      header: t('Invoice'),
      cell: ({ row }) => <span className="font-mono text-xs">{row.original.id.slice(0, 8)}...</span>,
    },
    {
      accessorKey: 'abonent_id',
      header: t('Abonent'),
      cell: ({ row, table }) => {
        const meta = table.options.meta as InvoiceTableMeta | undefined;
        const abonent = meta?.abonents.find((item) => item.id === row.original.abonent_id);
        return <span>{abonent?.full_name || abonent?.phone || row.original.abonent_id.slice(0, 8)}</span>;
      },
    },
    {
      accessorKey: 'amount',
      header: t('Amount'),
      cell: ({ row }) => (
        <span className="font-medium">
          {Number(row.original.amount).toLocaleString(i18n.language === 'en' ? 'en-US' : 'ru-RU', { minimumFractionDigits: 2 })} {row.original.currency}
        </span>
      ),
    },
    {
      accessorKey: 'status',
      header: t('Status'),
      cell: ({ row }) => {
        const config = statusConfig[row.original.status] || { label: row.original.status, className: 'bg-gray-100 text-gray-800' };
        return <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.className}`}>{config.label}</span>;
      },
    },
    {
      accessorKey: 'period_start',
      header: t('Period'),
      cell: ({ row }) => `${formatInvoiceDate(row.original.period_start)} - ${formatInvoiceDate(row.original.period_end)}`,
    },
    {
      accessorKey: 'due_date',
      header: t('DueDate'),
      cell: ({ row }) => formatInvoiceDate(row.original.due_date),
    },
    {
      accessorKey: 'description',
      header: t('Description'),
      cell: ({ row }) => <span className="line-clamp-2 max-w-[260px]">{row.original.description || '-'}</span>,
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row, table }) => {
        const meta = table.options.meta as InvoiceTableMeta | undefined;
        const invoice = row.original;
        const pending = meta?.pendingId === invoice.id;
        const closed = invoice.status === 'PAID' || invoice.status === 'CANCELLED';

        return (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={pending || invoice.status !== 'DRAFT'} onClick={() => meta?.onAction(invoice.id, 'issue')} title={t('IssueInvoice')}>
              <Play className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" disabled={pending || closed || invoice.status === 'SENT'} onClick={() => meta?.onAction(invoice.id, 'send')} title={t('SendInvoice')}>
              <Send className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" disabled={pending || closed} onClick={() => meta?.onPay(invoice.id)} title={t('PayInvoice')}>
              <CreditCard className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" disabled={pending || closed} onClick={() => meta?.onAction(invoice.id, 'cancel')} title={t('CancelInvoice')}>
              <XCircle className="h-4 w-4" />
            </Button>
          </div>
        );
      },
    },
  ], [formatInvoiceDate, i18n.language, statusConfig, t]);

  const handleRunCycle = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const result = await runCycle.mutateAsync({
        periodStart: periodStart || undefined,
        periodEnd: periodEnd || undefined,
        limit: Number(cycleLimit) || 100,
      });
      toast.success(t('BillingCycleDone', { processed: result.processed, withdraws: result.withdraw_count, invoices: result.invoice_count }));
    } catch {
      toast.error(t('BillingCycleFailed'));
    }
  };

  const handleRunWithdraw = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedWithdrawAbonentId) {
      toast.error(t('SelectAbonent'));
      return;
    }

    try {
      const result = await runWithdraw.mutateAsync({
        abonentId: selectedWithdrawAbonentId,
        periodStart: periodStart || undefined,
        periodEnd: periodEnd || undefined,
      });
      toast.success(t('WithdrawsCreated', { count: result.withdraws.length }));
    } catch {
      toast.error(t('WithdrawFailed'));
    }
  };

  const handleInvoiceAction = async (invoiceId: string, action: 'issue' | 'send' | 'cancel') => {
    const labels = { issue: t('InvoiceIssued'), send: t('InvoiceSent'), cancel: t('InvoiceCancelled') };
    try {
      await invoiceAction.mutateAsync({ invoiceId, action });
      toast.success(labels[action]);
    } catch {
      toast.error(t('InvoiceActionFailed'));
    }
  };

  const handlePayInvoice = async (invoiceId: string) => {
    try {
      await payInvoice.mutateAsync({ invoiceId });
      toast.success(t('InvoicePaid'));
    } catch {
      toast.error(t('InvoicePayFailed'));
    }
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-3xl font-bold tracking-tight">{t('Billing')}</h2>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          {t('Refresh')}
        </Button>
      </div>

      <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('RunBillingCycle')}</CardTitle>
              <CardDescription>{t('RunBillingCycleDescription')}</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-3" onSubmit={handleRunCycle}>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-2">
                    <Label htmlFor="period-start">{t('Start')}</Label>
                    <Input id="period-start" type="date" value={periodStart} onChange={(event) => setPeriodStart(event.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="period-end">{t('End')}</Label>
                    <Input id="period-end" type="date" value={periodEnd} onChange={(event) => setPeriodEnd(event.target.value)} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cycle-limit">{t('Limit')}</Label>
                  <Input id="cycle-limit" type="number" min="1" max="500" value={cycleLimit} onChange={(event) => setCycleLimit(event.target.value)} />
                </div>
                <Button type="submit" disabled={runCycle.isPending} className="w-full">
                  <Play className="mr-2 h-4 w-4" />
                  {t('Run')}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('AbonentWithdraw')}</CardTitle>
              <CardDescription>{t('AbonentWithdrawDescription')}</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-3" onSubmit={handleRunWithdraw}>
                <div className="space-y-2">
                  <Label htmlFor="withdraw-abonent">{t('Abonent')}</Label>
                  <Select id="withdraw-abonent" value={selectedWithdrawAbonentId} onChange={(event) => setWithdrawAbonentId(event.target.value)}>
                    {abonents.map((abonent) => (
                      <option key={abonent.id} value={abonent.id}>
                        {abonent.full_name || abonent.phone || abonent.id.slice(0, 8)}
                      </option>
                    ))}
                  </Select>
                </div>
                <Button type="submit" disabled={runWithdraw.isPending || !selectedWithdrawAbonentId} className="w-full">
                  <Calendar className="mr-2 h-4 w-4" />
                  {t('RunWithdraw')}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader className="gap-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle>{t('Invoices')}</CardTitle>
                <CardDescription>{t('TotalCount', { count: invoicePage?.total ?? invoices.length })}</CardDescription>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                  <option value="all">{t('AllStatuses')}</option>
                  <option value="DRAFT">{t('InvoiceStatusDraftPlural')}</option>
                  <option value="ISSUED">{t('InvoiceStatusIssuedPlural')}</option>
                  <option value="SENT">{t('InvoiceStatusSentPlural')}</option>
                  <option value="PAID">{t('InvoiceStatusPaidPlural')}</option>
                  <option value="OVERDUE">{t('InvoiceStatusOverduePlural')}</option>
                  <option value="CANCELLED">{t('InvoiceStatusCancelledPlural')}</option>
                </Select>
                <Select value={invoiceAbonentFilter} onChange={(event) => setInvoiceAbonentFilter(event.target.value)}>
                  <option value="all">{t('AllAbonents')}</option>
                  {abonents.map((abonent) => (
                    <option key={abonent.id} value={abonent.id}>
                      {abonent.full_name || abonent.phone || abonent.id.slice(0, 8)}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-64 w-full" />
              </div>
            ) : isError ? (
              <Button variant="outline" onClick={() => refetch()}>{t('Reload')}</Button>
            ) : (
              <DataTable
                columns={invoiceColumns}
                data={invoices}
                searchKey="description"
                searchPlaceholder={t('SearchInvoices')}
                meta={{
                  abonents,
                  onAction: handleInvoiceAction,
                  onPay: handlePayInvoice,
                  pendingId: pendingInvoiceId,
                }}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
