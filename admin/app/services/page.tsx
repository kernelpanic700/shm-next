'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Edit, PowerOff } from 'lucide-react';
import { DataTable } from '@/components/ui/data-table';
import { useServices } from '@/lib/hooks/use-services';
import { ColumnDef } from '@tanstack/react-table';
import { Service } from '@/lib/api';
import { toast } from 'sonner';
import { Skeleton } from '@/components/ui/skeleton';
import { ServiceModal } from '@/components/modals';

const columns: ColumnDef<Service>[] = [
  { accessorKey: 'name', header: 'Название' },
  { accessorKey: 'description', header: 'Описание', cell: ({ row }) => <span className="text-muted-foreground">{row.getValue('description') || '-'}</span> },
  { accessorKey: 'price', header: 'Цена', cell: ({ row }) => <span className="font-medium">{parseFloat(row.getValue('price') || '0').toLocaleString('ru-RU', { minimumFractionDigits: 2 })} {row.getValue('currency')}</span> },
  { accessorKey: 'is_active', header: 'Статус', cell: ({ row }) => <span className={`px-2 py-1 rounded-full text-xs font-medium ${row.getValue('is_active') ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>{row.getValue('is_active') ? 'Активна' : 'Неактивна'}</span> },
  { id: 'actions', header: 'Действия', cell: ({ row, table }) => (
    <div className="flex gap-1">
      <Button variant="ghost" size="sm" onClick={() => (table.options.meta as any)?.onEdit(row.original)} title="Редактировать"><Edit className="h-4 w-4" /></Button>
      <Button variant="ghost" size="sm" onClick={() => (table.options.meta as any)?.onDeactivate(row.original)} title="Деактивировать"><PowerOff className="h-4 w-4" /></Button>
    </div>
  ), enableSorting: false },
];

export default function ServicesPage() {
  const [editService, setEditService] = useState<Service | null>(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const { data: services = [], isLoading, isError, refetch } = useServices();

  const handleEdit = (service: Service) => setEditService(service);
  const handleDeactivate = (service: Service) => toast.warning('Деактивация', { description: service.name });

  if (isLoading) return <div className="flex-1 space-y-4 p-8 pt-6"><h2 className="text-3xl font-bold">Услуги</h2><Skeleton className="h-10 w-full" /><Skeleton className="h-64 w-full" /></div>;
  if (isError) return <div className="flex-1 space-y-4 p-8 pt-6"><h2 className="text-3xl font-bold">Услуги</h2><p className="text-destructive">Ошибка загрузки услуг</p></div>;

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Услуги</h2>
        <Button onClick={() => setCreateModalOpen(true)}><Plus className="mr-2 h-4 w-4" />Создать услугу</Button>
      </div>
      <Card><CardHeader><CardTitle>Список услуг</CardTitle><CardDescription>Управление услугами абонентов</CardDescription></CardHeader>
        <CardContent><DataTable columns={columns} data={services} searchKey="name" searchPlaceholder="Поиск по названию услуги..." meta={{ onEdit: handleEdit, onDeactivate: handleDeactivate }} /></CardContent>
      </Card>
      <ServiceModal service={editService} open={!!editService} onOpenChange={(open) => !open && setEditService(null)} onSuccess={refetch} />
      <ServiceModal open={createModalOpen} onOpenChange={setCreateModalOpen} onSuccess={refetch} />
    </div>
  );
}