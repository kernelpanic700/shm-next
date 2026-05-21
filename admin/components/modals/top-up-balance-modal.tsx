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
import { Abonent } from '@/lib/api';
import { DollarSign, CreditCard, Banknote, Smartphone } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

interface TopUpBalanceModalProps {
  abonent: Abonent | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

const paymentMethods = [
  { value: 'CASH', label: 'Наличные', icon: Banknote },
  { value: 'CARD', label: 'Банковская карта', icon: CreditCard },
  { value: 'MOBILE', label: 'Мобильный платеж', icon: Smartphone },
];

export function TopUpBalanceModal({ abonent, open, onOpenChange, onSuccess }: TopUpBalanceModalProps) {
  const [amount, setAmount] = useState<string>('');
  const [paymentMethod, setPaymentMethod] = useState<string>('CARD');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [amountError, setAmountError] = useState<string>('');

  const validateAmount = (value: string): boolean => {
    const num = parseFloat(value);
    if (!value) {
      setAmountError('Введите сумму');
      return false;
    }
    if (isNaN(num) || num <= 0) {
      setAmountError('Сумма должна быть больше 0');
      return false;
    }
    setAmountError('');
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!abonent || !validateAmount(amount)) return;

    setIsSubmitting(true);
    try {
      await api.post(`/abonents/${abonent.id}/balance/top-up`, {
        amount: parseFloat(amount),
        payment_method: paymentMethod,
      });
      toast.success('Баланс пополнен', {
        description: `На счёт ${abonent.name || abonent.phone} зачислено ${parseFloat(amount).toLocaleString('ru-RU', { minimumFractionDigits: 2 })}`,
      });
      onSuccess?.();
      onOpenChange(false);
      setAmount('');
    } catch (error: any) {
      toast.error('Ошибка пополнения', {
        description: error.response?.data?.detail || 'Не удалось пополнить баланс',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Пополнение баланса</DialogTitle>
          <DialogDescription>
            {abonent?.name || abonent?.phone} • Лицевой счёт: {abonent?.account_number}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="amount">Сумма пополнения</Label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="0.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  onBlur={(e) => validateAmount(e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
              {amountError && <p className="text-sm text-destructive">{amountError}</p>}
            </div>
            <div className="space-y-2">
              <Label>Способ оплаты</Label>
              <div className="grid grid-cols-3 gap-2">
                {paymentMethods.map((method) => {
                  const Icon = method.icon;
                  return (
                    <button
                      key={method.value}
                      type="button"
                      onClick={() => setPaymentMethod(method.value)}
                      className={`flex flex-col items-center p-3 rounded-lg border transition-colors ${
                        paymentMethod === method.value
                          ? 'border-primary bg-primary/5'
                          : 'border-input hover:bg-accent'
                      }`}
                    >
                      <Icon className="h-5 w-5 mb-1" />
                      <span className="text-xs">{method.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={isSubmitting || !amount}>
              {isSubmitting ? 'Пополняем...' : 'Пополнить'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}