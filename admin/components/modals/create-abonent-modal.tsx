'use client';

import { useState } from 'react';
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
import { UserPlus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { useCreateAbonent } from '@/lib/hooks/use-abonents';

interface CreateAbonentModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function CreateAbonentModal({ open, onOpenChange, onSuccess }: CreateAbonentModalProps) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    email: '',
    account_number: '',
    login: '',
    contract: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const createAbonent = useCreateAbonent();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await createAbonent.mutateAsync({
        full_name: formData.full_name,
        phone: formData.phone,
        email: formData.email || undefined,
        account_number: formData.account_number,
        login: formData.login || formData.phone,
        contract: formData.contract || formData.account_number,
        currency: 'RUB',
        balance: 0,
        status: 'ACTIVE',
      });
      toast.success(t('Created'));
      onSuccess?.();
      onOpenChange(false);
      setFormData({ full_name: '', phone: '', email: '', account_number: '', login: '', contract: '' });
    } catch (error) {
      console.error('Failed to create abonent:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{t('NewAbonent')}</DialogTitle>
          <DialogDescription>
            {t('CreateAbonentDescription')}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="full_name">{t('FullName')}</Label>
              <Input
                id="full_name"
                placeholder={t('FullNamePlaceholder')}
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="account_number">{t('AccountNumber')}</Label>
              <Input
                id="account_number"
                value={formData.account_number}
                onChange={(e) => setFormData({ ...formData, account_number: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="login">Login</Label>
              <Input
                id="login"
                value={formData.login}
                onChange={(e) => setFormData({ ...formData, login: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">{t('Phone')}</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="+7 (999) 123-45-67"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">{t('EmailOptional')}</Label>
              <Input
                id="email"
                type="email"
                placeholder="ivanov@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="contract">Contract</Label>
              <Input
                id="contract"
                value={formData.contract}
                onChange={(e) => setFormData({ ...formData, contract: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              {t('Cancel')}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? t('Creating') : t('Create')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
