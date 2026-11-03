import React from 'react';
import { WifiOff } from 'lucide-react';
import type { LanguageCode } from '../types/api';
import { TRANSLATIONS } from '../i18n/translations';

interface OfflineBannerProps {
  isOffline: boolean;
  language: LanguageCode;
}

export const OfflineBanner: React.FC<OfflineBannerProps> = ({ isOffline, language }) => {
  if (!isOffline) return null;

  const t = TRANSLATIONS[language];

  return (
    <div
      role="alert"
      aria-live="assertive"
      data-testid="offline-banner"
      data-accessibility-id="offline-banner"
      style={{
        backgroundColor: '#7c2d12',
        color: '#ffedd5',
        padding: '0.65rem 1rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.6rem',
        fontSize: '0.875rem',
        fontWeight: 500,
        boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
        zIndex: 50,
      }}
    >
      <WifiOff size={18} aria-hidden="true" style={{ flexShrink: 0 }} />
      <div>
        <strong>{t.offlineBannerTitle}:</strong> {t.offlineBannerDesc}
      </div>
    </div>
  );
};
