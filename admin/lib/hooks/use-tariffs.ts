import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, Tariff } from '@/lib/api';

export const useTariffs = () => {
  return useQuery<Tariff[]>({
    queryKey: ['tariffs'],
    queryFn: async () => {
      const response = await api.get('/tariffs');
      const items: Tariff[] = response.data.items || response.data;
      return items.map((tariff) => ({
        ...tariff,
        billing_cycle: tariff.billing_cycle || tariff.billing_period,
      }));
    },
  });
};

export const useDeleteTariff = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/tariffs/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tariffs'] });
    },
  });
};
