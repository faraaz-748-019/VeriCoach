import React from 'react';
import type { LanguageCode } from '../types/api';
import { TRANSLATIONS } from '../i18n/translations';

interface LoadingIndicatorProps {
  language: LanguageCode;
}

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ language }) => {
  const t = TRANSLATIONS[language];

  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="loading-indicator"
      data-accessibility-id="loading-indicator"
      className="loading-indicator-bubble"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.6rem',
        padding: '0.85rem 1.25rem',
        borderRadius: '16px',
        backgroundColor: 'var(--color-surface-variant)',
        color: 'var(--color-text-secondary)',
        fontSize: '0.9rem',
        maxWidth: '85%',
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      }}
    >
      <div className="typing-dots" aria-hidden="true" style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
        <span className="dot" style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-primary)', display: 'inline-block' }} />
        <span className="dot" style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-primary)', display: 'inline-block' }} />
        <span className="dot" style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-primary)', display: 'inline-block' }} />
      </div>
      <span>{t.loadingMessage}</span>
    </div>
  );
};
