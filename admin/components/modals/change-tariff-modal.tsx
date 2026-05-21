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
import { Label } from '@/components/ui/label';
import { Abonent, Tariff } from '@/lib/api';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { useTariffs } from '@/lib/hooks/use-tariffs';

interface ChangeTariffModalProps {
  abonent?: Abonent | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function ChangeTariffModal({ abonent, open, onOpenChange, onSuccess }: ChangeTariffModalProps) {
  const [selectedTariff, setSelectedTariff] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { data: tariffs = [] } = useTariffs();

  useEffect(() => {
    if (open) {
      setSelectedTariff('');
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!abonent || !selectedTariff) return;

    setIsSubmitting(true);
    try {
      await api.patch(`/abonents/${abonent.id}`, { tariff_id: selectedTariff });
      toast.success('Тариф изменён');
      onSuccess?.();
      onOpenChange(false);
    } catch (error: any) {
      toast.error('Ошибка', {
        description: error.response?.data?.detail || 'Не удалось изменить тариф',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Смена тарифа</DialogTitle>
          <DialogDescription>
            {abonent?.name || abonent?.phone} • Выберите новый тариф
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="tariff">Новый тариф</Label>
              <select
                id="tariff"
                value={selectedTariff}
                onChange={(e) => setSelectedTariff(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                required
              >
                <option value="">Выберите тариф...</option>
                {tariffs.filter(t => t.is_active).map((tariff) => (
                  <option key={tariff.id} value={tariff.id}>
                    {tariff.name} — {tariff.price.toLocaleString('ru-RU')} {tariff.currency}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={isSubmitting || !selectedTariff}>
              {isSubmitting ? 'Сохраняем...' : 'Сменить тариф'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}