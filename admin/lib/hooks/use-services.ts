'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, Service } from '@/lib/api';

// Demo data for admin panel
const DEMO_SERVICES: Service[] = [
  {
    id: 'svc-1',
    name: 'Интернет',
    description: 'Интернет-услуга',
    price: 300.0,
    currency: 'RUB',
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'svc-2',
    name: 'Телефония',
    description: 'Телефонные услуги',
    price: 200.0,
    currency: 'RUB',
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
  },
];

export const useServices = () => {
  return useQuery({
    queryKey: ['services'],
    queryFn: async () => {
      try {
        const response = await api.get<Service[]>('/services');
        return response.data;
      } catch (error) {
        // Return demo data if backend is unavailable
        console.warn('Backend unavailable, using demo data:', error);
        return DEMO_SERVICES;
      }
    },
  });
};

export const useService = (id: string) => {
  return useQuery({
    queryKey: ['services', id],
    queryFn: async () => {
      try {
        const response = await api.get<Service>(`/services/${id}`);
        return response.data;
      } catch (error) {
        // Return demo data if backend is unavailable
        const demo = DEMO_SERVICES.find(s => s.id === id);
        if (demo) return demo;
        throw error;
      }
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

export const useDeleteService = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/services/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services'] });
    },
  });
};