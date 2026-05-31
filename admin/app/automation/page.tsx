'use client';

import { FormEvent, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { KeyRound, Plus, Server, TerminalSquare, Trash2, Workflow } from 'lucide-react';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';
import {
  useCommandTemplates,
  useCreateCommandTemplate,
  useCreateEventActionRule,
  useCreateManagedServer,
  useCreateServerGroup,
  useCreateSSHKey,
  useDeleteAutomationItem,
  useDeleteEventActionRule,
  useEventActionRules,
  useManagedServers,
  useServerGroups,
  useSSHKeys,
} from '@/lib/hooks/use-automation';

const events = [
  'service.activated',
  'service.deactivated',
  'service.renewed',
  'abonent.created',
  'abonent.updated',
  'abonent.blocked',
  'abonent.activated',
  'abonent.deactivated',
  'abonent.deleted',
];

function preventEmpty(value: string | undefined) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : undefined;
}

export default function AutomationPage() {
  const { t } = useTranslation();
  const keys = useSSHKeys();
  const groups = useServerGroups();
  const servers = useManagedServers();
  const templates = useCommandTemplates();
  const rules = useEventActionRules();

  const createKey = useCreateSSHKey();
  const createGroup = useCreateServerGroup();
  const createServer = useCreateManagedServer();
  const createTemplate = useCreateCommandTemplate();
  const createRule = useCreateEventActionRule();
  const deleteItem = useDeleteAutomationItem();
  const deleteRule = useDeleteEventActionRule();

  const [keyForm, setKeyForm] = useState({ name: '', private_key: '', public_key: '' });
  const [groupForm, setGroupForm] = useState({ name: '', strategy: 'first_active' });
  const [serverForm, setServerForm] = useState({ group_id: '', key_id: '', name: '', host: '', port: 22, default_cmd: '' });
  const [templateForm, setTemplateForm] = useState({ name: '', description: '', body: '' });
  const [ruleForm, setRuleForm] = useState({
    title: '',
    event_type: 'service.activated',
    service_type: '',
    server_group_id: '',
    server_id: '',
    template_id: '',
    command: '',
    priority: 50,
    max_retries: 3,
  });

  const isLoading = keys.isLoading || groups.isLoading || servers.isLoading || templates.isLoading || rules.isLoading;

  async function submitKey(event: FormEvent) {
    event.preventDefault();
    await createKey.mutateAsync({ ...keyForm, public_key: preventEmpty(keyForm.public_key) });
    setKeyForm({ name: '', private_key: '', public_key: '' });
    toast.success(t('Created'));
  }

  async function submitGroup(event: FormEvent) {
    event.preventDefault();
    await createGroup.mutateAsync({ name: groupForm.name, transport: 'ssh', strategy: groupForm.strategy });
    setGroupForm({ name: '', strategy: 'first_active' });
    toast.success(t('Created'));
  }

  async function submitServer(event: FormEvent) {
    event.preventDefault();
    await createServer.mutateAsync({
      ...serverForm,
      key_id: preventEmpty(serverForm.key_id) || null,
      default_cmd: preventEmpty(serverForm.default_cmd),
    });
    setServerForm({ group_id: serverForm.group_id, key_id: serverForm.key_id, name: '', host: '', port: 22, default_cmd: '' });
    toast.success(t('Created'));
  }

  async function submitTemplate(event: FormEvent) {
    event.preventDefault();
    await createTemplate.mutateAsync({ ...templateForm, description: preventEmpty(templateForm.description), transport: 'ssh' });
    setTemplateForm({ name: '', description: '', body: '' });
    toast.success(t('Created'));
  }

  async function submitRule(event: FormEvent) {
    event.preventDefault();
    await createRule.mutateAsync({
      title: preventEmpty(ruleForm.title),
      event_type: ruleForm.event_type,
      action_type: 'ssh.exec',
      service_type: preventEmpty(ruleForm.service_type),
      server_group_id: preventEmpty(ruleForm.server_group_id) || null,
      server_id: preventEmpty(ruleForm.server_id) || null,
      template_id: preventEmpty(ruleForm.template_id) || null,
      command: preventEmpty(ruleForm.command),
      priority: Number(ruleForm.priority || 50),
      max_retries: Number(ruleForm.max_retries || 3),
    });
    setRuleForm({ ...ruleForm, title: '', service_type: '', command: '' });
    toast.success(t('Created'));
  }

  return (
    <div className="flex-1 space-y-5 p-8 pt-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">{t('Automation')}</h2>
        <p className="text-sm text-muted-foreground">{t('AutomationDescription')}</p>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><KeyRound className="h-5 w-5" />{t('SSHKeys')}</CardTitle>
            <CardDescription>{t('SSHKeysDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={submitKey} className="grid gap-3">
              <Label>{t('Name')}<Input value={keyForm.name} onChange={(e) => setKeyForm({ ...keyForm, name: e.target.value })} required /></Label>
              <Label>{t('PrivateKey')}<Textarea value={keyForm.private_key} onChange={(e) => setKeyForm({ ...keyForm, private_key: e.target.value })} required rows={5} /></Label>
              <Label>{t('PublicKey')}<Textarea value={keyForm.public_key} onChange={(e) => setKeyForm({ ...keyForm, public_key: e.target.value })} rows={2} /></Label>
              <Button disabled={createKey.isPending}><Plus className="mr-2 h-4 w-4" />{t('Create')}</Button>
            </form>
            <div className="space-y-2">
              {(keys.data || []).map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-md border p-3 text-sm">
                  <span>{item.name}</span>
                  <Button variant="ghost" size="sm" onClick={() => deleteItem.mutate({ type: 'ssh-keys', id: item.id })} title={t('Delete')}><Trash2 className="h-4 w-4" /></Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Server className="h-5 w-5" />{t('ServerGroups')}</CardTitle>
            <CardDescription>{t('ServerGroupsDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={submitGroup} className="grid gap-3 md:grid-cols-[1fr_180px_auto]">
              <Label>{t('Name')}<Input value={groupForm.name} onChange={(e) => setGroupForm({ ...groupForm, name: e.target.value })} required /></Label>
              <Label>{t('Strategy')}<Select value={groupForm.strategy} onChange={(e) => setGroupForm({ ...groupForm, strategy: e.target.value })}><option value="first_active">first_active</option><option value="round_robin">round_robin</option></Select></Label>
              <Button className="self-end" disabled={createGroup.isPending}><Plus className="mr-2 h-4 w-4" />{t('Create')}</Button>
            </form>
            <div className="space-y-2">
              {(groups.data || []).map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-md border p-3 text-sm">
                  <span>{item.name} · {item.strategy}</span>
                  <Button variant="ghost" size="sm" onClick={() => deleteItem.mutate({ type: 'server-groups', id: item.id })} title={t('Delete')}><Trash2 className="h-4 w-4" /></Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Server className="h-5 w-5" />{t('Servers')}</CardTitle>
            <CardDescription>{t('ServersDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={submitServer} className="grid gap-3">
              <div className="grid gap-3 md:grid-cols-2">
                <Label>{t('ServerGroup')}<Select value={serverForm.group_id} onChange={(e) => setServerForm({ ...serverForm, group_id: e.target.value })} required><option value="">{t('Select')}</option>{(groups.data || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></Label>
                <Label>{t('SSHKey')}<Select value={serverForm.key_id} onChange={(e) => setServerForm({ ...serverForm, key_id: e.target.value })}><option value="">{t('Select')}</option>{(keys.data || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></Label>
                <Label>{t('Name')}<Input value={serverForm.name} onChange={(e) => setServerForm({ ...serverForm, name: e.target.value })} required /></Label>
                <Label>{t('Host')}<Input value={serverForm.host} onChange={(e) => setServerForm({ ...serverForm, host: e.target.value })} placeholder="root@10.0.0.10" required /></Label>
                <Label>{t('Port')}<Input type="number" min={1} max={65535} value={serverForm.port} onChange={(e) => setServerForm({ ...serverForm, port: Number(e.target.value) })} required /></Label>
              </div>
              <Label>{t('DefaultCommand')}<Textarea value={serverForm.default_cmd} onChange={(e) => setServerForm({ ...serverForm, default_cmd: e.target.value })} rows={3} /></Label>
              <Button disabled={createServer.isPending}><Plus className="mr-2 h-4 w-4" />{t('Create')}</Button>
            </form>
            <div className="space-y-2">
              {(servers.data || []).map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-md border p-3 text-sm">
                  <span>{item.name} · {item.host}:{item.port}</span>
                  <Button variant="ghost" size="sm" onClick={() => deleteItem.mutate({ type: 'servers', id: item.id })} title={t('Delete')}><Trash2 className="h-4 w-4" /></Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><TerminalSquare className="h-5 w-5" />{t('CommandTemplates')}</CardTitle>
            <CardDescription>{t('CommandTemplatesDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={submitTemplate} className="grid gap-3">
              <Label>{t('Name')}<Input value={templateForm.name} onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })} required /></Label>
              <Label>{t('Description')}<Input value={templateForm.description} onChange={(e) => setTemplateForm({ ...templateForm, description: e.target.value })} /></Label>
              <Label>{t('Command')}<Textarea value={templateForm.body} onChange={(e) => setTemplateForm({ ...templateForm, body: e.target.value })} placeholder="sh /opt/scripts/activate.sh {abonent_id} {service_id} {event_type}" required rows={5} /></Label>
              <Button disabled={createTemplate.isPending}><Plus className="mr-2 h-4 w-4" />{t('Create')}</Button>
            </form>
            <div className="space-y-2">
              {(templates.data || []).map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-md border p-3 text-sm">
                  <span>{item.name}</span>
                  <Button variant="ghost" size="sm" onClick={() => deleteItem.mutate({ type: 'templates', id: item.id })} title={t('Delete')}><Trash2 className="h-4 w-4" /></Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Workflow className="h-5 w-5" />{t('EventRules')}</CardTitle>
          <CardDescription>{t('EventRulesDescription')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={submitRule} className="grid gap-3 lg:grid-cols-3">
            <Label>{t('Title')}<Input value={ruleForm.title} onChange={(e) => setRuleForm({ ...ruleForm, title: e.target.value })} /></Label>
            <Label>{t('Event')}<Select value={ruleForm.event_type} onChange={(e) => setRuleForm({ ...ruleForm, event_type: e.target.value })}>{events.map((event) => <option key={event} value={event}>{event}</option>)}</Select></Label>
            <Label>{t('ServiceType')}<Input value={ruleForm.service_type} onChange={(e) => setRuleForm({ ...ruleForm, service_type: e.target.value })} placeholder="internet" /></Label>
            <Label>{t('Priority')}<Input type="number" min={0} max={1000} value={ruleForm.priority} onChange={(e) => setRuleForm({ ...ruleForm, priority: Number(e.target.value) })} /></Label>
            <Label>{t('MaxRetries')}<Input type="number" min={0} max={20} value={ruleForm.max_retries} onChange={(e) => setRuleForm({ ...ruleForm, max_retries: Number(e.target.value) })} /></Label>
            <Label>{t('ServerGroup')}<Select value={ruleForm.server_group_id} onChange={(e) => setRuleForm({ ...ruleForm, server_group_id: e.target.value })}><option value="">{t('Select')}</option>{(groups.data || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></Label>
            <Label>{t('Server')}<Select value={ruleForm.server_id} onChange={(e) => setRuleForm({ ...ruleForm, server_id: e.target.value })}><option value="">{t('AutoSelect')}</option>{(servers.data || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></Label>
            <Label>{t('Template')}<Select value={ruleForm.template_id} onChange={(e) => setRuleForm({ ...ruleForm, template_id: e.target.value })}><option value="">{t('InlineCommand')}</option>{(templates.data || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></Label>
            <Label className="lg:col-span-3">{t('InlineCommand')}<Textarea value={ruleForm.command} onChange={(e) => setRuleForm({ ...ruleForm, command: e.target.value })} rows={3} /></Label>
            <p className="lg:col-span-3 text-xs text-muted-foreground">{t('CommandVariablesHelp')}</p>
            <Button className="lg:col-span-3" disabled={createRule.isPending || isLoading}><Plus className="mr-2 h-4 w-4" />{t('Create')}</Button>
          </form>
          <div className="grid gap-2">
            {(rules.data || []).map((item) => (
              <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded-md border p-3 text-sm">
                <div>
                  <div className="font-medium">{item.title || item.event_type}</div>
                  <div className="text-muted-foreground">{item.event_type} · {item.action_type} · {item.service_type || t('AllServices')}</div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => deleteRule.mutate(item.id)} title={t('Delete')}><Trash2 className="h-4 w-4" /></Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
