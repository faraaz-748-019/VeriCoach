import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp } from 'lucide-react';
import type { LanguageCode, SourceCitation } from '../types/api';
import { TRANSLATIONS } from '../i18n/translations';

interface CitationsPanelProps {
  sources: SourceCitation[];
  language: LanguageCode;
  defaultExpanded?: boolean;
}

export const CitationsPanel: React.FC<CitationsPanelProps> = ({
  sources,
  language,
  defaultExpanded = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const t = TRANSLATIONS[language];

  if (!sources || sources.length === 0) return null;

  return (
    <div
      className="citations-wrapper"
      style={{
        marginTop: '0.75rem',
        borderTop: '1px solid var(--color-border)',
        paddingTop: '0.5rem',
      }}
    >
      <button
        type="button"
        data-testid="citations-toggle"
        data-accessibility-id="citations-toggle"
        aria-expanded={isExpanded}
        aria-controls="citations-panel-content"
        onClick={() => setIsExpanded((prev) => !prev)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.4rem',
          backgroundColor: 'transparent',
          border: 'none',
          color: 'var(--color-primary)',
          fontSize: '0.85rem',
          fontWeight: 600,
          cursor: 'pointer',
          padding: '0.25rem 0',
        }}
      >
        <BookOpen size={16} aria-hidden="true" />
        <span>
          {isExpanded ? t.hideSources : t.viewSources} ({sources.length})
        </span>
        {isExpanded ? (
          <ChevronUp size={16} aria-hidden="true" />
        ) : (
          <ChevronDown size={16} aria-hidden="true" />
        )}
      </button>

      {isExpanded && (
        <div
          id="citations-panel-content"
          data-testid="citations-panel"
          data-accessibility-id="citations-panel"
          style={{
            marginTop: '0.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', fontWeight: 500 }}>
            {t.sourcesDescription}
          </div>

          {sources.map((source, index) => (
            <div
              key={`${source.doc_id}-${index}`}
              data-testid="citation-item"
              data-accessibility-id="citation-item"
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: '8px',
                padding: '0.65rem 0.85rem',
                fontSize: '0.825rem',
                boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.25rem',
                  gap: '0.5rem',
                }}
              >
                <span
                  data-testid="citation-title"
                  style={{
                    fontWeight: 600,
                    color: 'var(--color-text)',
                  }}
                >
                  {source.title}
                </span>
                <span
                  data-testid="citation-score"
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    backgroundColor: 'var(--color-badge-bg)',
                    color: 'var(--color-badge-text)',
                    padding: '0.15rem 0.45rem',
                    borderRadius: '12px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {t.relevanceScore}: {Math.round(source.score * 100)}%
                </span>
              </div>

              <p
                data-testid="citation-snippet"
                style={{
                  margin: 0,
                  color: 'var(--color-text-secondary)',
                  lineHeight: 1.4,
                  fontSize: '0.8rem',
                }}
              >
                "{source.snippet}"
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
