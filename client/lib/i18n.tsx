"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

export const languages = [
  { code: "ru", label: "RU", name: "Русский", locale: "ru-RU" },
  { code: "en", label: "EN", name: "English", locale: "en-US" },
] as const;

export type LanguageCode = (typeof languages)[number]["code"];

const dictionaries = {
  ru: {
    active: "Активна",
    amount: "Сумма",
    availableTariffs: "Доступные тарифы",
    balance: "Баланс",
    changeTariff: "Сменить тариф",
    confirmPassword: "Повторите пароль",
    connect: "Подключить",
    connectedServices: "Подключённые услуги",
    dashboard: "Главная",
    dashboardWelcome: "Добро пожаловать в личный кабинет!",
    disconnect: "Отключить",
    disabled: "Отключена",
    email: "Email",
    emailOptional: "Email (необязательно)",
    enterRequired: "Пожалуйста, войдите в систему",
    fullName: "ФИО",
    fullNamePlaceholder: "Иванов Иван Иванович",
    lastPayments: "Последние платежи",
    loading: "Загрузка...",
    loadingData: "Подождите, данные загружаются...",
    login: "Войти",
    loginError: "Ошибка входа",
    loginProgress: "Вход...",
    logout: "Выйти",
    manageServices: "Управление услугами",
    monthly: "мес",
    myServices: "Мои услуги",
    noAccount: "Нет аккаунта?",
    noEmail: "Не указан",
    noPayments: "Платежей пока нет",
    noPaymentsFound: "Платежей не найдено",
    noServices: "Нет подключённых услуг",
    noServicesFound: "Услуги не найдены",
    noTariff: "Тариф не назначен",
    paid: "Оплачено",
    password: "Пароль",
    passwordsMismatch: "Пароли не совпадают",
    paymentHistory: "История платежей",
    payments: "Платежи",
    paymentsProcessing: "В обработке",
    phone: "Телефон",
    profile: "Профиль",
    personalAccount: "Личный кабинет",
    personalData: "Личные данные",
    redirected: "Вы будете перенаправлены на страницу входа...",
    register: "Зарегистрироваться",
    registerError: "Ошибка регистрации",
    registerProgress: "Регистрация...",
    registration: "Регистрация",
    registrationDisabled: "Регистрация отключена",
    registrationDisabledDescription: "Создание новых аккаунтов временно закрыто. Обратитесь к администратору или войдите в существующий аккаунт.",
    role: "Роль",
    services: "Услуги",
    signedInAs: "Вы успешно вошли в систему как {{phone}}",
    status: "Статус",
    submitPayment: "Пополнить",
    submitting: "Обработка...",
    subscriber: "Абонент",
    tariffs: "Тарифы",
    tariffsNotFound: "Тарифы не найдены",
    topUpBalance: "Пополнение баланса",
    alreadyHaveAccount: "Уже есть аккаунт?",
    secureWorkspace: "Защищенное рабочее пространство",
    subscriberPortal: "Кабинет абонента",
    accountNumber: "Лицевой счет",
    currentPlan: "Текущий план",
    activeServices: "Активные услуги",
    recentPayment: "Последний платеж",
    serviceStatus: "Состояние услуг",
    operations: "Операции",
    open: "Открыть",
    yourTariff: "Ваш тариф",
    yourServices: "Ваши услуги",
    monthlyTotal: "Сумма в месяц",
    paymentMethod: "Способ оплаты",
    paymentNotice: "Платеж будет создан в биллинге и пройдет через стандартный сценарий обработки.",
    totalPaid: "Всего платежей",
  },
  en: {
    active: "Active",
    amount: "Amount",
    availableTariffs: "Available tariffs",
    balance: "Balance",
    changeTariff: "Change tariff",
    confirmPassword: "Confirm password",
    connect: "Connect",
    connectedServices: "Connected services",
    dashboard: "Home",
    dashboardWelcome: "Welcome to your account!",
    disconnect: "Disconnect",
    disabled: "Disabled",
    email: "Email",
    emailOptional: "Email (optional)",
    enterRequired: "Please sign in",
    fullName: "Full name",
    fullNamePlaceholder: "John Smith",
    lastPayments: "Recent payments",
    loading: "Loading...",
    loadingData: "Please wait while the data is loading...",
    login: "Sign in",
    loginError: "Login failed",
    loginProgress: "Signing in...",
    logout: "Log out",
    manageServices: "Manage services",
    monthly: "mo",
    myServices: "My services",
    noAccount: "No account?",
    noEmail: "Not specified",
    noPayments: "No payments yet",
    noPaymentsFound: "No payments found",
    noServices: "No connected services",
    noServicesFound: "No services found",
    noTariff: "No tariff assigned",
    paid: "Paid",
    password: "Password",
    passwordsMismatch: "Passwords do not match",
    paymentHistory: "Payment history",
    payments: "Payments",
    paymentsProcessing: "Processing",
    phone: "Phone",
    profile: "Profile",
    personalAccount: "Personal account",
    personalData: "Personal data",
    redirected: "You will be redirected to the sign-in page...",
    register: "Create account",
    registerError: "Registration failed",
    registerProgress: "Creating account...",
    registration: "Registration",
    registrationDisabled: "Registration disabled",
    registrationDisabledDescription: "New account creation is currently closed. Contact an administrator or sign in with an existing account.",
    role: "Role",
    services: "Services",
    signedInAs: "You are signed in as {{phone}}",
    status: "Status",
    submitPayment: "Top up",
    submitting: "Processing...",
    subscriber: "Subscriber",
    tariffs: "Tariffs",
    tariffsNotFound: "No tariffs found",
    topUpBalance: "Top up balance",
    alreadyHaveAccount: "Already have an account?",
    secureWorkspace: "Secure workspace",
    subscriberPortal: "Subscriber portal",
    accountNumber: "Account number",
    currentPlan: "Current plan",
    activeServices: "Active services",
    recentPayment: "Recent payment",
    serviceStatus: "Service status",
    operations: "Operations",
    open: "Open",
    yourTariff: "Your tariff",
    yourServices: "Your services",
    monthlyTotal: "Monthly total",
    paymentMethod: "Payment method",
    paymentNotice: "The payment will be created in billing and processed through the standard flow.",
    totalPaid: "Total payments",
  },
} as const;

