'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Edit, PowerOff } from 'lucide-react';
import { DataTable } from '@/components/ui/data-table';
import { useTariffs } from '@/lib/hooks/use-tariffs';
import { ColumnDef } from '@tanstack/react-table';
import { Tariff } from '@/lib/api';
import { toast } from 'sonner';
import { Skeleton } from '@/components/ui/skeleton';
import { TariffModal } from '@/components/modals';

const columns: ColumnDef<Tariff>[] = [
  {
    accessorKey: 'name',
    header: 'Название',
  },
  {
    accessorKey: 'description',
    header: 'Описание',
    cell: ({ row }) => {
      const desc = row.getValue('description') as string;
      return <span className="text-muted-foreground">{desc || '-'}</span>;
    },
  },
  {
    accessorKey: 'price',
    header: 'Цена',
    cell: ({ row }) => {
      const price = parseFloat(row.getValue('price') || '0');
      const currency = row.getValue('currency') as string;
      return (
        <span className="font-medium">
          {price.toLocaleString('ru-RU', { minimumFractionDigits: 2 })} {currency}
        </span>
      );
    },
  },
  {
    accessorKey: 'billing_cycle',
    header: 'Период',
    cell: ({ row }) => {
      const cycle = row.getValue('billing_cycle') as string;
      const cycleMap: Record<string, string> = {
        monthly: 'Месячный',
        quarterly: 'Квартальный',
        yearly: 'Годовой',
      };
      return cycleMap[cycle] || cycle;
    },
  },
  {
    accessorKey: 'is_active',
    header: 'Статус',
    cell: ({ row }) => {
      const isActive = row.getValue('is_active') as boolean;
      return (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
          {isActive ? 'Активен' : 'Неактивен'}
        </span>
      );
    },
  },
  {
    id: 'actions',
    header: 'Действия',
    cell: ({ row, table }) => {
      const tariff = row.original;
      return (
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => (table.options.meta as any)?.onEdit(tariff)}
            title="Редактировать"
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => (table.options.meta as any)?.onDeactivate(tariff)}
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

export default function TariffsPage() {
  const [editTariff, setEditTariff] = useState<Tariff | null>(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  
  const { data: tariffs = [], isLoading, isError, refetch } = useTariffs();

  const handleEdit = (tariff: Tariff) => {
    setEditTariff(tariff);
  };

  const handleDeactivate = (tariff: Tariff) => {
    toast.warning('Деактивация', { description: tariff.name });
  };

  if (isLoading) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <h2 className="text-3xl font-bold tracking-tight">Тарифы</h2>
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
        <h2 className="text-3xl font-bold tracking-tight">Тарифы</h2>
        <p className="text-destructive">Ошибка загрузки тарифов</p>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Тарифы</h2>
        <Button onClick={() => setCreateModalOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Создать тариф
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Список тарифов</CardTitle>
          <CardDescription>Управление тарифами и ценами</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable 
            columns={columns} 
            data={tariffs} 
            searchKey="name"
            searchPlaceholder="Поиск по названию тарифа..."
            meta={{ onEdit: handleEdit, onDeactivate: handleDeactivate }}
          />
        </CardContent>
      </Card>

      {/* Modals */}
      <TariffModal
        tariff={editTariff}
        open={!!editTariff}
        onOpenChange={(open) => !open && setEditTariff(null)}
        onSuccess={refetch}
      />
      <TariffModal
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onSuccess={refetch}
      />
    </div>
  );
}