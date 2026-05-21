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
