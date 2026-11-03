import React, { useState, useEffect } from 'react';
import { X, Check, Server, Smartphone, Laptop } from 'lucide-react';
import type { LanguageCode } from '../types/api';
import { TRANSLATIONS } from '../i18n/translations';
import {
  getApiBaseUrl,
  setApiBaseUrl,
  getApiKey,
  setApiKey,
  getDefaultApiBaseUrl,
  isAndroidPlatform,
} from '../config/api';
import { checkBackendHealth } from '../services/api';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  language: LanguageCode;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  language,
}) => {
  const [backendUrl, setBackendUrlState] = useState('');
  const [apiKey, setApiKeyState] = useState('');
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [healthStatus, setHealthStatus] = useState<string | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  const t = TRANSLATIONS[language];
  const isAndroid = isAndroidPlatform();

  useEffect(() => {
    if (isOpen) {
      setBackendUrlState(getApiBaseUrl());
      setApiKeyState(getApiKey());
      setSaveMessage(null);
      verifyHealth();
    }
  }, [isOpen]);

  const verifyHealth = async () => {
    setIsCheckingHealth(true);
    try {
      const data = await checkBackendHealth();
      setHealthStatus(`Connected (${data.provider} provider, ${data.documents_indexed} docs indexed)`);
    } catch {
      setHealthStatus('Unable to reach backend');
    } finally {
      setIsCheckingHealth(false);
    }
  };

  if (!isOpen) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setApiBaseUrl(backendUrl);
    setApiKey(apiKey);
    setSaveMessage(t.settingsSaved);
    verifyHealth();
    setTimeout(() => {
      setSaveMessage(null);
    }, 2500);
  };

  const handleReset = () => {
    const defaultUrl = getDefaultApiBaseUrl();
    setBackendUrlState(defaultUrl);
    setApiBaseUrl(defaultUrl);
    setApiKeyState('');
    setApiKey('');
    verifyHealth();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="settings-title"
      data-testid="settings-modal"
      data-accessibility-id="settings-modal"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
        zIndex: 100,
      }}
    >
      <div
        style={{
          backgroundColor: 'var(--color-surface)',
          borderRadius: '12px',
          width: '100%',
          maxWidth: '480px',
          boxShadow: '0 8px 30px rgba(0, 0, 0, 0.25)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div
          style={{
            padding: '1rem 1.25rem',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Server size={20} color="var(--color-primary)" />
            <h3
              id="settings-title"
              style={{
                margin: 0,
                fontSize: '1.1rem',
                fontWeight: 700,
                color: 'var(--color-text)',
              }}
            >
              {t.settingsTitle}
            </h3>
          </div>
          <button
            type="button"
            data-testid="settings-close-button"
            data-accessibility-id="settings-close-button"
            aria-label="Close settings"
            onClick={onClose}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--color-text-secondary)',
              padding: '0.25rem',
            }}
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSave} style={{ padding: '1.25rem' }}>
          <div style={{ marginBottom: '1rem' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                marginBottom: '0.5rem',
                fontSize: '0.825rem',
                color: 'var(--color-text-secondary)',
              }}
            >
              {isAndroid ? <Smartphone size={16} /> : <Laptop size={16} />}
              <span>Platform detected: <strong>{isAndroid ? 'Android Emulator / Device' : 'Desktop / Web Browser'}</strong></span>
            </div>

            <label
              htmlFor="settings-backend-url"
              style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: 600,
                color: 'var(--color-text)',
                marginBottom: '0.35rem',
              }}
            >
              {t.backendUrlLabel}
            </label>
            <input
              id="settings-backend-url"
              type="text"
              data-testid="settings-backend-url-input"
              data-accessibility-id="settings-backend-url-input"
              value={backendUrl}
              onChange={(e) => setBackendUrlState(e.target.value)}
              placeholder="http://localhost:8000"
              style={{
                width: '100%',
                padding: '0.65rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-surface-variant)',
                color: 'var(--color-text)',
                fontSize: '0.9rem',
                boxSizing: 'border-box',
              }}
            />
            <div
              style={{
                fontSize: '0.75rem',
                color: 'var(--color-text-secondary)',
                marginTop: '0.35rem',
              }}
            >
              {t.backendUrlHelp}
            </div>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label
              htmlFor="settings-api-key"
              style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: 600,
                color: 'var(--color-text)',
                marginBottom: '0.35rem',
              }}
            >
              {t.apiKeyLabel}
            </label>
            <input
              id="settings-api-key"
              type="text"
              data-testid="settings-api-key-input"
              data-accessibility-id="settings-api-key-input"
              value={apiKey}
              onChange={(e) => setApiKeyState(e.target.value)}
              placeholder="Optional: vc-dev-key-12345"
              style={{
                width: '100%',
                padding: '0.65rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-surface-variant)',
                color: 'var(--color-text)',
                fontSize: '0.9rem',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {healthStatus && (
            <div
              data-testid="backend-health-status"
              style={{
                padding: '0.5rem 0.75rem',
                borderRadius: '6px',
                backgroundColor: healthStatus.includes('Connected') ? '#ecfdf5' : '#fef2f2',
                color: healthStatus.includes('Connected') ? '#065f46' : '#991b1b',
                fontSize: '0.8rem',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
              }}
            >
              <span>{isCheckingHealth ? 'Checking backend...' : healthStatus}</span>
            </div>
          )}

          {saveMessage && (
            <div
              data-testid="settings-save-success"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                color: 'var(--color-success)',
                fontSize: '0.825rem',
                fontWeight: 600,
                marginBottom: '0.85rem',
              }}
            >
              <Check size={16} />
              {saveMessage}
            </div>
          )}

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '0.75rem',
            }}
          >
            <button
              type="button"
              data-testid="settings-reset-button"
              data-accessibility-id="settings-reset-button"
              onClick={handleReset}
              style={{
                padding: '0.55rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                backgroundColor: 'transparent',
                color: 'var(--color-text-secondary)',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {t.resetDefault}
            </button>

            <button
              type="submit"
              data-testid="settings-save-button"
              data-accessibility-id="settings-save-button"
              style={{
                padding: '0.55rem 1.25rem',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: 'var(--color-primary)',
                color: '#ffffff',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {t.saveSettings}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
