'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, BonusEntry, BonusEntryListResponse } from '@/lib/api';

export interface BonusEntryCreatePayload {
  abonent_id: string;
  amount: number;
  currency: string;
  reason: string;
  expires_at?: string | null;
  source: string;
}

interface BonusEntryFilters {
  abonentId?: string;
  activeOnly?: boolean;
  expiredOnly?: boolean;
}

export const useBonusEntries = (filters: BonusEntryFilters = {}) => {
  return useQuery({
    queryKey: ['bonus-entries', filters],
    queryFn: async () => {
      const response = await api.get<BonusEntryListResponse>('/bonus-entries', {
        params: {
          abonent_id: filters.abonentId || undefined,
          active_only: filters.activeOnly || undefined,
          expired_only: filters.expiredOnly || undefined,
        },
      });
      return response.data.items;
    },
  });
};

export const useCreateBonusEntry = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: BonusEntryCreatePayload) => {
      const response = await api.post<BonusEntry>('/bonus-entries', payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bonus-entries'] });
    },
  });
};

export const useExpireBonusEntry = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (entryId: string) => {
      const response = await api.post<BonusEntry>(`/bonus-entries/${entryId}/expire`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bonus-entries'] });
    },
  });
};
