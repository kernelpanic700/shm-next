'use client';

export const dynamic = 'force-dynamic';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus, DollarSign, PowerOff, RefreshCw, Pencil } from 'lucide-react';
import { DataTable } from '@/components/ui/data-table';
import { useAbonents, useDeleteAbonent } from '@/lib/hooks/use-abonents';
import { ColumnDef } from '@tanstack/react-table';
import { Abonent } from '@/lib/api';
import { toast } from 'sonner';
import { Skeleton } from '@/components/ui/skeleton';
import { TopUpBalanceModal, CreateAbonentModal, ChangeTariffModal } from '@/components/modals';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';
import { useTranslation } from 'react-i18next';

export default function AbonentsPage() {
  const { t, i18n } = useTranslation();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [minBalance, setMinBalance] = useState<string>('');
  const [maxBalance, setMaxBalance] = useState<string>('');
  const [topUpAbonent, setTopUpAbonent] = useState<Abonent | null>(null);
  const [changeTariffAbonent, setChangeTariffAbonent] = useState<Abonent | null>(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState<{ open: boolean; abonent: Abonent | null }>({ open: false, abonent: null });
  
  const { data: abonents = [], isLoading, isError, refetch } = useAbonents();
  const deleteAbonent = useDeleteAbonent();
  const numberLocale = i18n.language.startsWith('en') ? 'en-US' : i18n.language.startsWith('de') ? 'de-DE' : 'ru-RU';

  const filteredAbonents = useMemo(() => {
    return abonents.filter((abonent) => {
      if (statusFilter !== 'all' && abonent.status !== statusFilter) {
        return false;
      }
      const balance = parseFloat(String(abonent.balance || 0));
      if (minBalance && balance < parseFloat(minBalance)) {
        return false;
      }
      if (maxBalance && balance > parseFloat(maxBalance)) {
        return false;
      }
      return true;
    });
  }, [abonents, statusFilter, minBalance, maxBalance]);

  const columns = useMemo<ColumnDef<Abonent>[]>(() => [
    {
      accessorKey: 'full_name',
      header: t('FullName'),
    },
    {
      accessorKey: 'phone',
      header: t('Phone'),
    },
    {
      accessorKey: 'account_number',
      header: t('AccountNumber'),
    },
    {
      accessorKey: 'status',
      header: t('Status'),
      cell: ({ row }) => {
        const status = row.getValue('status') as string;
        const statusMap: Record<string, { label: string; className: string }> = {
          ACTIVE: { label: t('Active'), className: 'bg-green-100 text-green-800' },
          INACTIVE: { label: t('Inactive'), className: 'bg-gray-100 text-gray-800' },
          BLOCKED: { label: t('Blocked'), className: 'bg-red-100 text-red-800' },
          SUSPENDED: { label: t('Suspended'), className: 'bg-yellow-100 text-yellow-800' },
        };
        const config = statusMap[status] || { label: status, className: 'bg-gray-100 text-gray-800' };
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.className}`}>
            {config.label}
          </span>
        );
      },
    },
    {
      accessorKey: 'balance',
      header: t('Balance'),
      cell: ({ row }) => {
        const amount = parseFloat(String(row.getValue('balance') || 0));
        return <span className="font-medium">{amount.toLocaleString(numberLocale, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₽</span>;
      },
    },
    {
      id: 'actions',
      header: t('Actions'),
      cell: ({ row, table }) => {
        const abonent = row.original;
        return (
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => window.location.href = `/abonents/detail?id=${abonent.id}&tab=settings`}
              title={t('Edit')}
            >
              <Pencil className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => (table.options.meta as any)?.onTopUp(abonent)}
              title={t('TopUpBalance')}
            >
              <DollarSign className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => (table.options.meta as any)?.onChangeTariff(abonent)}
              title={t('ChangeTariff')}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => (table.options.meta as any)?.onDeactivate(abonent)}
              title={t('Deactivate')}
            >
              <PowerOff className="h-4 w-4" />
            </Button>
          </div>
        );
      },
      enableSorting: false,
    },
  ], [numberLocale, t]);

  const handleTopUp = (abonent: Abonent) => {
    setTopUpAbonent(abonent);
  };

  const handleChangeTariff = (abonent: Abonent) => {
    setChangeTariffAbonent(abonent);
  };

  const handleDeactivate = (abonent: Abonent) => {
    setConfirmDialog({ open: true, abonent });
  };

  const confirmDeactivate = async () => {
    if (confirmDialog.abonent) {
      try {
        await deleteAbonent.mutateAsync(confirmDialog.abonent.id);
        toast.success(t('AbonentDeactivated'), { description: `${confirmDialog.abonent.full_name || confirmDialog.abonent.phone}` });
      } catch (error: any) {
        toast.error(t('AbonentDeactivateFailed'), {
          description: error.response?.data?.detail || error.message,
        });
      }
      refetch();
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <h2 className="text-3xl font-bold tracking-tight">{t('Abonents')}</h2>
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <h2 className="text-3xl font-bold tracking-tight">{t('Abonents')}</h2>
        <p className="text-destructive">{t('AbonentsLoadError')}</p>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">{t('Abonents')}</h2>
        <Button onClick={() => setCreateModalOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          {t('AddAbonent')}
        </Button>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>{t('Filters')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('Status')}</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="all">{t('AllStatuses')}</option>
                <option value="ACTIVE">{t('Active')}</option>
                <option value="INACTIVE">{t('Inactive')}</option>
                <option value="BLOCKED">{t('Blocked')}</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('MinBalance')}</label>
              <Input
                type="number"
                placeholder="0"
                value={minBalance}
                onChange={(e) => setMinBalance(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('MaxBalance')}</label>
              <Input
                type="number"
                placeholder="10000"
                value={maxBalance}
                onChange={(e) => setMaxBalance(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button variant="outline" onClick={() => { setStatusFilter('all'); setMinBalance(''); setMaxBalance(''); }}>
                {t('Reset')}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('AbonentsList')}</CardTitle>
          <CardDescription>{t('AbonentsListDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable 
            columns={columns} 
            data={filteredAbonents} 
            searchKey="name"
            searchPlaceholder={t('SearchAbonents')}
            meta={{ onTopUp: handleTopUp, onChangeTariff: handleChangeTariff, onDeactivate: handleDeactivate }}
          />
        </CardContent>
      </Card>

      <TopUpBalanceModal
        abonent={topUpAbonent}
        open={!!topUpAbonent}
        onOpenChange={(open) => !open && setTopUpAbonent(null)}
        onSuccess={refetch}
      />
      <ChangeTariffModal
        abonent={changeTariffAbonent}
        open={!!changeTariffAbonent}
        onOpenChange={(open) => !open && setChangeTariffAbonent(null)}
        onSuccess={refetch}
      />
      <CreateAbonentModal
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onSuccess={refetch}
      />
      <ConfirmationDialog
        open={confirmDialog.open}
        onOpenChange={(open) => setConfirmDialog({ ...confirmDialog, open })}
        title={t('DeactivateAbonentTitle')}
        description={t('DeactivateAbonentDescription', { name: confirmDialog.abonent?.full_name || confirmDialog.abonent?.phone })}
        confirmText={t('Deactivate')}
        variant="destructive"
        onConfirm={confirmDeactivate}
      />
    </div>
  );
}
