import React from 'react';
import { Settings, ShieldCheck } from 'lucide-react';
import type { LanguageCode } from '../types/api';
import { TRANSLATIONS } from '../i18n/translations';
import { LanguageSelector } from './LanguageSelector';

interface HeaderProps {
  currentLanguage: LanguageCode;
  onLanguageChange: (lang: LanguageCode) => void;
  onOpenSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentLanguage,
  onLanguageChange,
  onOpenSettings,
}) => {
  const t = TRANSLATIONS[currentLanguage];

  return (
    <header
      data-testid="app-header"
      data-accessibility-id="app-header"
      role="banner"
      style={{
        padding: '0.75rem 1.25rem',
        backgroundColor: 'var(--color-surface)',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
        boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            backgroundColor: 'var(--color-primary)',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            fontSize: '1.1rem',
            boxShadow: '0 2px 4px rgba(37, 99, 235, 0.25)',
          }}
        >
          <ShieldCheck size={22} />
        </div>
        <div>
          <h1
            data-testid="app-title"
            style={{
              margin: 0,
              fontSize: '1.15rem',
              fontWeight: 700,
              color: 'var(--color-text)',
              lineHeight: 1.2,
            }}
          >
            {t.appName}
          </h1>
          <p
            style={{
              margin: 0,
              fontSize: '0.75rem',
              color: 'var(--color-text-secondary)',
              lineHeight: 1,
            }}
          >
            {t.tagline}
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <LanguageSelector
          currentLanguage={currentLanguage}
          onLanguageChange={onLanguageChange}
        />

        <button
          type="button"
          data-testid="settings-button"
          data-accessibility-id="settings-button"
          aria-label={t.settingsTitle}
          onClick={onOpenSettings}
          style={{
            backgroundColor: 'transparent',
            border: '1.5px solid var(--color-border)',
            borderRadius: '8px',
            padding: '0.4rem',
            cursor: 'pointer',
            color: 'var(--color-text-secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'color 0.2s, border-color 0.2s',
          }}
        >
          <Settings size={18} aria-hidden="true" />
        </button>
      </div>
    </header>
  );
};
