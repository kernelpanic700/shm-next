'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, Abonent } from '@/lib/api';

export const useAbonents = () => {
  return useQuery({
    queryKey: ['abonents'],
    queryFn: async () => {
      const response = await api.get<Abonent[]>('/abonents');
      return response.data;
    },
  });
};

export const useAbonent = (id: string) => {
  return useQuery({
    queryKey: ['abonents', id],
    queryFn: async () => {
      const response = await api.get<Abonent>(`/abonents/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCreateAbonent = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (abonent: Partial<Abonent>) => {
      const response = await api.post<Abonent>('/abonents', abonent);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['abonents'] });
    },
  });
};

export const useUpdateAbonent = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, ...abonent }: Partial<Abonent> & { id: string }) => {
      const response = await api.patch<Abonent>(`/abonents/${id}`, abonent);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['abonents'] });
    },
  });
};

export const useDeleteAbonent = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/abonents/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['abonents'] });
    },
  });
};