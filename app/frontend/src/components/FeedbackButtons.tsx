import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Check } from 'lucide-react';
import type { LanguageCode } from '../types/api';
import { TRANSLATIONS } from '../i18n/translations';
import { sendFeedback } from '../services/api';

interface FeedbackButtonsProps {
  traceId?: string;
  language: LanguageCode;
  initialRating?: number | null;
  onFeedbackSent?: (rating: number) => void;
}

export const FeedbackButtons: React.FC<FeedbackButtonsProps> = ({
  traceId,
  language,
  initialRating,
  onFeedbackSent,
}) => {
  const [selectedRating, setSelectedRating] = useState<number | null>(initialRating ?? null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(Boolean(initialRating));
  const [feedbackError, setFeedbackError] = useState<string | null>(null);

  const t = TRANSLATIONS[language];

  if (!traceId) return null;

  const handleFeedback = async (rating: number) => {
    if (submitted || isSubmitting) return;

    setIsSubmitting(true);
    setFeedbackError(null);

    try {
      await sendFeedback(traceId, rating);
      setSelectedRating(rating);
      setSubmitted(true);
      if (onFeedbackSent) {
        onFeedbackSent(rating);
      }
    } catch {
      setFeedbackError(t.feedbackError);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="feedback-container"
      data-testid="feedback-container"
      data-accessibility-id="feedback-container"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        marginTop: '0.5rem',
        fontSize: '0.8rem',
      }}
    >
      {submitted ? (
        <span
          data-testid="feedback-status"
          data-accessibility-id="feedback-status"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            color: 'var(--color-success)',
            fontWeight: 500,
          }}
        >
          <Check size={14} aria-hidden="true" />
          {t.feedbackSuccess}
        </span>
      ) : (
        <>
          <button
            type="button"
            data-testid="feedback-thumbs-up"
            data-accessibility-id="feedback-thumbs-up"
            aria-label={t.thumbsUp}
            disabled={isSubmitting}
            onClick={() => handleFeedback(5)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0.3rem 0.5rem',
              borderRadius: '6px',
              border: '1px solid var(--color-border)',
              backgroundColor: selectedRating === 5 ? 'var(--color-primary-light)' : 'var(--color-surface)',
              color: selectedRating === 5 ? 'var(--color-primary)' : 'var(--color-text-secondary)',
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.2s, color 0.2s',
            }}
          >
            <ThumbsUp size={15} aria-hidden="true" />
          </button>

          <button
            type="button"
            data-testid="feedback-thumbs-down"
            data-accessibility-id="feedback-thumbs-down"
            aria-label={t.thumbsDown}
            disabled={isSubmitting}
            onClick={() => handleFeedback(1)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0.3rem 0.5rem',
              borderRadius: '6px',
              border: '1px solid var(--color-border)',
              backgroundColor: selectedRating === 1 ? 'var(--color-danger-light)' : 'var(--color-surface)',
              color: selectedRating === 1 ? 'var(--color-danger)' : 'var(--color-text-secondary)',
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.2s, color 0.2s',
            }}
          >
            <ThumbsDown size={15} aria-hidden="true" />
          </button>

          {feedbackError && (
            <span
              data-testid="feedback-error"
              data-accessibility-id="feedback-error"
              style={{ color: 'var(--color-danger)', fontSize: '0.75rem' }}
            >
              {feedbackError}
            </span>
          )}
        </>
      )}
    </div>
  );
};
