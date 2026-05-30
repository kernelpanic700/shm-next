'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, SpoolTask } from '@/lib/api';

interface SpoolTaskApiResponse {
  success: boolean;
  data: {
    items: SpoolTask[];
    total: number;
    page: number;
    per_page: number;
  };
  error: string | null;
  timestamp: string;
}

export const useSpoolTasks = () => {
  return useQuery({
    queryKey: ['spool-tasks'],
    queryFn: async (): Promise<SpoolTask[]> => {
      const response = await api.get<SpoolTaskApiResponse>('/spool');
      return response.data.data.items || [];
    },
    staleTime: 0,
    retry: 1,
  });
};

export const useRetryTask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (taskId: string) => {
      const response = await api.post(`/spool/${taskId}/retry`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['spool-tasks'] });
    },
  });
};

export const useCancelTask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (taskId: string) => {
      const response = await api.post(`/spool/${taskId}/cancel`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['spool-tasks'] });
    },
  });
};