import { useQuery } from '@tanstack/react-query';
import { api, Tariff } from '@/lib/api';

export const useTariffs = () => {
  return useQuery<Tariff[]>({
    queryKey: ['tariffs'],
    queryFn: async () => {
      const response = await api.get('/tariffs');
      return response.data.items || response.data;
    },
  });
};