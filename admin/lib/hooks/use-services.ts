'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, Service, ServiceListResponse } from '@/lib/api';

type ServiceFormData = {
  name: string;
  description?: string | null;
  cost?: number;
  price?: number;
  currency?: string;
  period_cost?: string;
  category?: string | null;
  allow_to_order?: boolean;
  pay_always?: boolean;
  no_discount?: boolean;
  pay_in_credit?: boolean;
  is_composite?: boolean;
};

const SERVICE_ENDPOINT = '/catalog-services';

function normalizeServicePayload(data: ServiceFormData) {
  return {
    name: data.name,
    description: data.description || null,
    cost: Number(data.cost ?? data.price ?? 0),
    currency: data.currency || 'RUB',
    period_cost: data.period_cost || '1.0000',
    category: data.category || null,
    allow_to_order: data.allow_to_order ?? true,
    pay_always: data.pay_always ?? false,
    no_discount: data.no_discount ?? false,
    pay_in_credit: data.pay_in_credit ?? false,
    is_composite: data.is_composite ?? false,
  };
}

export const useServices = () => {
  return useQuery({
    queryKey: ['services'],
    queryFn: async () => {
      const response = await api.get<ServiceListResponse>(SERVICE_ENDPOINT);
      return response.data.items;
    },
  });
};

export const useService = (id: string) => {
  return useQuery({
    queryKey: ['services', id],
    queryFn: async () => {
      const response = await api.get<Service>(`${SERVICE_ENDPOINT}/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCreateService = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ServiceFormData) => {
      const response = await api.post<Service>(SERVICE_ENDPOINT, normalizeServicePayload(data));
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
    mutationFn: async ({ id, ...data }: { id: string } & Partial<ServiceFormData>) => {
      const response = await api.patch<Service>(`${SERVICE_ENDPOINT}/${id}`, normalizeServicePayload(data as ServiceFormData));
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
      await api.delete(`${SERVICE_ENDPOINT}/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services'] });
    },
  });
};
