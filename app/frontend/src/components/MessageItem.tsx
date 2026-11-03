import React from 'react';
import { ShieldAlert } from 'lucide-react';
import type { ChatMessage, LanguageCode } from '../types/api';
import { TRANSLATIONS } from '../i18n/translations';
import { CitationsPanel } from './CitationsPanel';
import { FeedbackButtons } from './FeedbackButtons';

interface MessageItemProps {
  message: ChatMessage;
  language: LanguageCode;
  onFeedbackSent?: (rating: number) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  language,
  onFeedbackSent,
}) => {
  const isUser = message.sender === 'user';
  const t = TRANSLATIONS[language];

  return (
    <div
      data-testid={isUser ? 'message-user' : 'message-assistant'}
      data-accessibility-id={isUser ? 'message-user' : 'message-assistant'}
      role="article"
      aria-label={isUser ? 'Your message' : 'Assistant response'}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignSelf: isUser ? 'flex-end' : 'flex-start',
        maxWidth: '85%',
        marginBottom: '1rem',
      }}
    >
      <div
        style={{
          padding: '0.85rem 1.15rem',
          borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
          backgroundColor: isUser ? 'var(--color-chat-user-bg)' : 'var(--color-chat-assistant-bg)',
          color: isUser ? 'var(--color-chat-user-text)' : 'var(--color-chat-assistant-text)',
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
          border: isUser ? 'none' : '1px solid var(--color-border)',
          wordBreak: 'break-word',
        }}
      >
        {message.refused && (
          <div
            data-testid="refusal-warning"
            data-accessibility-id="refusal-warning"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              backgroundColor: '#fef3c7',
              color: '#92400e',
              padding: '0.25rem 0.5rem',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: 700,
              marginBottom: '0.5rem',
            }}
          >
            <ShieldAlert size={14} aria-hidden="true" />
            <span>{t.refusedBadge}</span>
          </div>
        )}

        <div
          data-testid="message-text"
          style={{
            fontSize: '0.95rem',
            lineHeight: 1.5,
            whiteSpace: 'pre-wrap',
          }}
        >
          {message.text}
        </div>

        {/* Citations panel for assistant responses */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <CitationsPanel sources={message.sources} language={language} />
        )}
      </div>

      {/* Thumbs up/down feedback for assistant responses */}
      {!isUser && message.traceId && (
        <FeedbackButtons
          traceId={message.traceId}
          language={language}
          initialRating={message.feedbackRating}
          onFeedbackSent={onFeedbackSent}
        />
      )}
    </div>
  );
};
