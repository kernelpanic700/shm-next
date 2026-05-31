import axios from 'axios';

// Use relative URL to go through Next.js rewrites proxy
// This works in Docker and locally through the Next.js rewrite in next.config.js.
const API_BASE_URL = '/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          // API returns { success, data: { access_token, refresh_token, ... } }
          const tokenData = response.data.data || response.data;
          const { access_token, refresh_token } = tokenData;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// API Types
export interface Abonent {
  id: string;
  full_name: string;
  name?: string;
  phone: string;
  login?: string | null;
  login2?: string | null;
  account_number?: string;
  email?: string;
  address?: string;
  status: 'active' | 'inactive' | 'suspended' | 'ACTIVE' | 'INACTIVE' | 'BLOCKED' | 'SUSPENDED';
  balance: number;
  currency: string;
  partner_id?: string | null;
  discount?: number;
  credit?: number;
  bonus?: number;
  comment?: string | null;
  contract?: string | null;
  can_overdraft?: boolean;
  verified?: boolean;
  settings?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AbonentListResponse {
  items: Abonent[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface AbonentProfile {
  abonent_id: string;
  data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Tariff {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  billing_period: 'monthly' | 'quarterly' | 'yearly';
  billing_cycle?: 'monthly' | 'quarterly' | 'yearly';
  is_active: boolean;
  created_at: string;
}

export interface Service {
  id: string;
  name: string;
  description?: string | null;
  price?: number;
  cost?: number;
  currency: string;
  is_active?: boolean;
  allow_to_order?: boolean;
  is_deleted?: boolean;
  period_cost?: string;
  category?: string | null;
  legacy_service_id?: number | null;
  max_count?: number | null;
  pay_always?: boolean;
  no_discount?: boolean;
  pay_in_credit?: boolean;
  is_composite?: boolean;
  created_at: string;
}

export interface ServiceListResponse {
  items: Service[];
  total: number;
}

export interface Payment {
  id: string;
  abonent_id: string;
  amount: number;
  currency: string;
  status: 'NEW' | 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'REFUNDED' | 'CANCELLED';
  payment_method: string;
  external_id: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface SpoolTask {
  id: string;
  action_type: string;
  status: 'NEW' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'RETRY';
  priority: number;
  retry_count: number;
  max_retries: number;
  execute_after: string | null;
  created_at: string;
  updated_at: string;
  payload: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error_message: string | null;
}

export interface AutomationListResponse<T> {
  items: T[];
  total: number;
}

export interface SSHKey {
  id: string;
  name: string;
  public_key?: string | null;
  fingerprint?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ServerGroup {
  id: string;
  name: string;
  transport: string;
  strategy: string;
  settings?: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ManagedServer {
  id: string;
  group_id: string;
  name: string;
  host: string;
  port: number;
  key_id?: string | null;
  proxy_jump?: string | null;
  default_cmd?: string | null;
  settings?: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CommandTemplate {
  id: string;
  name: string;
  transport: string;
  body: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EventActionRule {
  id: string;
  event_type: string;
  action_type: string;
  title: string;
  service_type?: string | null;
  catalog_service_id?: string | null;
  server_group_id?: string | null;
  server_id?: string | null;
  template_id?: string | null;
  command?: string | null;
  settings: Record<string, unknown>;
  priority: number;
  max_retries: number;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface EventActionRuleListResponse {
  items: EventActionRule[];
  total: number;
}

export interface BillingCycle {
  id: string;
  period: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface BillingCycleRunResult {
  period_start: string;
  period_end: string;
  offset: number;
  limit: number;
  processed: number;
  withdraw_count: number;
  invoice_count: number;
  items: Array<{
    abonent_id: string;
    withdraw_count: number;
    invoice_ids: string[];
    status: 'processed' | 'skipped';
  }>;
}

export interface WithdrawResult {
  service_id: string;
  amount: number;
  currency: string;
  subtotal?: number;
  discount?: number;
  bonus_used?: number;
  pay_in_credit?: boolean;
  withdraw_id?: string;
  invoice_id?: string;
}

export interface Invoice {
  id: string;
  abonent_id: string;
  amount: number;
  currency: string;
  status: 'DRAFT' | 'ISSUED' | 'SENT' | 'PAID' | 'OVERDUE' | 'CANCELLED';
  period_start: string | null;
  period_end: string | null;
  due_date: string | null;
  description: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface InvoiceListResponse {
  items: Invoice[];
  total: number;
  page: number;
  per_page: number;
}

export interface BonusEntry {
  id: string;
  abonent_id: string;
  amount: number;
  currency: string;
  reason: string;
  expires_at: string | null;
  is_active: boolean;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface BonusEntryListResponse {
  items: BonusEntry[];
  total: number;
}

export interface Discount {
  id: string;
  name: string;
  description: string;
  discount_type: 'percent' | 'fixed' | 'relative';
  value: number;
  currency: string;
  valid_from: string | null;
  valid_to: string | null;
  is_active: boolean;
  max_uses: number | null;
  used_count: number;
  created_at: string;
  updated_at: string;
}

export interface DiscountListResponse {
  items: Discount[];
  total: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
