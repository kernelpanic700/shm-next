'use client';

import { useQuery } from '@tanstack/react-query';
import { api, Payment } from '@/lib/api';

export const usePayments = (abonentId?: string) => {
  return useQuery({
    queryKey: ['payments', abonentId],
    queryFn: async () => {
      if (abonentId) {
        const response = await api.get<Payment[]>(`/abonents/${abonentId}/payments`);
        return response.data;
      }
      const response = await api.get<Payment[]>('/payments');
      return response.data;
    },
    enabled: abonentId ? !!abonentId : true,
  });
};