import React from 'react';
import { AlertCircle, X, RefreshCw } from 'lucide-react';
import type { LanguageCode } from '../types/api';
import { TRANSLATIONS } from '../i18n/translations';

interface ErrorBannerProps {
  errorMessage: string | null;
  language: LanguageCode;
  onDismiss: () => void;
  onRetry?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  errorMessage,
  language,
  onDismiss,
  onRetry,
}) => {
  if (!errorMessage) return null;

  const t = TRANSLATIONS[language];

  return (
    <div
      role="alert"
      aria-live="polite"
      data-testid="error-banner"
      data-accessibility-id="error-banner"
      style={{
        backgroundColor: '#991b1b',
        color: '#fef2f2',
        padding: '0.75rem 1rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '0.75rem',
        fontSize: '0.875rem',
        borderBottom: '1px solid #b91c1c',
        zIndex: 40,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1 }}>
        <AlertCircle size={20} aria-hidden="true" style={{ flexShrink: 0, color: '#fca5a5' }} />
        <span>
          <strong>{t.errorBannerTitle}: </strong>
          {errorMessage}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
        {onRetry && (
          <button
            type="button"
            data-testid="error-banner-retry"
            data-accessibility-id="error-banner-retry"
            aria-label={t.retry}
            onClick={onRetry}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem',
              backgroundColor: 'rgba(255,255,255,0.2)',
              border: 'none',
              borderRadius: '4px',
              color: '#ffffff',
              padding: '0.3rem 0.6rem',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={14} aria-hidden="true" />
            {t.retry}
          </button>
        )}
        <button
          type="button"
          data-testid="error-banner-dismiss"
          data-accessibility-id="error-banner-dismiss"
          aria-label={t.dismiss}
          onClick={onDismiss}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            color: '#fef2f2',
            padding: '0.25rem',
            cursor: 'pointer',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <X size={18} aria-hidden="true" />
        </button>
      </div>
    </div>
  );
};
