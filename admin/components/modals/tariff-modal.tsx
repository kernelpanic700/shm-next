'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tariff } from '@/lib/api';
import { api } from '@/lib/api';
import { toast } from 'sonner';

interface TariffModalProps {
  tariff?: Tariff | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

const billingCycles = [
  { value: 'monthly', label: 'Месячный' },
  { value: 'quarterly', label: 'Квартальный' },
  { value: 'yearly', label: 'Годовой' },
];

export function TariffModal({ tariff, open, onOpenChange, onSuccess }: TariffModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    billing_cycle: 'monthly',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (tariff) {
      setFormData({
        name: tariff.name || '',
        description: tariff.description || '',
        price: tariff.price?.toString() || '',
        billing_cycle: tariff.billing_cycle || 'monthly',
      });
    } else {
      setFormData({
        name: '',
        description: '',
        price: '',
        billing_cycle: 'monthly',
      });
    }
  }, [tariff, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      if (tariff) {
        await api.patch(`/tariffs/${tariff.id}`, formData);
        toast.success('Тариф обновлён');
      } else {
        await api.post('/tariffs', formData);
        toast.success('Тариф создан');
      }
      onSuccess?.();
      onOpenChange(false);
    } catch (error: any) {
      toast.error('Ошибка', {
        description: error.response?.data?.detail || 'Не удалось сохранить тариф',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{tariff ? 'Редактировать тариф' : 'Новый тариф'}</DialogTitle>
          <DialogDescription>
            {tariff ? `Изменение тарифа: ${tariff.name}` : 'Создайте новый тариф в системе'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Название</Label>
              <Input
                id="name"
                placeholder="Тариф Оптимум"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Описание</Label>
              <Textarea
                id="description"
                placeholder="Описание тарифа"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="price">Цена</Label>
                <Input
                  id="price"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="500.00"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="billing_cycle">Период</Label>
                <select
                  id="billing_cycle"
                  value={formData.billing_cycle}
                  onChange={(e) => setFormData({ ...formData, billing_cycle: e.target.value })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {billingCycles.map((cycle) => (
                    <option key={cycle.value} value={cycle.value}>
                      {cycle.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Сохраняем...' : tariff ? 'Сохранить' : 'Создать'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}