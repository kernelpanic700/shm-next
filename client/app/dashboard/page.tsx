"use client";

import { useAuth } from "@/components/auth-provider";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency, formatDate } from "@/lib/utils";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import api from "@/lib/api";
import { useAbonent } from "@/lib/hooks/use-abonent";

interface Tariff {
  id: string;
  name: string;
  price: number;
  currency: string;
  description: string;
}

interface Service {
  id: string;
  name?: string;
  service_type?: string;
  status: string;
  price?: number;
  cost?: number;
}

interface Payment {
  id: string;
  amount: number;
  date?: string;
  created_at?: string;
  status: string;
}

interface DashboardData {
  balance: number;
  tariff: Tariff;
  services: Service[];
  payments: Payment[];
}

export default function DashboardPage() {
  const { isAuthenticated, user } = useAuth();
  const { data: abonent } = useAbonent();
  const { locale, t } = useI18n();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || !abonent?.id) return;

    const fetchData = async () => {
      try {
        const [balanceRes, tariffRes, servicesRes, paymentRes] = await Promise.allSettled([
          api.get(`/billing/${abonent.id}/balance`),
          api.get(`/billing/${abonent.id}/tariff`),
          api.get(`/services/${abonent.id}/`),
          api.get(`/billing/${abonent.id}/last-payment`),
        ]);

        const balanceData = balanceRes.status === "fulfilled" ? balanceRes.value.data : {};
        const tariffData = tariffRes.status === "fulfilled" ? tariffRes.value.data : null;
        const servicesData = servicesRes.status === "fulfilled" ? servicesRes.value.data : { items: [] };
        const paymentData = paymentRes.status === "fulfilled" ? paymentRes.value.data : null;

        setData({
          balance: balanceData.balance ?? abonent.balance ?? 0,
          tariff: tariffData,
          services: servicesData.items || [],
          payments: paymentData ? [paymentData.payment ?? paymentData] : [],
        });
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [abonent, isAuthenticated]);

  const activeServices = data?.services.filter((service) => service.status === "ACTIVE").length ?? 0;
  const lastPayment = data?.payments[0];
  const accountNumber = abonent?.account_number ?? "-";

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">{t("enterRequired")}</h1>
          <p className="text-slate-600">{t("redirected")}</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="text-center">
          <h1 className="mb-4 text-2xl font-bold">{t("loading")}</h1>
          <p className="text-slate-600">{t("loadingData")}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-col gap-3 border-b border-slate-200 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">
              {t("dashboardWelcome")}
            </h1>
            <p className="mt-1 text-sm text-slate-600">{t("signedInAs", { phone: user?.phone })}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              href="/payments"
              className="inline-flex h-10 items-center justify-center rounded-md border border-slate-300 bg-white px-4 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              {t("submitPayment")}
            </Link>
            <Link
              href="/services"
              className="inline-flex h-10 items-center justify-center rounded-md border border-slate-300 bg-white px-4 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              {t("manageServices")}
            </Link>
          </div>
        </div>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card>
            <CardHeader className="px-4 py-3">
              <CardTitle className="text-sm text-slate-500">{t("balance")}</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 pt-0">
              <p className="text-2xl font-semibold text-slate-950">
                {formatCurrency(data?.balance || 0, locale)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="px-4 py-3">
              <CardTitle className="text-sm text-slate-500">{t("accountNumber")}</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 pt-0">
              <p className="truncate text-2xl font-semibold text-slate-950">{accountNumber}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="px-4 py-3">
              <CardTitle className="text-sm text-slate-500">{t("activeServices")}</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 pt-0">
              <p className="text-2xl font-semibold text-slate-950">{activeServices}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="px-4 py-3">
              <CardTitle className="text-sm text-slate-500">{t("currentPlan")}</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4 pt-0">
              <p className="truncate text-2xl font-semibold text-slate-950">{data?.tariff?.name ?? t("noTariff")}</p>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{t("yourServices")}</CardTitle>
              <Link className="text-sm font-medium text-slate-600 hover:text-slate-950" href="/services">
                {t("open")}
              </Link>
            </CardHeader>
            <CardContent>
              {data?.services.length ? (
                <div className="overflow-hidden rounded-md border border-slate-200">
                  <div className="grid grid-cols-[1fr_auto_auto] gap-3 bg-slate-50 px-4 py-2 text-xs font-medium text-slate-500">
                    <span>{t("services")}</span>
                    <span>{t("status")}</span>
                    <span>{t("amount")}</span>
                  </div>
                  {data.services.slice(0, 6).map((service) => (
                    <div
                      key={service.id}
                      className="grid grid-cols-[1fr_auto_auto] items-center gap-3 border-t border-slate-200 px-4 py-3 text-sm"
                    >
                      <div>
                        <p className="font-medium text-slate-950">{service.name ?? service.service_type}</p>
                        <p className="text-xs text-slate-500">{service.id}</p>
                      </div>
                      <span className="rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">
                        {service.status}
                      </span>
                      <span className="font-medium text-slate-950">
                        {formatCurrency(service.price ?? service.cost ?? 0, locale)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="rounded-md border border-dashed border-slate-300 px-4 py-8 text-center text-sm text-slate-500">
                  {t("noServicesFound")}
                </p>
              )}
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>{t("yourTariff")}</CardTitle>
              </CardHeader>
              <CardContent>
                {data?.tariff ? (
                  <div className="space-y-2">
                    <p className="text-lg font-semibold text-slate-950">{data.tariff.name}</p>
                    <p className="text-sm text-slate-600">
                      {formatCurrency(data.tariff.price, locale)}/{t("monthly")}
                    </p>
                    <p className="text-sm text-slate-500">{data.tariff.description}</p>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">{t("noTariff")}</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>{t("recentPayment")}</CardTitle>
                <Link className="text-sm font-medium text-slate-600 hover:text-slate-950" href="/payments">
                  {t("open")}
                </Link>
              </CardHeader>
              <CardContent>
                {lastPayment ? (
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-lg font-semibold text-slate-950">
                        {formatCurrency(lastPayment.amount, locale)}
                      </p>
                      <p className="text-sm text-slate-500">
                        {formatDate(lastPayment.created_at ?? lastPayment.date ?? new Date().toISOString(), locale)}
                      </p>
                    </div>
                    <span className="rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700">
                      {lastPayment.status}
                    </span>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">{t("noPaymentsFound")}</p>
                )}
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </div>
  );
}
