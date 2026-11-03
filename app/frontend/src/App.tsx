import React, { useState, useEffect, useCallback } from 'react';
import type { ChatMessage, LanguageCode } from './types/api';
import { TRANSLATIONS } from './i18n/translations';
import { sendChatMessage } from './services/api';
import { Header } from './components/Header';
import { OfflineBanner } from './components/OfflineBanner';
import { ErrorBanner } from './components/ErrorBanner';
import { MessageList } from './components/MessageList';
import { ChatInput } from './components/ChatInput';
import { SettingsModal } from './components/SettingsModal';

export const App: React.FC = () => {
  const [language, setLanguage] = useState<LanguageCode>('en');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState<boolean>(!navigator.onLine);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [sessionId] = useState<string>(() => `sess_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`);

  const t = TRANSLATIONS[language];

  // Monitor online / offline network state
  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleSendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return;

      setErrorMessage(null);
      setLastFailedMessage(null);

      const userMessageId = `msg_${Date.now()}_user`;
      const userMessage: ChatMessage = {
        id: userMessageId,
        sender: 'user',
        text: text.trim(),
        timestamp: new Date().toISOString(),
        language,
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        const response = await sendChatMessage(text.trim(), language, sessionId);

        const assistantMessage: ChatMessage = {
          id: `msg_${Date.now()}_assistant`,
          sender: 'assistant',
          text: response.answer,
          timestamp: new Date().toISOString(),
          language: (response.language as LanguageCode) || language,
          sources: response.sources,
          refused: response.refused,
          refusalReason: response.refusal_reason,
          traceId: response.trace_id,
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'An unexpected error occurred';
        setErrorMessage(msg);
        setLastFailedMessage(text.trim());
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, language, sessionId]
  );

  const handleRetry = useCallback(() => {
    if (lastFailedMessage) {
      handleSendMessage(lastFailedMessage);
    }
  }, [lastFailedMessage, handleSendMessage]);

  const handleFeedbackSent = useCallback((messageId: string, rating: number) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId ? { ...msg, feedbackRating: rating, feedbackSubmitted: true } : msg
      )
    );
  }, []);

  return (
    <div
      data-testid="chat-window"
      data-accessibility-id="chat-window"
      className="vericoach-app-container"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100%',
        maxWidth: '900px',
        margin: '0 auto',
        backgroundColor: 'var(--color-bg)',
        boxShadow: '0 0 20px rgba(0, 0, 0, 0.05)',
        position: 'relative',
      }}
    >
      <Header
        currentLanguage={language}
        onLanguageChange={setLanguage}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      <OfflineBanner isOffline={isOffline} language={language} />

      <ErrorBanner
        errorMessage={errorMessage}
        language={language}
        onDismiss={() => setErrorMessage(null)}
        onRetry={lastFailedMessage ? handleRetry : undefined}
      />

      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <MessageList
          messages={messages}
          isLoading={isLoading}
          language={language}
          onSelectExampleQuery={(query) => handleSendMessage(query)}
          onFeedbackSent={handleFeedbackSent}
        />

        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isOffline={isOffline}
          language={language}
        />
      </main>

      <footer
        data-testid="app-footer"
        style={{
          padding: '0.4rem 1rem',
          textAlign: 'center',
          fontSize: '0.725rem',
          color: 'var(--color-text-secondary)',
          backgroundColor: 'var(--color-surface)',
          borderTop: '1px solid var(--color-border)',
        }}
      >
        {t.disclaimer}
      </footer>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        language={language}
      />
    </div>
  );
};

export default App;
