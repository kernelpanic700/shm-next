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
import { useTranslation } from 'react-i18next';

interface ChangeTariffModalProps {
  abonent?: Abonent | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function ChangeTariffModal({ abonent, open, onOpenChange, onSuccess }: ChangeTariffModalProps) {
  const { t, i18n } = useTranslation();
  const [selectedTariff, setSelectedTariff] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { data: tariffs = [], isLoading: isTariffsLoading } = useTariffs();
  const numberLocale = i18n.language.startsWith('en') ? 'en-US' : i18n.language.startsWith('de') ? 'de-DE' : 'ru-RU';
  const activeTariffs = tariffs.filter((tariff) => tariff.is_active);
  const selectedTariffInfo = activeTariffs.find((tariff) => tariff.id === selectedTariff);

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
      toast.success(t('TariffChanged'), {
        description: selectedTariffInfo
          ? `${abonent.full_name || abonent.phone}: ${selectedTariffInfo.name}`
          : abonent.full_name || abonent.phone,
      });
      onSuccess?.();
      onOpenChange(false);
    } catch (error: any) {
      toast.error(t('Error'), {
        description: error.response?.data?.detail || t('TariffChangeFailed'),
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{t('ChangeTariff')}</DialogTitle>
          <DialogDescription>
            {abonent?.full_name || abonent?.phone} • {t('SelectNewTariff')}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="tariff">{t('NewTariff')}</Label>
              <select
                id="tariff"
                value={selectedTariff}
                onChange={(e) => setSelectedTariff(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                required
              >
                <option value="">{t('SelectTariffPlaceholder')}</option>
                {activeTariffs.map((tariff) => (
                  <option key={tariff.id} value={tariff.id}>
                    {tariff.name} - {tariff.price.toLocaleString(numberLocale)} {tariff.currency}
                  </option>
                ))}
              </select>
              {!isTariffsLoading && activeTariffs.length === 0 && (
                <p className="text-sm text-destructive">{t('TariffsNotFound')}</p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              {t('Cancel')}
            </Button>
            <Button type="submit" disabled={isSubmitting || !selectedTariff || activeTariffs.length === 0}>
              {isSubmitting ? t('Saving') : t('ChangeTariff')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
