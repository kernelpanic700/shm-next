'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { RefreshCw, RefreshCcw, X, Eye } from 'lucide-react';
import { DataTable } from '@/components/ui/data-table';
import { useSpoolTasks, useRetryTask, useCancelTask } from '@/lib/hooks/use-spool-tasks';
import { ColumnDef } from '@tanstack/react-table';
import { SpoolTask } from '@/lib/api';
import { toast } from 'sonner';
import { Skeleton } from '@/components/ui/skeleton';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const statusColors: Record<string, string> = {
  NEW: 'bg-blue-100 text-blue-800',
  PROCESSING: 'bg-yellow-100 text-yellow-800',
  COMPLETED: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  RETRY: 'bg-orange-100 text-orange-800',
};

const priorityColors: Record<number, string> = {
  1: 'bg-red-100 text-red-800',
  2: 'bg-orange-100 text-orange-800',
  3: 'bg-yellow-100 text-yellow-800',
  4: 'bg-blue-100 text-blue-800',
  5: 'bg-gray-100 text-gray-800',
};

const columns: ColumnDef<SpoolTask>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
    cell: ({ row }) => {
      const id = row.getValue('id') as string;
      return <span className="font-mono text-xs">{id.slice(0, 8)}...</span>;
    },
  },
  {
    accessorKey: 'action_type',
    header: 'Action Type',
    cell: ({ row }) => {
      const type = row.getValue('action_type') as string;
      return (
        <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
          {type}
        </span>
      );
    },
  },
  {
    accessorKey: 'status',
    header: 'Статус',
    cell: ({ row }) => {
      const status = row.getValue('status') as string;
      return (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
          {status}
        </span>
      );
    },
  },
  {
    accessorKey: 'priority',
    header: 'Priority',
    cell: ({ row }) => {
      const priority = row.getValue('priority') as number;
      return (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityColors[priority] || 'bg-gray-100 text-gray-800'}`}>
          {priority}
        </span>
      );
    },
  },
  {
    accessorKey: 'retry_count',
    header: 'Retry',
    cell: ({ row }) => {
      const retry = row.getValue('retry_count') as number;
      const max = row.original.max_retries;
      return <span className="text-sm">{retry} / {max}</span>;
    },
  },
  {
    accessorKey: 'execute_after',
    header: 'Execute After',
    cell: ({ row }) => {
      const date = row.getValue('execute_after') as string | null;
      return date ? format(new Date(date), 'dd MMM HH:mm', { locale: ru }) : '-';
    },
  },
  {
    accessorKey: 'created_at',
    header: 'Created',
    cell: ({ row }) => {
      const date = row.getValue('created_at') as string;
      return format(new Date(date), 'dd MMM yyyy HH:mm', { locale: ru });
    },
  },
  {
    accessorKey: 'error_message',
    header: 'Error',
    cell: ({ row }) => {
      const error = row.getValue('error_message') as string | null;
      return error ? <span className="text-red-600 text-xs max-w-[200px] truncate">{error}</span> : '-';
    },
  },
  {
    id: 'actions',
    header: 'Действия',
    cell: ({ row, table }) => {
      const task = row.original;
      const onRetry = (table.options.meta as any)?.onRetry;
      const onCancel = (table.options.meta as any)?.onCancel;
      const onView = (table.options.meta as any)?.onView;
      
      return (
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" onClick={() => onView(task)} title="Просмотр">
            <Eye className="h-4 w-4" />
          </Button>
          {(task.status === 'FAILED' || task.status === 'RETRY') && (
            <Button variant="ghost" size="sm" onClick={() => onRetry(task.id)} title="Retry">
              <RefreshCw className="h-4 w-4" />
            </Button>
          )}
          {task.status === 'NEW' && (
            <Button variant="ghost" size="sm" onClick={() => onCancel(task.id)} title="Cancel">
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      );
    },
    enableSorting: false,
  },
];

export default function SpoolPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [dateFilter, setDateFilter] = useState<string>('');
  const [selectedTask, setSelectedTask] = useState<SpoolTask | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const { data: tasks = [], isLoading, isError, refetch } = useSpoolTasks();
  const retryMutation = useRetryTask();
  const cancelMutation = useCancelTask();

  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      if (statusFilter !== 'all' && task.status !== statusFilter) return false;
      if (typeFilter !== 'all' && task.action_type !== typeFilter) return false;
      if (priorityFilter !== 'all' && task.priority.toString() !== priorityFilter) return false;
      if (dateFilter && new Date(task.created_at) < new Date(dateFilter)) return false;
      return true;
    });
  }, [tasks, statusFilter, typeFilter, priorityFilter, dateFilter]);

  const stats = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    return {
      total: tasks.length,
      pending: tasks.filter(t => t.status === 'NEW').length,
      processing: tasks.filter(t => t.status === 'PROCESSING').length,
      failed: tasks.filter(t => t.status === 'FAILED' || t.status === 'RETRY').length,
      today: tasks.filter(t => new Date(t.created_at) >= today).length,
    };
  }, [tasks]);

  const handleRetry = async (id: string) => {
    try {
      await retryMutation.mutateAsync(id);
      toast.success('Задача отправлена на повторный запуск');
    } catch {
      toast.error('Не удалось повторить задачу');
    }
  };

  const handleCancel = async (id: string) => {
    try {
      await cancelMutation.mutateAsync(id);
      toast.success('Задача отменена');
    } catch {
      toast.error('Не удалось отменить задачу');
    }
  };

  const handleView = (task: SpoolTask) => {
    setSelectedTask(task);
    setDetailsOpen(true);
  };

  if (isLoading) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <h2 className="text-3xl font-bold tracking-tight">SPOOL Tasks</h2>
        <div className="grid gap-4 md:grid-cols-5">
          {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-10" />)}
        </div>
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex-1 p-8">
        <p className="text-destructive">Ошибка загрузки задач</p>
        <Button variant="outline" onClick={() => refetch()} className="mt-4">Попробовать снова</Button>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">SPOOL Tasks</h2>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" /> Обновить
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Total</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{stats.total}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Pending</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-blue-600">{stats.pending}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Processing</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-yellow-600">{stats.processing}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Failed</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-red-600">{stats.failed}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Today</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{stats.today}</p></CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="grid gap-4 md:grid-cols-5">
        <select 
          className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">Все статусы</option>
          <option value="NEW">NEW</option>
          <option value="PROCESSING">PROCESSING</option>
          <option value="COMPLETED">COMPLETED</option>
          <option value="FAILED">FAILED</option>
          <option value="RETRY">RETRY</option>
        </select>
        <Input placeholder="Тип действия" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} />
        <select 
          className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
        >
          <option value="all">Все приоритеты</option>
          <option value="1">1 (Highest)</option>
          <option value="2">2</option>
          <option value="3">3</option>
          <option value="4">4</option>
          <option value="5">5 (Lowest)</option>
        </select>
        <Input type="date" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Task Queue</CardTitle>
          <CardDescription>Всего: {filteredTasks.length} задач</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable 
            columns={columns} 
            data={filteredTasks} 
            searchKey="id"
            meta={{ onRetry: handleRetry, onCancel: handleCancel, onView: handleView }}
          />
        </CardContent>
      </Card>

      {/* Details Dialog */}
      <Dialog open={detailsOpen} onOpenChange={setDetailsOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Детали задачи</DialogTitle>
            <DialogDescription>
              ID: {selectedTask?.id}
            </DialogDescription>
          </DialogHeader>
          {selectedTask && (
            <div className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">Payload</h4>
                <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto max-h-64">
                  {JSON.stringify(selectedTask.payload, null, 2)}
                </pre>
              </div>
              {selectedTask.result && (
                <div>
                  <h4 className="font-medium mb-2">Result</h4>
                  <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto max-h-64">
                    {JSON.stringify(selectedTask.result, null, 2)}
                  </pre>
                </div>
              )}
              {selectedTask.error_message && (
                <div>
                  <h4 className="font-medium mb-2 text-red-600">Error</h4>
                  <p className="text-sm text-red-600">{selectedTask.error_message}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}