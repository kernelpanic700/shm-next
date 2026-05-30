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
import { useTranslation } from 'react-i18next';

interface TariffModalProps {
  tariff?: Tariff | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function TariffModal({ tariff, open, onOpenChange, onSuccess }: TariffModalProps) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    billing_cycle: 'monthly',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const billingCycles = [
    { value: 'monthly', label: t('Monthly') },
    { value: 'quarterly', label: t('Quarterly') },
    { value: 'yearly', label: t('Yearly') },
  ];

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
        toast.success(t('TariffUpdated'));
      } else {
        await api.post('/tariffs', formData);
        toast.success(t('TariffCreated'));
      }
      onSuccess?.();
      onOpenChange(false);
    } catch (error: any) {
      toast.error(t('Error'), {
        description: error.response?.data?.detail || t('TariffSaveFailed'),
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{tariff ? t('EditTariff') : t('NewTariffTitle')}</DialogTitle>
          <DialogDescription>
            {tariff ? t('EditTariffDescription', { name: tariff.name }) : t('CreateTariffDescription')}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">{t('Name')}</Label>
              <Input
                id="name"
                placeholder={t('TariffNamePlaceholder')}
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">{t('Description')}</Label>
              <Textarea
                id="description"
                placeholder={t('TariffDescriptionPlaceholder')}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="price">{t('Price')}</Label>
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
                <Label htmlFor="billing_cycle">{t('Period')}</Label>
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
              {t('Cancel')}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? t('Saving') : tariff ? t('Save') : t('Create')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
