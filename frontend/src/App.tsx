import React, { useEffect, useState } from 'react';
import {
  bootstrapSyntheticData,
  clearKnowledgeBase,
  fetchHealth,
  generateSyntheticUser,
  sendChatMessage,
} from './api';
import { ChatMessage, HealthInfo, Locale, SyntheticUser } from './types';

const SUGGESTIONS: Record<Locale, string[]> = {
  en: [
    'What is the recommended emergency fund?',
    'What accounts and balances are available?',
    'Give me advice on mutual fund SIP.',
  ],
  hi: [
    'आपातकालीन निधि (Emergency Fund) की क्या सिफारिश है?',
    'मेरी कुल बचत और खाते कितने हैं?',
    'म्यूचुअल फंड एसआईपी (SIP) के बारे में सलाह दीजिए।',
  ],
  te: [
    'అత్యవసర నిధి (Emergency Fund) సిఫార్సు ఏమిటి?',
    'నా ఖాతాలు మరియు బ్యాలెన్స్ ఎంత?',
    'మ్యూచువల్ ఫండ్ ఎస్ఐపీ (SIP) గురించి సలహా ఇవ్వండి.',
  ],
};

export const App: React.FC = () => {
  const [locale, setLocale] = useState<Locale>('en');
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [syntheticUser, setSyntheticUser] = useState<SyntheticUser | null>(null);
  const [infoMessage, setInfoMessage] = useState<string>('');

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() =>
        setHealth({
          status: 'offline',
          version: '0.1.0',
          provider: 'unknown',
          default_locale: 'en',
        })
      );
  }, []);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const res = await sendChatMessage(text, locale);
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: res.response,
        provider: res.provider,
        model: res.model,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: `Error connecting to assistant: ${(err as Error).message}`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateUser = async () => {
    try {
      setInfoMessage('Generating fake profile (Faker)...');
      const user = await generateSyntheticUser(locale);
      setSyntheticUser(user);
      setInfoMessage(`Generated synthetic user: ${user.name}`);
    } catch (err: unknown) {
      setInfoMessage(`Error: ${(err as Error).message}`);
    }
  };

  const handleBootstrap = async () => {
    try {
      setInfoMessage('Indexing synthetic portfolio into RAG...');
      const res = await bootstrapSyntheticData(locale, 2);
      setInfoMessage(
        `Bootstrapped! Created ${res.users_created} users, indexed ${res.chunks_indexed} context chunks.`
      );
    } catch (err: unknown) {
      setInfoMessage(`Error: ${(err as Error).message}`);
    }
  };

  const handleClear = async () => {
    try {
      await clearKnowledgeBase();
      setInfoMessage('Knowledge base cleared.');
    } catch (err: unknown) {
      setInfoMessage(`Error: ${(err as Error).message}`);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <div className="title-group">
          <h1>VeriCoach</h1>
          <p>Multilingual Personal-Finance Assistant (English · हिन्दी · తెలుగు)</p>
        </div>
        <div className="status-badge">
          <span>●</span>
          <span>Provider: {health?.provider || 'connecting...'}</span>
        </div>
      </header>

      <div className="layout">
        <div className="chat-panel">
          <div className="chat-header">
            <strong>Assistant Conversation</strong>
            <select
              className="locale-select"
              value={locale}
              onChange={(e) => setLocale(e.target.value as Locale)}
            >
              <option value="en">English (en)</option>
              <option value="hi">हिन्दी (hi)</option>
              <option value="te">తెలుగు (te)</option>
            </select>
          </div>

          <div className="chat-messages">
            {messages.length === 0 && (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '60px' }}>
                <p style={{ marginBottom: '12px' }}>
                  Ask a question or bootstrap the assistant with synthetic data from the right panel!
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {SUGGESTIONS[locale].map((s, idx) => (
                    <button
                      key={idx}
                      className="btn-secondary"
                      style={{ fontSize: '0.85rem' }}
                      onClick={() => handleSend(s)}
                    >
                      💡 {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m) => (
              <div key={m.id} className={`message ${m.sender}`}>
                <p>{m.text}</p>
                <div className="message-meta">
                  {m.timestamp} {m.provider && `• [${m.provider}]`}
                </div>
              </div>
            ))}
            {loading && (
              <div className="message assistant">
                <em>Thinking in {locale}...</em>
              </div>
            )}
          </div>

          <form
            className="chat-input-box"
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
          >
            <input
              type="text"
              placeholder={
                locale === 'hi'
                  ? 'अपना वित्तीय प्रश्न यहाँ पूछें...'
                  : locale === 'te'
                  ? 'మీ ఆర్థిక ప్రశ్నను ఇక్కడ అడగండి...'
                  : 'Ask your personal finance question...'
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <button type="submit" disabled={loading}>
              Send
            </button>
          </form>
        </div>

        <div className="side-panel">
          <div className="card">
            <h3>Synthetic Data (Faker)</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
              All PII values are 100% fake and dynamically generated for privacy-safe testing.
            </p>
            <button className="btn-secondary" onClick={handleGenerateUser}>
              👤 Generate Fake Profile
            </button>
            <button className="btn-secondary" onClick={handleBootstrap}>
              📚 Bootstrap RAG Knowledge Base
            </button>
            <button
              className="btn-secondary"
              style={{ color: '#dc2626' }}
              onClick={handleClear}
            >
              🗑️ Clear Knowledge Base
            </button>
            {infoMessage && (
              <div
                style={{
                  fontSize: '0.8rem',
                  padding: '8px',
                  background: '#f8fafc',
                  border: '1px solid var(--border)',
                  borderRadius: '6px',
                  marginTop: '8px',
                }}
              >
                {infoMessage}
              </div>
            )}
          </div>

          {syntheticUser && (
            <div className="card">
              <h3>Active Synthetic User</h3>
              <div className="profile-field">
                <span>Name:</span>
                <strong>{syntheticUser.name}</strong>
              </div>
              <div className="profile-field">
                <span>Fake PAN:</span>
                <code>{syntheticUser.pan}</code>
              </div>
              <div className="profile-field">
                <span>Fake Aadhaar:</span>
                <code>{syntheticUser.aadhaar}</code>
              </div>
              <div className="profile-field">
                <span>Fake UPI:</span>
                <code>{syntheticUser.upi_id}</code>
              </div>
              <div className="profile-field">
                <span>Monthly Income:</span>
                <span>₹{syntheticUser.monthly_income.toLocaleString()}</span>
              </div>
              {syntheticUser.accounts.length > 0 && (
                <div style={{ marginTop: '8px', borderTop: '1px solid var(--border)', paddingTop: '6px' }}>
                  <div className="profile-field">
                    <span>Bank:</span>
                    <span>{syntheticUser.accounts[0].bank}</span>
                  </div>
                  <div className="profile-field">
                    <span>Balance:</span>
                    <strong>₹{syntheticUser.accounts[0].balance.toLocaleString()}</strong>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
