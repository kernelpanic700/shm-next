"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAbonent } from "./use-abonent";

interface PaymentListResponse {
  items: any[];
  total: number;
  page: number;
  per_page: number;
}

export function usePayments(abonentId?: string) {
  return useQuery({
    queryKey: ["payments", abonentId],
    enabled: Boolean(abonentId),
    queryFn: async () => {
      const response = await api.get<PaymentListResponse>("/payments", {
        params: { abonent_id: abonentId },
      });
      return response.data.items;
    },
  });
}

export function useRecentPayments(limit = 5) {
  const { data: abonent } = useAbonent();
  return useQuery({
    queryKey: ["payments", "recent", abonent?.id, limit],
    enabled: Boolean(abonent?.id),
    queryFn: async () => {
      const response = await api.get<PaymentListResponse>("/payments", {
        params: { abonent_id: abonent?.id, per_page: limit },
      });
      return response.data.items;
    },
  });
}
