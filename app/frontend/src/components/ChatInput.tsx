import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import type { LanguageCode } from '../types/api';
import { TRANSLATIONS } from '../i18n/translations';

interface ChatInputProps {
  onSendMessage: (text: string) => void;
  isLoading: boolean;
  isOffline: boolean;
  language: LanguageCode;
  initialValue?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading,
  isOffline,
  language,
  initialValue = '',
}) => {
  const [inputText, setInputText] = useState(initialValue);
  const inputRef = useRef<HTMLInputElement>(null);
  const t = TRANSLATIONS[language];

  useEffect(() => {
    if (initialValue) {
      setInputText(initialValue);
      inputRef.current?.focus();
    }
  }, [initialValue]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading || isOffline) return;

    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form
      data-testid="chat-form"
      data-accessibility-id="chat-form"
      onSubmit={handleSubmit}
      style={{
        padding: '0.85rem 1.25rem',
        borderTop: '1px solid var(--color-border)',
        backgroundColor: 'var(--color-surface)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.65rem',
      }}
    >
      <div style={{ flex: 1, position: 'relative' }}>
        <label
          htmlFor="chat-input"
          className="sr-only"
          style={{ position: 'absolute', width: '1px', height: '1px', padding: 0, margin: '-1px', overflow: 'hidden', clip: 'rect(0, 0, 0, 0)', border: 0 }}
        >
          {t.inputPlaceholder}
        </label>
        <input
          id="chat-input"
          ref={inputRef}
          type="text"
          data-testid="chat-input"
          data-accessibility-id="chat-input"
          aria-label={t.inputPlaceholder}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isOffline ? t.offlineBannerTitle : t.inputPlaceholder}
          disabled={isLoading || isOffline}
          maxLength={1000}
          autoComplete="off"
          style={{
            width: '100%',
            padding: '0.75rem 1rem',
            fontSize: '0.95rem',
            borderRadius: '24px',
            border: '1.5px solid var(--color-border)',
            backgroundColor: isOffline ? 'var(--color-disabled-bg)' : 'var(--color-surface)',
            color: 'var(--color-text)',
            outline: 'none',
            boxSizing: 'border-box',
          }}
        />
      </div>

      <button
        type="submit"
        data-testid="send-button"
        data-accessibility-id="send-button"
        aria-label={isLoading ? t.sending : t.send}
        disabled={!inputText.trim() || isLoading || isOffline}
        style={{
          width: '42px',
          height: '42px',
          borderRadius: '50%',
          backgroundColor: !inputText.trim() || isLoading || isOffline ? 'var(--color-disabled)' : 'var(--color-primary)',
          color: '#ffffff',
          border: 'none',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: !inputText.trim() || isLoading || isOffline ? 'not-allowed' : 'pointer',
          flexShrink: 0,
          transition: 'background-color 0.2s',
        }}
      >
        <Send size={18} aria-hidden="true" />
      </button>
    </form>
  );
};
