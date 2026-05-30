'use client';

import { Globe2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { languages, useLanguage } from '@/lib/i18n/LanguageProvider';

export function LanguageSwitcher() {
  const { t } = useTranslation();
  const { language, setLanguage } = useLanguage();

  return (
    <label className="flex items-center gap-2 text-sm text-muted-foreground">
      <Globe2 className="h-4 w-4" aria-hidden="true" />
      <span className="sr-only">{t('Language')}</span>
      <select
        aria-label={t('Language')}
        value={language}
        onChange={(event) => setLanguage(event.target.value)}
        className="h-9 rounded-md border border-input bg-background px-2 text-sm text-foreground shadow-sm outline-none transition-colors focus:ring-2 focus:ring-ring"
      >
        {languages.map((item) => (
          <option key={item.code} value={item.code}>
            {item.label}
          </option>
        ))}
      </select>
    </label>
  );
}
