'use client';

import { Suspense } from 'react';

export const dynamic = 'force-dynamic';

import { useEffect, useMemo, useState } from 'react';
import { useAbonent } from '@/lib/hooks/use-abonents';
import { usePayments } from '@/lib/hooks/use-payments';
import { useAbonentServices } from '@/lib/hooks/use-abonent-services';
import { TopUpBalanceModal, ChangeTariffModal } from '@/components/modals';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';
import { ArrowLeft, DollarSign, RefreshCw, PowerOff } from 'lucide-react';
import { DataTable } from '@/components/ui/data-table';
import { ColumnDef } from '@tanstack/react-table';
import { Payment, Service } from '@/lib/api';
import { format } from 'date-fns';
import { de, enUS, ru } from 'date-fns/locale';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const getDateLocale = (language: string) => {
  if (language.startsWith('de')) return de;
  if (language.startsWith('en')) return enUS;
  return ru;
};

export default function AbonentDetailPage() {
  const { t, i18n } = useTranslation();
  const [abonentId, setAbonentId] = useState('');
  const [topUpModalOpen, setTopUpModalOpen] = useState(false);
  const [changeTariffModalOpen, setChangeTariffModalOpen] = useState(false);
  const [deactivateDialog, setDeactivateDialog] = useState<{ open: boolean; abonent: any | null }>({ open: false, abonent: null });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setAbonentId(params.get('id') || '');
  }, []);

  const { data: abonent, isLoading: abonentLoading, isError: abonentError, refetch } = useAbonent(abonentId);
  const { data: payments = [], isLoading: paymentsLoading } = usePayments(abonentId);
  const { data: abonentServices = [], isLoading: servicesLoading } = useAbonentServices(abonentId);
  const dateLocale = getDateLocale(i18n.language);
  const numberLocale = i18n.language.startsWith('en') ? 'en-US' : i18n.language.startsWith('de') ? 'de-DE' : 'ru-RU';

  const paymentStatusLabels = useMemo<Record<string, string>>(() => ({
    NEW: t('PaymentStatusNew'),
    PENDING: t('PaymentStatusPending'),
    PROCESSING: t('PaymentStatusProcessing'),
    COMPLETED: t('PaymentStatusCompleted'),
    FAILED: t('PaymentStatusFailed'),
    REFUNDED: t('PaymentStatusRefunded'),
    CANCELLED: t('PaymentStatusCancelled'),
  }), [t]);

  const paymentColumns = useMemo<ColumnDef<Payment>[]>(() => [
    { accessorKey: 'created_at', header: t('Date'), cell: ({ row }) => format(new Date(row.getValue('created_at')), 'dd.MM.yyyy HH:mm', { locale: dateLocale }) },
    { accessorKey: 'amount', header: t('Amount'), cell: ({ row }) => `${parseFloat(String(row.getValue('amount'))).toLocaleString(numberLocale, { minimumFractionDigits: 2 })} ${row.getValue('currency')}` },
    {
      accessorKey: 'status',
      header: t('Status'),
      cell: ({ row }) => {
        const status = String(row.getValue('status')).toUpperCase();
        return <span className={`px-2 py-1 rounded-full text-xs ${status === 'COMPLETED' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>{paymentStatusLabels[status] || status}</span>;
      },
    },
    { accessorKey: 'payment_method', header: t('PaymentMethod') },
  ], [dateLocale, numberLocale, paymentStatusLabels, t]);

  const serviceColumns = useMemo<ColumnDef<Service>[]>(() => [
    { accessorKey: 'name', header: t('Service') },
    { accessorKey: 'price', header: t('Price'), cell: ({ row }) => `${parseFloat(String(row.getValue('price'))).toLocaleString(numberLocale, { minimumFractionDigits: 2 })} ${row.getValue('currency')}` },
    { accessorKey: 'is_active', header: t('Status'), cell: ({ row }) => <span className={`px-2 py-1 rounded-full text-xs ${row.getValue('is_active') ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>{row.getValue('is_active') ? t('Active') : t('Inactive')}</span> },
  ], [numberLocale, t]);

  if (abonentLoading) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-10 w-96" />
        <div className="grid gap-4">
          <Skeleton className="h-96" />
        </div>
      </div>
    );
  }

  if (abonentError) {
    return (
      <div className="flex-1 p-8">
        <p className="text-destructive">{t('ErrorLoadingAbonent')}</p>
        <Button variant="outline" onClick={() => refetch()} className="mt-4">
          {t('TryAgain')}
        </Button>
      </div>
    );
  }

  if (!abonent) {
    return <div className="flex-1 p-8">{t('AbonentNotFound')}</div>;
  }

  const handleDeactivate = () => {
    setDeactivateDialog({ open: true, abonent });
  };

  const confirmDeactivate = async () => {
    if (!deactivateDialog.abonent) return;
    try {
      await fetch(`/api/abonents/${deactivateDialog.abonent.id}/deactivate`, { method: 'POST' });
      toast.success(t('AbonentDeactivated'));
      refetch();
    } catch {
      toast.error(t('AbonentDeactivateFailed'));
    }
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => window.history.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" /> {t('Back')}
          </Button>
          <h2 className="text-3xl font-bold">{abonent.name || abonent.phone}</h2>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setTopUpModalOpen(true)}>
            <DollarSign className="mr-2 h-4 w-4" /> {t('TopUpBalance')}
          </Button>
          <Button variant="outline" onClick={() => setChangeTariffModalOpen(true)}>
            <RefreshCw className="mr-2 h-4 w-4" /> {t('ChangeTariff')}
          </Button>
          <Button variant="destructive" onClick={handleDeactivate}>
            <PowerOff className="mr-2 h-4 w-4" /> {t('Deactivate')}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="info" className="space-y-4">
        <TabsList>
          <TabsTrigger value="info">{t('BasicInfo')}</TabsTrigger>
          <TabsTrigger value="services">{t('Services')}</TabsTrigger>
          <TabsTrigger value="payments">{t('Payments')}</TabsTrigger>
          <TabsTrigger value="history">{t('ChangeHistory')}</TabsTrigger>
        </TabsList>

        <TabsContent value="info">
          <Card>
            <CardHeader>
              <CardTitle>{t('AbonentInfo')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p><strong>{t('AccountNumber')}:</strong> {abonent.account_number || '-'}</p>
              <p><strong>{t('Phone')}:</strong> {abonent.phone}</p>
              <p><strong>Email:</strong> {abonent.email || '-'}</p>
              <p><strong>{t('Address')}:</strong> {abonent.address || '-'}</p>
              <p><strong>{t('Status')}:</strong> {abonent.status}</p>
              <p><strong>{t('Balance')}:</strong> {parseFloat(String(abonent.balance || 0)).toLocaleString(numberLocale, { minimumFractionDigits: 2 })} ₽</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services">
          <Card>
            <CardHeader>
              <CardTitle>{t('AbonentServices')}</CardTitle>
              <CardDescription>{t('ConnectedServices')}</CardDescription>
            </CardHeader>
            <CardContent>
              {servicesLoading ? <Skeleton className="h-32" /> :
                abonentServices.length > 0
                  ? <DataTable columns={serviceColumns} data={abonentServices} searchKey="name" />
                  : <p className="text-sm text-muted-foreground">{t('NoConnectedServices')}</p>
              }
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments">
          <Card>
            <CardHeader>
              <CardTitle>{t('PaymentHistory')}</CardTitle>
              <CardDescription>{t('RecentTopUps')}</CardDescription>
            </CardHeader>
            <CardContent>
              {paymentsLoading ? <Skeleton className="h-32" /> : <DataTable columns={paymentColumns} data={payments} searchKey="created_at" />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>{t('ChangeHistory')}</CardTitle>
              <CardDescription>{t('AbonentChangeLog')}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{t('AuditLogPending')}</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <TopUpBalanceModal abonent={abonent} open={topUpModalOpen} onOpenChange={setTopUpModalOpen} />
      <ChangeTariffModal abonent={abonent} open={changeTariffModalOpen} onOpenChange={setChangeTariffModalOpen} />
      <ConfirmationDialog
        open={deactivateDialog.open}
        onOpenChange={(open) => setDeactivateDialog({ ...deactivateDialog, open })}
        title={t('DeactivateAbonentTitle')}
        description={t('DeactivateAbonentDescription', { name: deactivateDialog.abonent?.name || deactivateDialog.abonent?.phone })}
        confirmText={t('Deactivate')}
        variant="destructive"
        onConfirm={confirmDeactivate}
      />
    </div>
  );
}
