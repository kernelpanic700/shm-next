"use client";

import { useTariffs } from "@/lib/hooks/use-tariffs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/utils";
import { useI18n } from "@/lib/i18n";

export default function TariffsPage() {
  const { data: tariffs, isLoading } = useTariffs();
  const { locale, t } = useI18n();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">{t("tariffs")}</h1>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("availableTariffs")}</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <p>{t("loading")}</p>
            ) : tariffs?.length > 0 ? (
              <div className="space-y-4">
                {tariffs.map((tariff: any) => (
                  <div
                    key={tariff.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div>
                      <h3 className="font-medium">{tariff.name}</h3>
                      <p className="text-sm text-gray-600">
                        {tariff.speed} • {formatCurrency(tariff.price, locale)}/{t("monthly")}
                      </p>
                    </div>
                    <Button variant="outline" size="sm">
                      {t("connect")}
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600">{t("tariffsNotFound")}</p>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
