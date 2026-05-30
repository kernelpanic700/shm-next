'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api, BillingCycleRunResult, WithdrawResult } from '@/lib/api';

export interface BillingCyclePayload {
  periodStart?: string;
  periodEnd?: string;
  offset?: number;
  limit?: number;
}

export interface AbonentWithdrawPayload {
  abonentId: string;
  periodStart?: string;
  periodEnd?: string;
}

export const useRunBillingCycle = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: BillingCyclePayload) => {
      const response = await api.post<BillingCycleRunResult>('/billing/run-cycle', null, {
        params: {
          period_start: payload.periodStart || undefined,
          period_end: payload.periodEnd || undefined,
          offset: payload.offset ?? 0,
          limit: payload.limit ?? 100,
        },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['abonents'] });
    },
  });
};

export const useRunAbonentWithdraw = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: AbonentWithdrawPayload) => {
      const response = await api.post<{ withdraws: WithdrawResult[] }>(
        `/billing/${payload.abonentId}/withdraw`,
        null,
        {
          params: {
            period_start: payload.periodStart || undefined,
            period_end: payload.periodEnd || undefined,
          },
        }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['abonents'] });
    },
  });
};
