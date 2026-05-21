'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import { ru } from 'date-fns/locale';
import { toast } from 'sonner';

export default function AbonentDetailPage() {
  const { id } = useParams();
  const abonentId = id as string;
  const [topUpModalOpen, setTopUpModalOpen] = useState(false);
  const [changeTariffModalOpen, setChangeTariffModalOpen] = useState(false);
  const [deactivateDialog, setDeactivateDialog] = useState<{ open: boolean; abonent: typeof abonent | null }>({ open: false, abonent: null });
  
  const { data: abonent, isLoading: abonentLoading, isError: abonentError, refetch } = useAbonent(abonentId);
  const { data: payments = [], isLoading: paymentsLoading } = usePayments(abonentId);
  const { data: abonentServices = [], isLoading: servicesLoading } = useAbonentServices(abonentId);

  const paymentColumns: ColumnDef<Payment>[] = [
    { accessorKey: 'created_at', header: 'Дата', cell: ({ row }) => format(new Date(row.getValue('created_at')), 'dd.MM.yyyy HH:mm', { locale: ru }) },
    { accessorKey: 'amount', header: 'Сумма', cell: ({ row }) => `${parseFloat(String(row.getValue('amount'))).toLocaleString('ru-RU', { minimumFractionDigits: 2 })} ${row.getValue('currency')}` },
    { accessorKey: 'status', header: 'Статус', cell: ({ row }) => <span className={`px-2 py-1 rounded-full text-xs ${row.getValue('status') === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>{row.getValue('status')}</span> },
    { accessorKey: 'payment_method', header: 'Метод оплаты' },
  ];

  const serviceColumns: ColumnDef<Service>[] = [
    { accessorKey: 'name', header: 'Услуга' },
    { accessorKey: 'price', header: 'Цена', cell: ({ row }) => `${parseFloat(String(row.getValue('price'))).toLocaleString('ru-RU', { minimumFractionDigits: 2 })} ${row.getValue('currency')}` },
    { accessorKey: 'is_active', header: 'Статус', cell: ({ row }) => <span className={`px-2 py-1 rounded-full text-xs ${row.getValue('is_active') ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>{row.getValue('is_active') ? 'Активна' : 'Неактивна'}</span> },
  ];

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
        <p className="text-destructive">Ошибка загрузки данных абонента</p>
        <Button variant="outline" onClick={() => refetch()} className="mt-4">
          Попробовать снова
        </Button>
      </div>
    );
  }

  if (!abonent) {
    return <div className="flex-1 p-8">Абонент не найден</div>;
  }

  const handleDeactivate = () => {
    setDeactivateDialog({ open: true, abonent });
  };

  const confirmDeactivate = async () => {
    if (!deactivateDialog.abonent) return;
    try {
      await fetch(`/api/abonents/${deactivateDialog.abonent.id}/deactivate`, { method: 'POST' });
      toast.success('Абонент деактивирован');
      refetch();
    } catch {
      toast.error('Не удалось деактивировать абонента');
    }
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => window.history.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" /> Назад
          </Button>
          <h2 className="text-3xl font-bold">{abonent.name || abonent.phone}</h2>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setTopUpModalOpen(true)}>
            <DollarSign className="mr-2 h-4 w-4" /> Пополнить баланс
          </Button>
          <Button variant="outline" onClick={() => setChangeTariffModalOpen(true)}>
            <RefreshCw className="mr-2 h-4 w-4" /> Сменить тариф
          </Button>
          <Button variant="destructive" onClick={handleDeactivate}>
            <PowerOff className="mr-2 h-4 w-4" /> Деактивировать
          </Button>
        </div>
      </div>

      <Tabs defaultValue="info" className="space-y-4">
        <TabsList>
          <TabsTrigger value="info">Основная информация</TabsTrigger>
          <TabsTrigger value="services">Услуги</TabsTrigger>
          <TabsTrigger value="payments">Платежи</TabsTrigger>
          <TabsTrigger value="history">История изменений</TabsTrigger>
        </TabsList>

        <TabsContent value="info">
          <Card>
            <CardHeader>
              <CardTitle>Информация об абоненте</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p><strong>Лицевой счёт:</strong> {abonent.account_number || '-'}</p>
              <p><strong>Телефон:</strong> {abonent.phone}</p>
              <p><strong>Email:</strong> {abonent.email || '-'}</p>
              <p><strong>Адрес:</strong> {abonent.address || '-'}</p>
              <p><strong>Статус:</strong> {abonent.status}</p>
              <p><strong>Баланс:</strong> {parseFloat(String(abonent.balance || 0)).toLocaleString('ru-RU', { minimumFractionDigits: 2 })} ₽</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services">
          <Card>
            <CardHeader>
              <CardTitle>Услуги абонента</CardTitle>
              <CardDescription>Подключённые услуги</CardDescription>
            </CardHeader>
            <CardContent>
              {servicesLoading ? <Skeleton className="h-32" /> : 
                abonentServices.length > 0 
                  ? <DataTable columns={serviceColumns} data={abonentServices} searchKey="name" />
                  : <p className="text-sm text-muted-foreground">Услуги не подключены</p>
              }
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments">
          <Card>
            <CardHeader>
              <CardTitle>История платежей</CardTitle>
              <CardDescription>Последние операции пополнения баланса</CardDescription>
            </CardHeader>
            <CardContent>
              {paymentsLoading ? <Skeleton className="h-32" /> : <DataTable columns={paymentColumns} data={payments} searchKey="created_at" />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>История изменений</CardTitle>
              <CardDescription>Лог изменений данных абонента</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">История изменений будет доступна после интеграции с audit log</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <TopUpBalanceModal abonent={abonent} open={topUpModalOpen} onOpenChange={setTopUpModalOpen} />
      <ChangeTariffModal abonent={abonent} open={changeTariffModalOpen} onOpenChange={setChangeTariffModalOpen} />
      <ConfirmationDialog
        open={deactivateDialog.open}
        onOpenChange={(open) => setDeactivateDialog({ ...deactivateDialog, open })}
        title="Деактивация абонента"
        description={`Вы уверены, что хотите деактивировать абонента "${deactivateDialog.abonent?.name || deactivateDialog.abonent?.phone}"? Это действие нельзя отменить.`}
        confirmText="Деактивировать"
        variant="destructive"
        onConfirm={confirmDeactivate}
      />
    </div>
  );
}