type Dictionary = typeof dictionaries.ru;
type TranslationKey = keyof Dictionary;

type LanguageContextValue = {
  language: LanguageCode;
  locale: string;
  setLanguage: (language: LanguageCode | string) => void;
  t: (key: TranslationKey, params?: Record<string, string | number | undefined>) => string;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

function normalizeLanguage(value: string | null): LanguageCode {
  return languages.some((language) => language.code === value) ? (value as LanguageCode) : "ru";
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<LanguageCode>("ru");

  useEffect(() => {
    const savedLanguage = normalizeLanguage(localStorage.getItem("language"));
    setLanguageState(savedLanguage);
    document.documentElement.lang = savedLanguage;
  }, []);

  const setLanguage = (value: LanguageCode | string) => {
    const nextLanguage = normalizeLanguage(value);
    localStorage.setItem("language", nextLanguage);
    document.documentElement.lang = nextLanguage;
    setLanguageState(nextLanguage);
  };

  const currentLanguage = languages.find((item) => item.code === language) ?? languages[0];
  const dictionary = dictionaries[language];

  const value = useMemo<LanguageContextValue>(() => ({
    language,
    locale: currentLanguage.locale,
    setLanguage,
    t: (key, params) => {
      let text: string = dictionary[key] ?? key;
      Object.entries(params ?? {}).forEach(([name, replacement]) => {
        text = text.replace(`{{${name}}}`, String(replacement ?? ""));
      });
      return text;
    },
  }), [language, currentLanguage.locale, dictionary]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useI18n() {
  const context = useContext(LanguageContext);

  if (!context) {
    throw new Error("useI18n must be used within LanguageProvider");
  }

  return context;
}
