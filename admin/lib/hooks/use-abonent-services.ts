'use client';

import { useQuery } from '@tanstack/react-query';
import { api, Service } from '@/lib/api';

export const useAbonentServices = (abonentId?: string) => {
  return useQuery({
    queryKey: ['abonent-services', abonentId],
    queryFn: async () => {
      if (!abonentId) return [];
      const response = await api.get<Service[]>(`/abonents/${abonentId}/services`);
      return response.data;
    },
    enabled: !!abonentId,
  });
};