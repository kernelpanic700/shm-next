'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, Invoice, InvoiceListResponse } from '@/lib/api';

interface ApiEnvelope<T> {
  success: boolean;
  data: T;
}

export interface InvoiceFilters {
  abonentId?: string;
  status?: string;
  fromDate?: string;
  toDate?: string;
  page?: number;
  perPage?: number;
}

const invoiceQueryKeys = {
  all: ['invoices'] as const,
  list: (filters: InvoiceFilters) => ['invoices', filters] as const,
};

export const useInvoices = (filters: InvoiceFilters = {}) => {
  return useQuery({
    queryKey: invoiceQueryKeys.list(filters),
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<InvoiceListResponse>>('/invoices', {
        params: {
          abonent_id: filters.abonentId || undefined,
          status: filters.status || undefined,
          from_date: filters.fromDate || undefined,
          to_date: filters.toDate || undefined,
          page: filters.page || 1,
          per_page: filters.perPage || 50,
        },
      });
      return response.data.data;
    },
  });
};

export const useInvoiceAction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ invoiceId, action }: { invoiceId: string; action: 'issue' | 'send' | 'overdue' | 'cancel' }) => {
      const response = await api.post<Invoice>(`/invoices/${invoiceId}/${action}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceQueryKeys.all });
    },
  });
};

export const usePayInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ invoiceId, paymentMethod = 'manual' }: { invoiceId: string; paymentMethod?: string }) => {
      const response = await api.post<ApiEnvelope<{ paid: boolean; payment_id: string }>>(
        `/invoices/${invoiceId}/pay`,
        null,
        { params: { payment_method: paymentMethod } }
      );
      return response.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: invoiceQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: ['payments'] });
      queryClient.invalidateQueries({ queryKey: ['abonents'] });
    },
  });
};
