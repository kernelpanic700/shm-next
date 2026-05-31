"use client";

import { useMemo } from "react";
import { useMyServices } from "@/lib/hooks/use-services";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/utils";
import { useI18n } from "@/lib/i18n";

type ServiceItem = {
  id: string;
  name?: string;
  service_type?: string;
  description?: string;
  price?: number;
  cost?: number;
  status?: string;
  is_active?: boolean;
};

function isServiceActive(service: ServiceItem) {
  const status = service.status?.toLowerCase();
  return service.is_active ?? status === "active";
}

export default function ServicesPage() {
  const { data: services, isLoading } = useMyServices();
  const { locale, t } = useI18n();
  const items = useMemo(() => (services ?? []) as ServiceItem[], [services]);

  const activeCount = useMemo(() => items.filter(isServiceActive).length, [items]);
  const monthlyTotal = useMemo(
    () => items.reduce((sum, service) => sum + Number(service.price ?? service.cost ?? 0), 0),
    [items]
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.08em] text-slate-500">{t("serviceStatus")}</p>
          <h1 className="text-2xl font-semibold text-slate-950">{t("myServices")}</h1>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:w-auto">
          <div className="rounded-md border border-slate-200 bg-white px-4 py-2">
            <p className="text-xs text-slate-500">{t("activeServices")}</p>
            <p className="text-lg font-semibold text-slate-950">{activeCount}</p>
          </div>
          <div className="rounded-md border border-slate-200 bg-white px-4 py-2">
            <p className="text-xs text-slate-500">{t("monthlyTotal")}</p>
            <p className="text-lg font-semibold text-slate-950">{formatCurrency(monthlyTotal, locale)}</p>
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("connectedServices")}</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid gap-3 md:grid-cols-2">
              {[0, 1, 2, 3].map((item) => (
                <div key={item} className="h-28 rounded-md bg-slate-100" />
              ))}
            </div>
          ) : items.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2">
              {items.map((service) => {
                const active = isServiceActive(service);

                return (
                  <article key={service.id} className="rounded-md border border-slate-200 bg-white p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-slate-950">{service.name ?? service.service_type}</h3>
                        <p className="mt-1 text-sm text-slate-500">
                          {service.description ?? service.service_type ?? service.id}
                        </p>
                      </div>
                      <span
                        className={`rounded-md px-2 py-1 text-xs font-medium ${
                          active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {active ? t("active") : t("disabled")}
                      </span>
                    </div>
                    <div className="mt-5 flex items-center justify-between gap-3 border-t border-slate-200 pt-4">
                      <span className="font-semibold text-slate-950">
                        {formatCurrency(service.price ?? service.cost ?? 0, locale)}/{t("monthly")}
                      </span>
                      <Button variant="outline" size="sm">
                        {active ? t("disconnect") : t("connect")}
                      </Button>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <p className="rounded-md border border-dashed border-slate-300 px-4 py-10 text-center text-sm text-slate-500">
              {t("noServices")}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
