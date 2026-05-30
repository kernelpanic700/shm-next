"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";

export interface CurrentAbonent {
  id: string;
  phone: string;
  full_name: string;
  email?: string | null;
  account_number?: string;
  balance?: number;
  currency?: string;
  status?: string;
  role?: string;
}

export function useAbonent() {
  return useQuery<CurrentAbonent>({
    queryKey: ["abonent"],
    queryFn: async () => {
      const response = await api.get("/auth/me");
      return response.data;
    },
  });
}

export function useBalance(abonentId?: string) {
  return useQuery({
    queryKey: ["balance", abonentId],
    enabled: Boolean(abonentId),
    queryFn: async () => {
      const response = await api.get(`/billing/${abonentId}/balance`);
      return response.data;
    },
  });
}
