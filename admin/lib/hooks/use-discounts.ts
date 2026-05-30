'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, Discount, DiscountListResponse } from '@/lib/api';

export interface DiscountCreatePayload {
  name: string;
  description: string;
  discount_type: 'percent' | 'fixed' | 'relative';
  value: number;
  currency: string;
  valid_from?: string | null;
  valid_to?: string | null;
  is_active: boolean;
  max_uses?: number | null;
}

export type DiscountUpdatePayload = Partial<DiscountCreatePayload> & { id: string };

interface DiscountFilters {
  activeOnly?: boolean;
  validNow?: boolean;
}

export const useDiscounts = (filters: DiscountFilters = {}) => {
  return useQuery({
    queryKey: ['discounts', filters],
    queryFn: async () => {
      const response = await api.get<DiscountListResponse>('/discounts', {
        params: {
          active_only: filters.activeOnly || undefined,
          valid_now: filters.validNow || undefined,
        },
      });
      return response.data.items;
    },
  });
};

export const useCreateDiscount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: DiscountCreatePayload) => {
      const response = await api.post<Discount>('/discounts', payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discounts'] });
    },
  });
};

export const useUpdateDiscount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...payload }: DiscountUpdatePayload) => {
      const response = await api.patch<Discount>(`/discounts/${id}`, payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discounts'] });
    },
  });
};

export const useDeactivateDiscount = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (discountId: string) => {
      const response = await api.post<Discount>(`/discounts/${discountId}/deactivate`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discounts'] });
    },
  });
};
