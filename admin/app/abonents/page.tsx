'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus, DollarSign, Edit, PowerOff, RefreshCw } from 'lucide-react';
import { DataTable } from '@/components/ui/data-table';
import { useAbonents } from '@/lib/hooks/use-abonents';
import { ColumnDef } from '@tanstack/react-table';
import { Abonent } from '@/lib/api';
import { toast } from 'sonner';
import { Skeleton } from '@/components/ui/skeleton';
import { TopUpBalanceModal, CreateAbonentModal } from '@/components/modals';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';

const columns: ColumnDef<Abonent>[] = [
  {
    accessorKey: 'name',
    header: 'ФИО',
  },
  {
    accessorKey: 'phone',
    header: 'Телефон',
  },
  {
    accessorKey: 'account_number',
    header: 'Лицевой счёт',
  },
  {
    accessorKey: 'status',
    header: 'Статус',
    cell: ({ row }) => {
      const status = row.getValue('status') as string;
      const statusMap: Record<string, { label: string; className: string }> = {
        ACTIVE: { label: 'Активен', className: 'bg-green-100 text-green-800' },
        INACTIVE: { label: 'Неактивен', className: 'bg-gray-100 text-gray-800' },
        BLOCKED: { label: 'Заблокирован', className: 'bg-red-100 text-red-800' },
        SUSPENDED: { label: 'Приостановлен', className: 'bg-yellow-100 text-yellow-800' },
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
    header: 'Баланс',
    cell: ({ row }) => {
      const amount = parseFloat(String(row.getValue('balance') || 0));
      return <span className="font-medium">{amount.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₽</span>;
    },
  },
  {
    id: 'actions',
    header: 'Действия',
    cell: ({ row, table }) => {
      const abonent = row.original;
      return (
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => (table.options.meta as any)?.onTopUp(abonent)}
            title="Пополнить баланс"
          >
            <DollarSign className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => (table.options.meta as any)?.onChangeTariff(abonent)}
            title="Изменить тариф"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => (table.options.meta as any)?.onDeactivate(abonent)}
            title="Деактивировать"
          >
            <PowerOff className="h-4 w-4" />
          </Button>
        </div>
      );
    },
    enableSorting: false,
  },
];

export default function AbonentsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [minBalance, setMinBalance] = useState<string>('');
  const [maxBalance, setMaxBalance] = useState<string>('');
  const [topUpAbonent, setTopUpAbonent] = useState<Abonent | null>(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState<{ open: boolean; abonent: Abonent | null }>({ open: false, abonent: null });
  
  const { data: abonents = [], isLoading, isError, refetch } = useAbonents();

  // Клиентская фильтрация
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

  const handleTopUp = (abonent: Abonent) => {
    setTopUpAbonent(abonent);
  };

  const handleChangeTariff = (abonent: Abonent) => {
    toast.info('Изменение тарифа', { description: `${abonent.name || abonent.phone}` });
  };

  const handleDeactivate = (abonent: Abonent) => {
    setConfirmDialog({ open: true, abonent });
  };

  const confirmDeactivate = () => {
    if (confirmDialog.abonent) {
      toast.success('Абонент деактивирован', { description: `${confirmDialog.abonent.name || confirmDialog.abonent.phone}` });
      refetch();
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <h2 className="text-3xl font-bold tracking-tight">Абоненты</h2>
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
        <h2 className="text-3xl font-bold tracking-tight">Абоненты</h2>
        <p className="text-destructive">Ошибка загрузки абонентов</p>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Абоненты</h2>
        <Button onClick={() => setCreateModalOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Добавить абонента
        </Button>
      </div>
      
      {/* Фильтры */}
      <Card>
        <CardHeader>
          <CardTitle>Фильтры</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Статус</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="all">Все статусы</option>
                <option value="ACTIVE">Активен</option>
                <option value="INACTIVE">Неактивен</option>
                <option value="BLOCKED">Заблокирован</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Мин. баланс</label>
              <Input
                type="number"
                placeholder="0"
                value={minBalance}
                onChange={(e) => setMinBalance(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Макс. баланс</label>
              <Input
                type="number"
                placeholder="10000"
                value={maxBalance}
                onChange={(e) => setMaxBalance(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button variant="outline" onClick={() => { setStatusFilter('all'); setMinBalance(''); setMaxBalance(''); }}>
                Сбросить
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Список абонентов</CardTitle>
          <CardDescription>Управление абонентами и их счетами</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable 
            columns={columns} 
            data={filteredAbonents} 
            searchKey="name"
            searchPlaceholder="Поиск по ФИО, телефону или лицевому счёту..."
            meta={{ onTopUp: handleTopUp, onChangeTariff: handleChangeTariff, onDeactivate: handleDeactivate }}
          />
        </CardContent>
      </Card>

      {/* Modals */}
      <TopUpBalanceModal
        abonent={topUpAbonent}
        open={!!topUpAbonent}
        onOpenChange={(open) => !open && setTopUpAbonent(null)}
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
        title="Деактивация абонента"
        description={`Вы уверены, что хотите деактивировать абонента "${confirmDialog.abonent?.name || confirmDialog.abonent?.phone}"? Это действие нельзя отменить.`}
        confirmText="Деактивировать"
        variant="destructive"
        onConfirm={confirmDeactivate}
      />
    </div>
  );
}