"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAbonent } from "./use-abonent";

export interface UserService {
  id: string;
  abonent_id: string;
  service_type: string;
  status: string;
  cost: number;
  currency: string;
  quantity?: number;
  auto_bill?: boolean;
}

export function useServices(abonentId?: string) {
  return useQuery<UserService[]>({
    queryKey: ["services", abonentId],
    enabled: Boolean(abonentId),
    queryFn: async () => {
      const response = await api.get(`/services/${abonentId}/`);
      return response.data.items ?? [];
    },
  });
}

export function useMyServices() {
  const { data: abonent } = useAbonent();
  return useServices(abonent?.id);
}
