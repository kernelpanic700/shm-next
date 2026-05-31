'use client';

import { Suspense } from 'react';

export const dynamic = 'force-dynamic';

import { useEffect, useMemo, useState } from 'react';
import { useAbonent, useAbonentProfile, useDeleteAbonent, useUpdateAbonent, useUpdateAbonentProfile } from '@/lib/hooks/use-abonents';
import { usePayments } from '@/lib/hooks/use-payments';
import { useAbonentServices } from '@/lib/hooks/use-abonent-services';
import { TopUpBalanceModal, ChangeTariffModal } from '@/components/modals';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';
import { ArrowLeft, DollarSign, RefreshCw, PowerOff, Save, Pencil } from 'lucide-react';
import { DataTable } from '@/components/ui/data-table';
import { ColumnDef } from '@tanstack/react-table';
import { Abonent, Payment, Service } from '@/lib/api';
import { format } from 'date-fns';
import { de, enUS, ru } from 'date-fns/locale';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';

const getDateLocale = (language: string) => {
  if (language.startsWith('de')) return de;
  if (language.startsWith('en')) return enUS;
  return ru;
};

type AbonentStatus = Abonent['status'];
type AbonentFormData = {
  full_name: string;
  phone: string;
  email: string;
  account_number: string;
  login: string;
  login2: string;
  status: AbonentStatus;
  contract: string;
  discount: string;
  credit: string;
  bonus: string;
  comment: string;
  can_overdraft: boolean;
  verified: boolean;
  settings: string;
  profile: string;
};

