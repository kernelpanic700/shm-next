'use client';

import { useMemo, useState } from 'react';
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
import { useTranslation } from 'react-i18next';

export default function ServicesPage() {
  const { t, i18n } = useTranslation();
  const [editService, setEditService] = useState<Service | null>(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const { data: services = [], isLoading, isError, refetch } = useServices();
  const numberLocale = i18n.language.startsWith('en') ? 'en-US' : 'ru-RU';
  const columns = useMemo<ColumnDef<Service>[]>(() => [
    { accessorKey: 'name', header: t('Name') },
    { accessorKey: 'description', header: t('Description'), cell: ({ row }) => <span className="text-muted-foreground">{row.getValue('description') || '-'}</span> },
    {
      accessorKey: 'cost',
      header: t('Price'),
      cell: ({ row }) => {
        const service = row.original;
        const amount = Number(service.cost ?? service.price ?? 0);
        return (
          <span className="font-medium">
            {amount.toLocaleString(numberLocale, { minimumFractionDigits: 2 })} {service.currency}
          </span>
        );
      },
    },
    {
      accessorKey: 'allow_to_order',
      header: t('Status'),
      cell: ({ row }) => {
        const service = row.original;
        const isActive = service.allow_to_order ?? service.is_active ?? !service.is_deleted;
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
            {isActive ? t('Active') : t('Inactive')}
          </span>
        );
      },
    },
    { id: 'actions', header: t('Actions'), cell: ({ row, table }) => (
      <div className="flex gap-1">
        <Button variant="ghost" size="sm" onClick={() => (table.options.meta as any)?.onEdit(row.original)} title={t('Edit')}><Edit className="h-4 w-4" /></Button>
        <Button variant="ghost" size="sm" onClick={() => (table.options.meta as any)?.onDeactivate(row.original)} title={t('Deactivate')}><PowerOff className="h-4 w-4" /></Button>
      </div>
    ), enableSorting: false },
  ], [numberLocale, t]);

  const handleEdit = (service: Service) => setEditService(service);
  const handleDeactivate = (service: Service) => toast.warning(t('Deactivation'), { description: service.name });

  if (isLoading) return <div className="flex-1 space-y-4 p-8 pt-6"><h2 className="text-3xl font-bold">{t('Services')}</h2><Skeleton className="h-10 w-full" /><Skeleton className="h-64 w-full" /></div>;
  if (isError) return <div className="flex-1 space-y-4 p-8 pt-6"><h2 className="text-3xl font-bold">{t('Services')}</h2><p className="text-destructive">{t('ServicesLoadError')}</p></div>;

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">{t('Services')}</h2>
        <Button onClick={() => setCreateModalOpen(true)}><Plus className="mr-2 h-4 w-4" />{t('CreateService')}</Button>
      </div>
      <Card><CardHeader><CardTitle>{t('ServicesList')}</CardTitle><CardDescription>{t('ServicesListDescription')}</CardDescription></CardHeader>
        <CardContent><DataTable columns={columns} data={services} searchKey="name" searchPlaceholder={t('SearchServices')} meta={{ onEdit: handleEdit, onDeactivate: handleDeactivate }} /></CardContent>
      </Card>
      <ServiceModal service={editService} open={!!editService} onOpenChange={(open) => !open && setEditService(null)} onSuccess={refetch} />
      <ServiceModal open={createModalOpen} onOpenChange={setCreateModalOpen} onSuccess={refetch} />
    </div>
  );
}
