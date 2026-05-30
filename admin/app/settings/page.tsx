'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Settings, Save, Bell, Shield, Database } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';
import { languages, useLanguage } from '@/lib/i18n/LanguageProvider';

export default function SettingsPage() {
  const { t } = useTranslation();
  const { language, setLanguage } = useLanguage();
  const [settings, setSettings] = useState({
    notifications_enabled: true,
    two_factor_auth: false,
    demo_mode: true,
    theme: 'system',
  });
  const [saving, setSaving] = useState(false);

  const handleLanguageChange = (value: string) => {
    setLanguage(value);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Demo mode: simulate save
      await new Promise(resolve => setTimeout(resolve, 500));
      toast.success(t('SettingsSaved'));
    } catch (error) {
      toast.error(t('ErrorSaving'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">{t('Settings')}</h2>
      </div>

      <div className="grid gap-6">
        {/* General Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              {t('GeneralSettings')}
            </CardTitle>
            <CardDescription>{t('GeneralSettingsDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4">
              <div className="space-y-2">
                <label htmlFor="language" className="text-sm font-medium">{t('Language')}</label>
                <select
                  id="language"
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={language}
                  onChange={(e) => handleLanguageChange(e.target.value)}
                >
                  {languages.map((item) => (
                    <option key={item.code} value={item.code}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="demo_mode"
                  checked={settings.demo_mode}
                  onCheckedChange={(checked) => setSettings({ ...settings, demo_mode: checked === true })}
                />
                <label htmlFor="demo_mode" className="text-sm">{t('DemoMode')}</label>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              {t('Notifications')}
            </CardTitle>
            <CardDescription>{t('NotificationsDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="notifications_enabled"
                checked={settings.notifications_enabled}
                onCheckedChange={(checked) => setSettings({ ...settings, notifications_enabled: checked === true })}
              />
              <label htmlFor="notifications_enabled" className="text-sm">{t('EnableNotifications')}</label>
            </div>
          </CardContent>
        </Card>

        {/* Security */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              {t('Security')}
            </CardTitle>
            <CardDescription>{t('SecurityDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="two_factor_auth"
                checked={settings.two_factor_auth}
                onCheckedChange={(checked) => setSettings({ ...settings, two_factor_auth: checked === true })}
              />
              <label htmlFor="two_factor_auth" className="text-sm">{t('TwoFactorAuth')}</label>
            </div>
          </CardContent>
        </Card>

        {/* System Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              {t('SystemStatus')}
            </CardTitle>
            <CardDescription>{t('SystemStatusDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">{t('ApiStatus')}</label>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-600">{t('SystemWorking')}</span>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">{t('WorkMode')}</label>
                <span className="text-sm text-gray-600">
                  {settings.demo_mode ? t('Demo') : t('Production')}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Button onClick={handleSave} disabled={saving} className="w-fit">
          {saving ? t('Saving') : t('Save')}
        </Button>
      </div>
    </div>
  );
}