export default function AbonentDetailPage() {
  const { t, i18n } = useTranslation();
  const [abonentId, setAbonentId] = useState('');
  const [topUpModalOpen, setTopUpModalOpen] = useState(false);
  const [changeTariffModalOpen, setChangeTariffModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('info');
  const [deactivateDialog, setDeactivateDialog] = useState<{ open: boolean; abonent: any | null }>({ open: false, abonent: null });
  const [formData, setFormData] = useState<AbonentFormData>({
    full_name: '',
    phone: '',
    email: '',
    account_number: '',
    login: '',
    login2: '',
    status: 'ACTIVE',
    contract: '',
    discount: '0',
    credit: '0',
    bonus: '0',
    comment: '',
    can_overdraft: false,
    verified: false,
    settings: '{}',
    profile: '{}',
  });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setAbonentId(params.get('id') || '');
    setActiveTab(params.get('tab') || 'info');
  }, []);

  const { data: abonent, isLoading: abonentLoading, isError: abonentError, refetch } = useAbonent(abonentId);
  const { data: profile } = useAbonentProfile(abonentId);
  const updateAbonent = useUpdateAbonent();
  const updateProfile = useUpdateAbonentProfile();
  const deleteAbonent = useDeleteAbonent();
  const { data: payments = [], isLoading: paymentsLoading } = usePayments(abonentId);
  const { data: abonentServices = [], isLoading: servicesLoading } = useAbonentServices(abonentId);
  const dateLocale = getDateLocale(i18n.language);
  const numberLocale = i18n.language.startsWith('en') ? 'en-US' : i18n.language.startsWith('de') ? 'de-DE' : 'ru-RU';

  useEffect(() => {
    if (!abonent) return;
    setFormData((current) => ({
      ...current,
      full_name: abonent.full_name || '',
      phone: abonent.phone || '',
      email: abonent.email || '',
      account_number: abonent.account_number || '',
      login: abonent.login || '',
      login2: abonent.login2 || '',
      status: abonent.status || 'ACTIVE',
      contract: abonent.contract || '',
      discount: String(abonent.discount ?? 0),
      credit: String(abonent.credit ?? 0),
      bonus: String(abonent.bonus ?? 0),
      comment: abonent.comment || '',
      can_overdraft: Boolean(abonent.can_overdraft),
      verified: Boolean(abonent.verified),
      settings: JSON.stringify(abonent.settings || {}, null, 2),
    }));
  }, [abonent]);

  useEffect(() => {
    if (!profile) return;
    setFormData((current) => ({
      ...current,
      profile: JSON.stringify(profile.data || {}, null, 2),
    }));
  }, [profile]);

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
      await deleteAbonent.mutateAsync(deactivateDialog.abonent.id);
      toast.success(t('AbonentDeactivated'));
      refetch();
    } catch (error: any) {
      toast.error(t('AbonentDeactivateFailed'), {
        description: error.response?.data?.detail || error.message,
      });
    }
  };

  const handleSave = async () => {
    try {
      const settings = JSON.parse(formData.settings || '{}');
      const profileData = JSON.parse(formData.profile || '{}');

      await updateAbonent.mutateAsync({
        id: abonent.id,
        full_name: formData.full_name,
        phone: formData.phone,
        email: formData.email || undefined,
        account_number: formData.account_number,
        login: formData.login || undefined,
        login2: formData.login2 || undefined,
        status: formData.status,
        contract: formData.contract || undefined,
        discount: Number(formData.discount || 0),
        credit: Number(formData.credit || 0),
        bonus: Number(formData.bonus || 0),
        comment: formData.comment || undefined,
        can_overdraft: formData.can_overdraft,
        verified: formData.verified,
        metadata: settings,
      });
      await updateProfile.mutateAsync({ id: abonent.id, data: profileData });
      toast.success(t('AbonentUpdated'));
      refetch();
    } catch (error) {
      const message = error instanceof SyntaxError ? t('InvalidJson') : t('AbonentSaveFailed');
      toast.error(message);
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
          <Button variant="outline" onClick={() => setActiveTab('settings')}>
            <Pencil className="mr-2 h-4 w-4" /> {t('Edit')}
          </Button>
          <Button variant="destructive" onClick={handleDeactivate}>
            <PowerOff className="mr-2 h-4 w-4" /> {t('Deactivate')}
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="info">{t('BasicInfo')}</TabsTrigger>
          <TabsTrigger value="settings">{t('AbonentSettings')}</TabsTrigger>
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
              <p><strong>Login:</strong> {abonent.login || '-'}</p>
              <p><strong>Login2:</strong> {abonent.login2 || '-'}</p>
              <p><strong>{t('Phone')}:</strong> {abonent.phone}</p>
              <p><strong>Email:</strong> {abonent.email || '-'}</p>
              <p><strong>{t('Address')}:</strong> {abonent.address || '-'}</p>
              <p><strong>{t('Status')}:</strong> {abonent.status}</p>
              <p><strong>Contract:</strong> {abonent.contract || '-'}</p>
              <p><strong>Discount:</strong> {abonent.discount ?? 0}%</p>
              <p><strong>Credit:</strong> {Number(abonent.credit || 0).toLocaleString(numberLocale, { minimumFractionDigits: 2 })} ₽</p>
              <p><strong>Bonus:</strong> {Number(abonent.bonus || 0).toLocaleString(numberLocale, { minimumFractionDigits: 2 })} ₽</p>
              <p><strong>Verified:</strong> {abonent.verified ? t('Active') : t('Inactive')}</p>
              <p><strong>{t('Balance')}:</strong> {parseFloat(String(abonent.balance || 0)).toLocaleString(numberLocale, { minimumFractionDigits: 2 })} ₽</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle>{t('AbonentSettings')}</CardTitle>
                  <CardDescription>{t('AbonentSettingsDescription')}</CardDescription>
                </div>
                <Button onClick={handleSave} disabled={updateAbonent.isPending || updateProfile.isPending}>
                  <Save className="mr-2 h-4 w-4" />{t('Save')}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <Label>{t('FullName')}<Input value={formData.full_name} onChange={(e) => setFormData({ ...formData, full_name: e.target.value })} /></Label>
                <Label>{t('Phone')}<Input value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} /></Label>
                <Label>Email<Input type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} /></Label>
                <Label>{t('AccountNumber')}<Input value={formData.account_number} onChange={(e) => setFormData({ ...formData, account_number: e.target.value })} /></Label>
                <Label>Login<Input value={formData.login} onChange={(e) => setFormData({ ...formData, login: e.target.value })} /></Label>
                <Label>Login2<Input value={formData.login2} onChange={(e) => setFormData({ ...formData, login2: e.target.value })} /></Label>
                <Label>{t('Status')}<Select value={formData.status} onChange={(e) => setFormData({ ...formData, status: e.target.value as AbonentStatus })}><option value="ACTIVE">{t('Active')}</option><option value="INACTIVE">{t('Inactive')}</option><option value="BLOCKED">{t('Blocked')}</option><option value="SUSPENDED">{t('Suspended')}</option></Select></Label>
                <Label>Contract<Input value={formData.contract} onChange={(e) => setFormData({ ...formData, contract: e.target.value })} /></Label>
                <Label>Discount<Input type="number" min={0} max={100} value={formData.discount} onChange={(e) => setFormData({ ...formData, discount: e.target.value })} /></Label>
                <Label>Credit<Input type="number" min={0} value={formData.credit} onChange={(e) => setFormData({ ...formData, credit: e.target.value })} /></Label>
                <Label>Bonus<Input type="number" min={0} value={formData.bonus} onChange={(e) => setFormData({ ...formData, bonus: e.target.value })} /></Label>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <label className="flex items-center gap-2 text-sm font-medium">
                  <Checkbox checked={formData.can_overdraft} onCheckedChange={(checked) => setFormData({ ...formData, can_overdraft: checked === true })} />
                  Can overdraft
                </label>
                <label className="flex items-center gap-2 text-sm font-medium">
                  <Checkbox checked={formData.verified} onCheckedChange={(checked) => setFormData({ ...formData, verified: checked === true })} />
                  Verified
                </label>
              </div>
              <Label>{t('Comment')}<Textarea value={formData.comment} onChange={(e) => setFormData({ ...formData, comment: e.target.value })} rows={3} /></Label>
              <div className="grid gap-4 lg:grid-cols-2">
                <Label>Settings JSON<Textarea className="font-mono" value={formData.settings} onChange={(e) => setFormData({ ...formData, settings: e.target.value })} rows={10} /></Label>
                <Label>Profile JSON<Textarea className="font-mono" value={formData.profile} onChange={(e) => setFormData({ ...formData, profile: e.target.value })} rows={10} /></Label>
              </div>
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

      <TopUpBalanceModal abonent={abonent} open={topUpModalOpen} onOpenChange={setTopUpModalOpen} onSuccess={refetch} />
      <ChangeTariffModal abonent={abonent} open={changeTariffModalOpen} onOpenChange={setChangeTariffModalOpen} onSuccess={refetch} />
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
