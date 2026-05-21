'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface DashboardStats {
  total_abonents: number;
  active_abonents: number;
  total_balance: number;
  pending_payments: number;
  spool_tasks: number;
}

export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get<DashboardStats>('/dashboard/stats');
      return response.data;
    },
    staleTime: 60 * 1000, // 1 minute
  });
};