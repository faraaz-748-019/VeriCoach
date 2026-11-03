import React from 'react';
import { Globe } from 'lucide-react';
import type { LanguageCode } from '../types/api';
import { TRANSLATIONS } from '../i18n/translations';

interface LanguageSelectorProps {
  currentLanguage: LanguageCode;
  onLanguageChange: (lang: LanguageCode) => void;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  currentLanguage,
  onLanguageChange,
}) => {
  const t = TRANSLATIONS[currentLanguage];

  return (
    <div className="language-selector-container" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <label
        htmlFor="language-select"
        className="sr-only"
        style={{ position: 'absolute', width: '1px', height: '1px', padding: 0, margin: '-1px', overflow: 'hidden', clip: 'rect(0, 0, 0, 0)', border: 0 }}
      >
        {t.selectLanguage}
      </label>
      <Globe size={18} aria-hidden="true" style={{ color: 'var(--color-primary-text)' }} />
      <select
        id="language-select"
        data-testid="language-select"
        data-accessibility-id="language-select"
        aria-label={t.selectLanguage}
        value={currentLanguage}
        onChange={(e) => onLanguageChange(e.target.value as LanguageCode)}
        style={{
          padding: '0.4rem 0.75rem',
          fontSize: '0.9rem',
          fontWeight: 600,
          borderRadius: '8px',
          border: '1.5px solid var(--color-border)',
          backgroundColor: 'var(--color-surface)',
          color: 'var(--color-text)',
          cursor: 'pointer',
          outline: 'none',
        }}
      >
        <option value="en" data-testid="lang-option-en">English</option>
        <option value="hi" data-testid="lang-option-hi">हिंदी (Hindi)</option>
        <option value="te" data-testid="lang-option-te">తెలుగు (Telugu)</option>
      </select>
    </div>
  );
};
