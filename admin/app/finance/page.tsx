'use client';

export const dynamic = 'force-dynamic';

import { FormEvent, useCallback, useMemo, useState } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { format } from 'date-fns';
import { de, enUS, ru } from 'date-fns/locale';
import { Gift, Percent, Plus, PowerOff, RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { DataTable } from '@/components/ui/data-table';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { useAbonents } from '@/lib/hooks/use-abonents';
import { useBonusEntries, useCreateBonusEntry, useExpireBonusEntry } from '@/lib/hooks/use-bonus-entries';
import { useCreateDiscount, useDeactivateDiscount, useDiscounts } from '@/lib/hooks/use-discounts';
import { Abonent, BonusEntry, Discount } from '@/lib/api';

type BonusTableMeta = {
  abonents: Abonent[];
  onExpire: (entryId: string) => void;
  expiringId?: string;
};

type DiscountTableMeta = {
  onDeactivate: (discountId: string) => void;
  deactivatingId?: string;
};

const getDateLocale = (language: string) => {
  if (language.startsWith('de')) return de;
  if (language.startsWith('en')) return enUS;
  return ru;
};

const toOptionalIso = (value: string) => {
  if (!value) {
    return null;
  }
  return new Date(value).toISOString();
};

const StatusBadge = ({ active, label }: { active: boolean; label: string }) => (
  <span className={`px-2 py-1 rounded-full text-xs font-medium ${active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-700'}`}>
    {label}
  </span>
);

export default function FinancePage() {
  const { t, i18n } = useTranslation();
  const [bonusAbonentId, setBonusAbonentId] = useState('');
  const [bonusAmount, setBonusAmount] = useState('');
  const [bonusReason, setBonusReason] = useState('');
  const [bonusExpiresAt, setBonusExpiresAt] = useState('');
  const [bonusSource, setBonusSource] = useState('manual');
  const [bonusFilter, setBonusFilter] = useState<'active' | 'expired'>('active');

  const [discountName, setDiscountName] = useState('');
  const [discountDescription, setDiscountDescription] = useState('');
  const [discountType, setDiscountType] = useState<Discount['discount_type']>('percent');
  const [discountValue, setDiscountValue] = useState('');
  const [discountValidTo, setDiscountValidTo] = useState('');
  const [discountMaxUses, setDiscountMaxUses] = useState('');
  const [discountFilter, setDiscountFilter] = useState<'active' | 'valid'>('active');

  const { data: abonents = [] } = useAbonents();
  const {
    data: bonusEntries = [],
    isLoading: isBonusesLoading,
    isError: isBonusesError,
    refetch: refetchBonuses,
  } = useBonusEntries({ activeOnly: bonusFilter === 'active', expiredOnly: bonusFilter === 'expired' });
  const {
    data: discounts = [],
    isLoading: isDiscountsLoading,
    isError: isDiscountsError,
    refetch: refetchDiscounts,
  } = useDiscounts({ activeOnly: discountFilter === 'active', validNow: discountFilter === 'valid' });

  const createBonus = useCreateBonusEntry();
  const expireBonus = useExpireBonusEntry();
  const createDiscount = useCreateDiscount();
  const deactivateDiscount = useDeactivateDiscount();

  const dateLocale = getDateLocale(i18n.language);
  const numberLocale = i18n.language.startsWith('en') ? 'en-US' : i18n.language.startsWith('de') ? 'de-DE' : 'ru-RU';
  const formatDateTime = useCallback((value?: string | null) => {
    if (!value) {
      return '-';
    }
    return format(new Date(value), 'dd MMM yyyy HH:mm', { locale: dateLocale });
  }, [dateLocale]);

  const firstAbonentId = useMemo(() => abonents[0]?.id || '', [abonents]);
  const selectedBonusAbonentId = bonusAbonentId || firstAbonentId;

  const bonusColumns = useMemo<ColumnDef<BonusEntry>[]>(() => [
    {
      accessorKey: 'abonent_id',
      header: t('Abonent'),
      cell: ({ row, table }) => {
        const abonentId = row.getValue('abonent_id') as string;
        const meta = table.options.meta as BonusTableMeta | undefined;
        const abonent = meta?.abonents.find((item) => item.id === abonentId);
        return <span>{abonent?.full_name || abonent?.phone || abonentId.slice(0, 8)}</span>;
      },
    },
    {
      accessorKey: 'amount',
      header: t('Amount'),
      cell: ({ row }) => (
        <span className="font-medium">
          {Number(row.original.amount).toLocaleString(numberLocale, { minimumFractionDigits: 2 })} {row.original.currency}
        </span>
      ),
    },
    {
      accessorKey: 'reason',
      header: t('Reason'),
      cell: ({ row }) => <span className="line-clamp-2 max-w-[260px]">{row.original.reason || '-'}</span>,
    },
    {
      accessorKey: 'source',
      header: t('Source'),
    },
    {
      accessorKey: 'expires_at',
      header: t('ExpiresAt'),
      cell: ({ row }) => formatDateTime(row.original.expires_at),
    },
    {
      accessorKey: 'is_active',
      header: t('Status'),
      cell: ({ row }) => <StatusBadge active={row.original.is_active} label={row.original.is_active ? t('Active') : t('Disabled')} />,
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row, table }) => {
        const meta = table.options.meta as BonusTableMeta | undefined;
        const disabled = !row.original.is_active || meta?.expiringId === row.original.id;
        return (
          <Button
            variant="outline"
            size="sm"
            disabled={disabled}
            onClick={() => meta?.onExpire(row.original.id)}
            title={t('DeactivateBonus')}
          >
            <PowerOff className="h-4 w-4" />
          </Button>
        );
      },
    },
  ], [formatDateTime, numberLocale, t]);

  const discountColumns = useMemo<ColumnDef<Discount>[]>(() => [
    {
      accessorKey: 'name',
      header: t('Name'),
      cell: ({ row }) => (
        <div className="max-w-[280px]">
          <div className="font-medium">{row.original.name}</div>
          {row.original.description && (
            <div className="line-clamp-1 text-xs text-muted-foreground">{row.original.description}</div>
          )}
        </div>
      ),
    },
    {
      accessorKey: 'discount_type',
      header: t('Type'),
      cell: ({ row }) => {
        const labels: Record<Discount['discount_type'], string> = {
          percent: t('DiscountTypePercent'),
          fixed: t('DiscountTypeFixedShort'),
          relative: t('DiscountTypeRelativeShort'),
        };
        return labels[row.original.discount_type] || row.original.discount_type;
      },
    },
    {
      accessorKey: 'value',
      header: t('Value'),
      cell: ({ row }) => (
        <span className="font-medium">
          {Number(row.original.value).toLocaleString(numberLocale, { maximumFractionDigits: 2 })}
          {row.original.discount_type === 'percent' ? '%' : ` ${row.original.currency}`}
        </span>
      ),
    },
    {
      accessorKey: 'valid_to',
      header: t('ValidTo'),
      cell: ({ row }) => formatDateTime(row.original.valid_to),
    },
    {
      accessorKey: 'used_count',
      header: t('Used'),
      cell: ({ row }) => `${row.original.used_count}${row.original.max_uses ? ` / ${row.original.max_uses}` : ''}`,
    },
    {
      accessorKey: 'is_active',
      header: t('Status'),
      cell: ({ row }) => <StatusBadge active={row.original.is_active} label={row.original.is_active ? t('Active') : t('Disabled')} />,
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row, table }) => {
        const meta = table.options.meta as DiscountTableMeta | undefined;
        const disabled = !row.original.is_active || meta?.deactivatingId === row.original.id;
        return (
          <Button
            variant="outline"
            size="sm"
            disabled={disabled}
            onClick={() => meta?.onDeactivate(row.original.id)}
            title={t('DeactivateDiscount')}
          >
            <PowerOff className="h-4 w-4" />
          </Button>
        );
      },
    },
  ], [formatDateTime, numberLocale, t]);

  const handleCreateBonus = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedBonusAbonentId || !bonusAmount) {
      toast.error(t('SelectAbonentAndAmount'));
      return;
    }

    try {
      await createBonus.mutateAsync({
        abonent_id: selectedBonusAbonentId,
        amount: Number(bonusAmount),
        currency: 'RUB',
        reason: bonusReason,
        expires_at: toOptionalIso(bonusExpiresAt),
        source: bonusSource,
      });
      setBonusAmount('');
      setBonusReason('');
      setBonusExpiresAt('');
      toast.success(t('BonusCreated'));
    } catch {
      toast.error(t('BonusCreateFailed'));
    }
  };

  const handleCreateDiscount = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!discountName || !discountValue) {
      toast.error(t('FillDiscountNameAndValue'));
      return;
    }

    try {
      await createDiscount.mutateAsync({
        name: discountName,
        description: discountDescription,
        discount_type: discountType,
        value: Number(discountValue),
        currency: 'RUB',
        valid_to: toOptionalIso(discountValidTo),
        is_active: true,
        max_uses: discountMaxUses ? Number(discountMaxUses) : null,
      });
      setDiscountName('');
      setDiscountDescription('');
      setDiscountValue('');
      setDiscountValidTo('');
      setDiscountMaxUses('');
      toast.success(t('DiscountCreated'));
    } catch {
      toast.error(t('DiscountCreateFailed'));
    }
  };

  const handleExpireBonus = async (entryId: string) => {
    try {
      await expireBonus.mutateAsync(entryId);
      toast.success(t('BonusDeactivated'));
    } catch {
      toast.error(t('BonusDeactivateFailed'));
    }
  };

  const handleDeactivateDiscount = async (discountId: string) => {
    try {
      await deactivateDiscount.mutateAsync(discountId);
      toast.success(t('DiscountDeactivated'));
    } catch {
      toast.error(t('DiscountDeactivateFailed'));
    }
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-3xl font-bold tracking-tight">{t('Finance')}</h2>
        <Button variant="outline" onClick={() => { refetchBonuses(); refetchDiscounts(); }}>
          <RefreshCw className="mr-2 h-4 w-4" />
          {t('Refresh')}
        </Button>
      </div>

      <Tabs defaultValue="bonuses" className="space-y-4">
        <TabsList>
          <TabsTrigger value="bonuses">
            <Gift className="mr-2 h-4 w-4" />
            {t('Bonuses')}
          </TabsTrigger>
          <TabsTrigger value="discounts">
            <Percent className="mr-2 h-4 w-4" />
            {t('Discounts')}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="bonuses" className="space-y-4">
          <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
            <Card>
              <CardHeader>
                <CardTitle>{t('CreateBonus')}</CardTitle>
                <CardDescription>{t('CreateBonusDescription')}</CardDescription>
              </CardHeader>
              <CardContent>
                <form className="space-y-3" onSubmit={handleCreateBonus}>
                  <div className="space-y-2">
                    <Label htmlFor="bonus-abonent">{t('Abonent')}</Label>
                    <Select id="bonus-abonent" value={selectedBonusAbonentId} onChange={(event) => setBonusAbonentId(event.target.value)}>
                      {abonents.map((abonent) => (
                        <option key={abonent.id} value={abonent.id}>
                          {abonent.full_name || abonent.phone || abonent.id.slice(0, 8)}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div className="grid grid-cols-[1fr_88px] gap-2">
                    <div className="space-y-2">
                      <Label htmlFor="bonus-amount">{t('Amount')}</Label>
                      <Input id="bonus-amount" type="number" min="0" step="0.01" value={bonusAmount} onChange={(event) => setBonusAmount(event.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="bonus-currency">{t('Currency')}</Label>
                      <Input id="bonus-currency" value="RUB" disabled />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bonus-reason">{t('Reason')}</Label>
                    <Textarea id="bonus-reason" rows={3} value={bonusReason} onChange={(event) => setBonusReason(event.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bonus-expires">{t('ExpiresAt')}</Label>
                    <Input id="bonus-expires" type="datetime-local" value={bonusExpiresAt} onChange={(event) => setBonusExpiresAt(event.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bonus-source">{t('Source')}</Label>
                    <Input id="bonus-source" value={bonusSource} onChange={(event) => setBonusSource(event.target.value)} />
                  </div>
                  <Button type="submit" disabled={createBonus.isPending || !selectedBonusAbonentId} className="w-full">
                    <Plus className="mr-2 h-4 w-4" />
                    {t('Create')}
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <CardTitle>{t('BonusEntries')}</CardTitle>
                  <CardDescription>{t('TotalCount', { count: bonusEntries.length })}</CardDescription>
                </div>
                <Select className="w-full sm:w-44" value={bonusFilter} onChange={(event) => setBonusFilter(event.target.value as 'active' | 'expired')}>
                  <option value="active">{t('ActivePlural')}</option>
                  <option value="expired">{t('ExpiredPlural')}</option>
                </Select>
              </CardHeader>
              <CardContent>
                {isBonusesLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-64 w-full" />
                  </div>
                ) : isBonusesError ? (
                  <Button variant="outline" onClick={() => refetchBonuses()}>{t('Reload')}</Button>
                ) : (
                  <DataTable
                    columns={bonusColumns}
                    data={bonusEntries}
                    searchKey="reason"
                    searchPlaceholder={t('SearchByReason')}
                    meta={{
                      abonents,
                      onExpire: handleExpireBonus,
                      expiringId: expireBonus.variables,
                    }}
                  />
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="discounts" className="space-y-4">
          <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
            <Card>
              <CardHeader>
                <CardTitle>{t('CreateDiscount')}</CardTitle>
                <CardDescription>{t('CreateDiscountDescription')}</CardDescription>
              </CardHeader>
              <CardContent>
                <form className="space-y-3" onSubmit={handleCreateDiscount}>
                  <div className="space-y-2">
                    <Label htmlFor="discount-name">{t('Name')}</Label>
                    <Input id="discount-name" value={discountName} onChange={(event) => setDiscountName(event.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="discount-description">{t('Description')}</Label>
                    <Textarea id="discount-description" rows={3} value={discountDescription} onChange={(event) => setDiscountDescription(event.target.value)} />
                  </div>
                  <div className="grid grid-cols-[1fr_120px] gap-2">
                    <div className="space-y-2">
                      <Label htmlFor="discount-type">{t('Type')}</Label>
                      <Select id="discount-type" value={discountType} onChange={(event) => setDiscountType(event.target.value as Discount['discount_type'])}>
                        <option value="percent">{t('DiscountTypePercent')}</option>
                        <option value="fixed">{t('DiscountTypeFixed')}</option>
                        <option value="relative">{t('DiscountTypeRelative')}</option>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="discount-value">{t('Value')}</Label>
                      <Input id="discount-value" type="number" min="0" step="0.01" value={discountValue} onChange={(event) => setDiscountValue(event.target.value)} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="discount-valid-to">{t('ValidTo')}</Label>
                    <Input id="discount-valid-to" type="datetime-local" value={discountValidTo} onChange={(event) => setDiscountValidTo(event.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="discount-max-uses">{t('UsageLimit')}</Label>
                    <Input id="discount-max-uses" type="number" min="1" value={discountMaxUses} onChange={(event) => setDiscountMaxUses(event.target.value)} />
                  </div>
                  <Button type="submit" disabled={createDiscount.isPending} className="w-full">
                    <Plus className="mr-2 h-4 w-4" />
                    {t('Create')}
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <CardTitle>{t('Discounts')}</CardTitle>
                  <CardDescription>{t('TotalCount', { count: discounts.length })}</CardDescription>
                </div>
                <Select className="w-full sm:w-44" value={discountFilter} onChange={(event) => setDiscountFilter(event.target.value as 'active' | 'valid')}>
                  <option value="active">{t('ActivePlural')}</option>
                  <option value="valid">{t('ValidNow')}</option>
                </Select>
              </CardHeader>
              <CardContent>
                {isDiscountsLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-64 w-full" />
                  </div>
                ) : isDiscountsError ? (
                  <Button variant="outline" onClick={() => refetchDiscounts()}>{t('Reload')}</Button>
                ) : (
                  <DataTable
                    columns={discountColumns}
                    data={discounts}
                    searchKey="name"
                    searchPlaceholder={t('SearchByName')}
                    meta={{
                      onDeactivate: handleDeactivateDiscount,
                      deactivatingId: deactivateDiscount.variables,
                    }}
                  />
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
