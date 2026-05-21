'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, SpoolTask } from '@/lib/api';

export const useSpoolTasks = () => {
  return useQuery({
    queryKey: ['spool-tasks'],
    queryFn: async () => {
      const response = await api.get<SpoolTask[]>('/spool');
      return response.data;
    },
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