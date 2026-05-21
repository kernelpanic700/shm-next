'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, Service } from '@/lib/api';

export const useServices = () => {
  return useQuery({
    queryKey: ['services'],
    queryFn: async () => {
      const response = await api.get<Service[]>('/services');
      return response.data;
    },
  });
};

export const useService = (id: string) => {
  return useQuery({
    queryKey: ['services', id],
    queryFn: async () => {
      const response = await api.get<Service>(`/services/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCreateService = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: Omit<Service, 'id' | 'created_at'>) => {
      const response = await api.post<Service>('/services', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services'] });
    },
  });
};

export const useUpdateService = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, ...data }: { id: string } & Partial<Service>) => {
      const response = await api.patch<Service>(`/services/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services'] });
    },
  });
};