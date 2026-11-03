import React, { useEffect, useRef } from 'react';
import type { ChatMessage, LanguageCode } from '../types/api';
import { TRANSLATIONS } from '../i18n/translations';
import { MessageItem } from './MessageItem';
import { LoadingIndicator } from './LoadingIndicator';

interface MessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
  language: LanguageCode;
  onSelectExampleQuery: (query: string) => void;
  onFeedbackSent?: (messageId: string, rating: number) => void;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading,
  language,
  onSelectExampleQuery,
  onFeedbackSent,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const t = TRANSLATIONS[language];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div
      data-testid="message-list"
      data-accessibility-id="message-list"
      role="log"
      aria-live="polite"
      aria-label="Conversation history"
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {messages.length === 0 ? (
        <div
          data-testid="welcome-hero"
          style={{
            margin: 'auto 0',
            textAlign: 'center',
            padding: '2rem 1rem',
          }}
        >
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              backgroundColor: 'var(--color-primary-light)',
              color: 'var(--color-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem',
              fontWeight: 800,
              fontSize: '1.5rem',
            }}
          >
            VC
          </div>
          <h2
            style={{
              fontSize: '1.35rem',
              fontWeight: 700,
              color: 'var(--color-text)',
              marginBottom: '0.5rem',
            }}
          >
            {t.welcomeTitle}
          </h2>
          <p
            style={{
              fontSize: '0.925rem',
              color: 'var(--color-text-secondary)',
              maxWidth: '540px',
              margin: '0 auto 1.5rem',
              lineHeight: 1.5,
            }}
          >
            {t.welcomeSubtitle}
          </p>

          <div style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'left' }}>
            <div
              style={{
                fontSize: '0.85rem',
                fontWeight: 600,
                color: 'var(--color-text-secondary)',
                marginBottom: '0.65rem',
              }}
            >
              {t.exampleQueriesTitle}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {t.exampleQueries.map((query, idx) => (
                <button
                  key={idx}
                  type="button"
                  data-testid={`example-query-${idx}`}
                  data-accessibility-id={`example-query-${idx}`}
                  onClick={() => onSelectExampleQuery(query)}
                  style={{
                    textAlign: 'left',
                    padding: '0.65rem 0.95rem',
                    borderRadius: '8px',
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'var(--color-surface)',
                    color: 'var(--color-text)',
                    fontSize: '0.875rem',
                    cursor: 'pointer',
                    transition: 'border-color 0.2s, background-color 0.2s',
                  }}
                >
                  "{query}"
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        messages.map((msg) => (
          <MessageItem
            key={msg.id}
            message={msg}
            language={language}
            onFeedbackSent={(rating) => onFeedbackSent?.(msg.id, rating)}
          />
        ))
      )}

      {isLoading && (
        <div style={{ marginBottom: '1rem', alignSelf: 'flex-start' }}>
          <LoadingIndicator language={language} />
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
