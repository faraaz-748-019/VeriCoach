import { Capacitor } from '@capacitor/core';

const STORAGE_KEY_BASE_URL = 'vericoach_api_base_url';
const STORAGE_KEY_API_KEY = 'vericoach_api_key';

/**
 * Determine the default backend URL based on platform.
 * In Android emulator, 10.0.2.2 points to host machine localhost:8000.
 */
export function getDefaultApiBaseUrl(): string {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && envUrl.trim() !== '') {
    return envUrl.trim();
  }

  // Check Capacitor platform
  const isAndroid = Capacitor.getPlatform() === 'android';
  if (isAndroid) {
    return 'http://10.0.2.2:8000';
  }

  // Web desktop fallback
  return 'http://localhost:8000';
}

export function getApiBaseUrl(): string {
  const custom = localStorage.getItem(STORAGE_KEY_BASE_URL);
  if (custom && custom.trim() !== '') {
    return custom.trim().replace(/\/+$/, '');
  }
  return getDefaultApiBaseUrl().replace(/\/+$/, '');
}

export function setApiBaseUrl(url: string): void {
  if (!url || url.trim() === '') {
    localStorage.removeItem(STORAGE_KEY_BASE_URL);
  } else {
    localStorage.setItem(STORAGE_KEY_BASE_URL, url.trim().replace(/\/+$/, ''));
  }
}

export function getApiKey(): string {
  const custom = localStorage.getItem(STORAGE_KEY_API_KEY);
  if (custom && custom.trim() !== '') {
    return custom.trim();
  }
  return (import.meta.env.VITE_API_KEY as string) || '';
}

export function setApiKey(key: string): void {
  if (!key || key.trim() === '') {
    localStorage.removeItem(STORAGE_KEY_API_KEY);
  } else {
    localStorage.setItem(STORAGE_KEY_API_KEY, key.trim());
  }
}

export function isAndroidPlatform(): boolean {
  return Capacitor.getPlatform() === 'android';
}
