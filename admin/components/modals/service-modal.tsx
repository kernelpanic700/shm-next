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
import { useTranslation } from 'react-i18next';

interface ServiceModalProps {
  service?: Service | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function ServiceModal({ service, open, onOpenChange, onSuccess }: ServiceModalProps) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    cost: '',
    currency: 'RUB',
    period_cost: '1.0000',
    category: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (service) {
      setFormData({
        name: service.name || '',
        description: service.description || '',
        cost: String(service.cost ?? service.price ?? ''),
        currency: service.currency || 'RUB',
        period_cost: service.period_cost || '1.0000',
        category: service.category || '',
      });
    } else {
      setFormData({
        name: '',
        description: '',
        cost: '',
        currency: 'RUB',
        period_cost: '1.0000',
        category: '',
      });
    }
  }, [service, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    const payload = {
      name: formData.name,
      description: formData.description || null,
      cost: Number(formData.cost || 0),
      currency: formData.currency || 'RUB',
      period_cost: formData.period_cost || '1.0000',
      category: formData.category || null,
      allow_to_order: true,
    };

    try {
      if (service) {
        await api.patch(`/catalog-services/${service.id}`, payload);
        toast.success(t('ServiceUpdated'));
      } else {
        await api.post('/catalog-services', payload);
        toast.success(t('ServiceCreated'));
      }
      onSuccess?.();
      onOpenChange(false);
    } catch (error: any) {
      toast.error(t('Error'), {
        description: error.response?.data?.detail || t('ServiceSaveFailed'),
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{service ? t('EditService') : t('NewService')}</DialogTitle>
          <DialogDescription>
            {service ? t('EditServiceDescription', { name: service.name }) : t('CreateServiceDescription')}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">{t('Name')}</Label>
              <Input
                id="name"
                placeholder={t('ServiceNamePlaceholder')}
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">{t('Description')}</Label>
              <Textarea
                id="description"
                placeholder={t('ServiceDescriptionPlaceholder')}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="cost">{t('Price')}</Label>
              <Input
                id="cost"
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                value={formData.cost}
                onChange={(e) => setFormData({ ...formData, cost: e.target.value })}
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="currency">{t('Currency')}</Label>
                <Input
                  id="currency"
                  maxLength={3}
                  value={formData.currency}
                  onChange={(e) => setFormData({ ...formData, currency: e.target.value.toUpperCase() })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="period_cost">{t('Period')}</Label>
                <Input
                  id="period_cost"
                  value={formData.period_cost}
                  onChange={(e) => setFormData({ ...formData, period_cost: e.target.value })}
                  required
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="category">{t('Category')}</Label>
              <Input
                id="category"
                placeholder="base"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              {t('Cancel')}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? t('Saving') : service ? t('Update') : t('Create')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
