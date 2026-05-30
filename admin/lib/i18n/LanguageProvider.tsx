'use client';

import { I18nextProvider, useTranslation } from 'react-i18next';
import i18n from './i18n';
import { useCallback, useEffect, useMemo, useState } from 'react';

export const languages = [
  { code: 'ru', label: 'RU', name: 'Русский' },
  { code: 'en', label: 'EN', name: 'English' },
  { code: 'de', label: 'DE', name: 'Deutsch' },
] as const;

export type LanguageCode = (typeof languages)[number]['code'];

function normalizeLanguage(value: string | null): LanguageCode {
  return languages.some((language) => language.code === value)
    ? (value as LanguageCode)
    : 'ru';
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const savedLanguage = normalizeLanguage(localStorage.getItem('language'));
    i18n.changeLanguage(savedLanguage);
    document.documentElement.lang = savedLanguage;
    setReady(true);
  }, []);

  return (
    <I18nextProvider i18n={i18n}>
      <div suppressHydrationWarning>{ready ? children : children}</div>
    </I18nextProvider>
  );
}

export function useLanguage() {
  const { i18n: i18next } = useTranslation();
  const language = normalizeLanguage(i18next.language);

  const setLanguage = useCallback(async (lang: string) => {
    const nextLanguage = normalizeLanguage(lang);
    localStorage.setItem('language', nextLanguage);
    document.documentElement.lang = nextLanguage;
    await i18next.changeLanguage(nextLanguage);
  }, [i18next]);

  return useMemo(() => ({
    language,
    setLanguage,
    languages,
  }), [language, setLanguage]);
}
