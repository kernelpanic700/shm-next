"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";

export function useTariffs() {
  return useQuery({
    queryKey: ["tariffs"],
    queryFn: async () => {
      const response = await api.get("/tariffs");
      return response.data;
    },
  });
}