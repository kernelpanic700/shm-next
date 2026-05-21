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
import { Service } from '@/lib/api';
import { api } from '@/lib/api';
import { toast } from 'sonner';

interface ServiceModalProps {
  service?: Service | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function ServiceModal({ service, open, onOpenChange, onSuccess }: ServiceModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (service) {
      setFormData({
        name: service.name || '',
        description: service.description || '',
        price: service.price?.toString() || '',
      });
    } else {
      setFormData({
        name: '',
        description: '',
        price: '',
      });
    }
  }, [service, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      if (service) {
        await api.patch(`/services/${service.id}`, formData);
        toast.success('Услуга обновлена');
      } else {
        await api.post('/services', formData);
        toast.success('Услуга создана');
      }
      onSuccess?.();
      onOpenChange(false);
    } catch (error: any) {
      toast.error('Ошибка', {
        description: error.response?.data?.detail || 'Не удалось сохранить услугу',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{service ? 'Редактировать услугу' : 'Новая услуга'}</DialogTitle>
          <DialogDescription>
            {service ? `Изменение услуги: ${service.name}` : 'Создайте новую услугу в системе'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Название</Label>
              <Input
                id="name"
                placeholder="Интернет-услуга"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Описание</Label>
              <Textarea
                id="description"
                placeholder="Описание услуги..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="price">Цена</Label>
              <Input
                id="price"
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                required
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Сохраняем...' : service ? 'Обновить' : 'Создать'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}