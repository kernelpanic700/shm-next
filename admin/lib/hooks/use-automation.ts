'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  api,
  AutomationListResponse,
  CommandTemplate,
  EventActionRule,
  EventActionRuleListResponse,
  ManagedServer,
  ServerGroup,
  SSHKey,
} from '@/lib/api';

const AUTOMATION = '/automation';
const EVENT_RULES = '/event-action-rules';

export type SSHKeyForm = {
  name: string;
  private_key: string;
  public_key?: string;
  passphrase?: string;
  fingerprint?: string;
};

export type ServerGroupForm = {
  name: string;
  transport?: string;
  strategy?: string;
};

export type ServerForm = {
  group_id: string;
  name: string;
  host: string;
  port?: number;
  key_id?: string | null;
  default_cmd?: string;
};

export type CommandTemplateForm = {
  name: string;
  body: string;
  description?: string;
  transport?: string;
};

export type EventActionRuleForm = {
  title?: string;
  event_type: string;
  action_type: string;
  service_type?: string;
  server_group_id?: string | null;
  server_id?: string | null;
  template_id?: string | null;
  command?: string;
  priority?: number;
  max_retries?: number;
};

function useAutomationList<T>(key: string, path: string) {
  return useQuery({
    queryKey: ['automation', key],
    queryFn: async () => {
      const response = await api.get<AutomationListResponse<T>>(path);
      return response.data.items;
    },
  });
}

function invalidateAutomation(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ['automation'] });
  queryClient.invalidateQueries({ queryKey: ['event-action-rules'] });
}

export const useSSHKeys = () => useAutomationList<SSHKey>('ssh-keys', `${AUTOMATION}/ssh-keys`);
export const useServerGroups = () => useAutomationList<ServerGroup>('server-groups', `${AUTOMATION}/server-groups`);
export const useManagedServers = () => useAutomationList<ManagedServer>('servers', `${AUTOMATION}/servers`);
export const useCommandTemplates = () => useAutomationList<CommandTemplate>('templates', `${AUTOMATION}/templates`);

export const useEventActionRules = () => {
  return useQuery({
    queryKey: ['event-action-rules'],
    queryFn: async () => {
      const response = await api.get<EventActionRuleListResponse>(EVENT_RULES);
      return response.data.items;
    },
  });
};

export const useCreateSSHKey = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: SSHKeyForm) => (await api.post<SSHKey>(`${AUTOMATION}/ssh-keys`, data)).data,
    onSuccess: () => invalidateAutomation(queryClient),
  });
};

export const useCreateServerGroup = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ServerGroupForm) => (await api.post<ServerGroup>(`${AUTOMATION}/server-groups`, data)).data,
    onSuccess: () => invalidateAutomation(queryClient),
  });
};

export const useCreateManagedServer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ServerForm) => (await api.post<ManagedServer>(`${AUTOMATION}/servers`, { ...data, port: Number(data.port || 22) })).data,
    onSuccess: () => invalidateAutomation(queryClient),
  });
};

export const useCreateCommandTemplate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CommandTemplateForm) => (await api.post<CommandTemplate>(`${AUTOMATION}/templates`, { ...data, transport: data.transport || 'ssh' })).data,
    onSuccess: () => invalidateAutomation(queryClient),
  });
};

export const useCreateEventActionRule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: EventActionRuleForm) => (
      await api.post<EventActionRule>(EVENT_RULES, {
        ...data,
        action_type: data.action_type || 'ssh.exec',
        priority: Number(data.priority || 50),
        max_retries: Number(data.max_retries || 3),
        settings: {},
      })
    ).data,
    onSuccess: () => invalidateAutomation(queryClient),
  });
};

export const useDeleteAutomationItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ type, id }: { type: 'ssh-keys' | 'server-groups' | 'servers' | 'templates'; id: string }) => {
      await api.delete(`${AUTOMATION}/${type}/${id}`);
    },
    onSuccess: () => invalidateAutomation(queryClient),
  });
};

export const useDeleteEventActionRule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`${EVENT_RULES}/${id}`);
    },
    onSuccess: () => invalidateAutomation(queryClient),
  });
};
