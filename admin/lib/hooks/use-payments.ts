'use client';

import { useQuery } from '@tanstack/react-query';
import { api, Payment } from '@/lib/api';

interface PaymentListResponse {
  items: Payment[];
  total: number;
  page: number;
  per_page: number;
}

export const usePayments = (abonentId?: string) => {
  return useQuery({
    queryKey: ['payments', abonentId],
    queryFn: async () => {
      const params = abonentId ? { abonent_id: abonentId } : {};
      const response = await api.get<PaymentListResponse>('/payments', { params });
      return response.data.items;
    },
    enabled: true,
  });
};