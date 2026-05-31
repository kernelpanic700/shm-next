"use client";

import { useAbonent } from "@/lib/hooks/use-abonent";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/auth-provider";
import { useI18n } from "@/lib/i18n";

function Field({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">{label}</p>
      <p className="mt-1 break-words font-semibold text-slate-950">{value || "-"}</p>
    </div>
  );
}

export default function ProfilePage() {
  const { data: abonent, isLoading } = useAbonent();
  const { logout } = useAuth();
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.08em] text-slate-500">{t("personalAccount")}</p>
          <h1 className="text-2xl font-semibold text-slate-950">{t("profile")}</h1>
        </div>
        <Button variant="outline" onClick={logout}>
          {t("logout")}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("personalData")}</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid gap-3 md:grid-cols-2">
              {[0, 1, 2, 3].map((item) => (
                <div key={item} className="h-20 rounded-md bg-slate-100" />
              ))}
            </div>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              <Field label={t("fullName")} value={abonent?.full_name} />
              <Field label={t("phone")} value={abonent?.phone} />
              <Field label={t("email")} value={abonent?.email || t("noEmail")} />
              <Field label="Login" value={abonent?.login} />
              <Field label="Contract" value={abonent?.contract ?? abonent?.account_number} />
              <Field label={t("status")} value={abonent?.status} />
              <Field label={t("accountNumber")} value={abonent?.account_number ?? abonent?.id} />
              <Field label="Discount" value={abonent?.discount} />
              <Field label="Credit" value={abonent?.credit} />
              <Field label="Bonus" value={abonent?.bonus} />
              <Field label="Verified" value={abonent?.verified ? "yes" : "no"} />
              <Field label={t("role")} value={abonent?.role ?? t("subscriber")} />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
