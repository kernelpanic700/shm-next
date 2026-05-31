"use client";

import { useMemo, useState } from "react";
import { usePayments } from "@/lib/hooks/use-payments";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatCurrency, formatDate } from "@/lib/utils";
import api from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useAbonent } from "@/lib/hooks/use-abonent";

type PaymentItem = {
  id: string;
  amount: number;
  status?: string;
  created_at?: string;
  date?: string;
  payment_method?: string;
};

function paymentStatusClass(status?: string) {
  const normalized = status?.toLowerCase();

  if (normalized === "completed" || normalized === "paid") {
    return "bg-emerald-50 text-emerald-700";
  }

  if (normalized === "failed" || normalized === "cancelled") {
    return "bg-rose-50 text-rose-700";
  }

  return "bg-amber-50 text-amber-700";
}

export default function PaymentsPage() {
  const { data: abonent } = useAbonent();
  const { data: payments, isLoading, refetch } = usePayments(abonent?.id);
  const { locale, t } = useI18n();
  const paymentItems = useMemo(() => (payments ?? []) as PaymentItem[], [payments]);
  const [amount, setAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const totalPaid = useMemo(
    () => paymentItems.reduce((sum, payment) => sum + Number(payment.amount ?? 0), 0),
    [paymentItems]
  );

  const handlePayment = async () => {
    const value = Number.parseFloat(amount);

    if (!value || value <= 0 || !abonent?.id) {
      return;
    }

    setSubmitting(true);
    try {
      await api.post("/payments", {
        abonent_id: abonent.id,
        amount: value,
        currency: abonent.currency ?? "RUB",
        payment_method: "online",
      });
      setAmount("");
      refetch();
    } catch (error) {
      console.error("Payment error:", error);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.08em] text-slate-500">{t("operations")}</p>
          <h1 className="text-2xl font-semibold text-slate-950">{t("payments")}</h1>
        </div>
        <div className="rounded-md border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600">
          {t("totalPaid")}: <span className="font-semibold text-slate-950">{formatCurrency(totalPaid, locale)}</span>
        </div>
      </div>

      <section className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>{t("topUpBalance")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="payment-amount">
                {t("amount")}
              </label>
              <Input
                id="payment-amount"
                min="1"
                step="1"
                type="number"
                placeholder="1000"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
              />
            </div>
            <Button className="w-full" onClick={handlePayment} disabled={submitting || !abonent?.id}>
              {submitting ? t("submitting") : t("submitPayment")}
            </Button>
            <p className="text-xs leading-5 text-slate-500">{t("paymentNotice")}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("paymentHistory")}</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {[0, 1, 2].map((item) => (
                  <div key={item} className="h-14 rounded-md bg-slate-100" />
                ))}
              </div>
            ) : paymentItems.length > 0 ? (
              <div className="overflow-hidden rounded-md border border-slate-200">
                <div className="grid grid-cols-[1fr_auto_auto] gap-3 bg-slate-50 px-4 py-2 text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
                  <span>{t("amount")}</span>
                  <span>{t("paymentMethod")}</span>
                  <span>{t("status")}</span>
                </div>
                {paymentItems.map((payment) => (
                  <div
                    key={payment.id}
                    className="grid grid-cols-[1fr_auto_auto] items-center gap-3 border-t border-slate-200 px-4 py-3 text-sm"
                  >
                    <div>
                      <p className="font-semibold text-slate-950">{formatCurrency(payment.amount, locale)}</p>
                      <p className="text-xs text-slate-500">
                        {formatDate(payment.created_at ?? payment.date ?? new Date().toISOString(), locale)}
                      </p>
                    </div>
                    <span className="text-slate-600">{payment.payment_method ?? "online"}</span>
                    <span className={`rounded-md px-2 py-1 text-xs font-medium ${paymentStatusClass(payment.status)}`}>
                      {payment.status === "completed" ? t("paid") : payment.status ?? t("paymentsProcessing")}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="rounded-md border border-dashed border-slate-300 px-4 py-10 text-center text-sm text-slate-500">
                {t("noPayments")}
              </p>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
