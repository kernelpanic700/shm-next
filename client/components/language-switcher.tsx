"use client";

import { languages, useI18n } from "@/lib/i18n";

export function LanguageSwitcher() {
  const { language, setLanguage } = useI18n();

  return (
    <label className="inline-flex items-center gap-2 text-sm text-gray-600">
      <span className="sr-only">Language</span>
      <select
        value={language}
        onChange={(event) => setLanguage(event.target.value)}
        className="h-9 rounded-md border border-gray-200 bg-white px-2 text-sm font-medium text-gray-900 shadow-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
        aria-label="Language"
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
