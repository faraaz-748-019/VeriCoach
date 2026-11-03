export type Locale = 'en' | 'hi' | 'te';

export interface AccountInfo {
  bank: string;
  account_number: string;
  balance: number;
  type: string;
}

export interface SyntheticUser {
  name: string;
  email: string;
  phone: string;
  pan: string;
  aadhaar: string;
  upi_id: string;
  locale: string;
  monthly_income: number;
  accounts: AccountInfo[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  provider?: string;
  model?: string;
  timestamp: string;
}

export interface HealthInfo {
  status: string;
  version: string;
  provider: string;
  default_locale: string;
}
