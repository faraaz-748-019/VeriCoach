/**
 * VeriCoach API and Domain Type Definitions
 */

export type LanguageCode = 'en' | 'hi' | 'te';

export interface SourceCitation {
  doc_id: string;
  title: string;
  snippet: string;
  score: number;
}

export interface ChatRequestV1 {
  question: string;
  language: LanguageCode | 'auto';
  session_id?: string;
}

export interface ChatResponseV1 {
  answer: string;
  language: string;
  sources: SourceCitation[];
  refused: boolean;
  refusal_reason: string | null;
  trace_id: string;
}

export interface FeedbackRequestV1 {
  trace_id: string;
  rating: number; // 1 to 5
  comment?: string;
}

export interface FeedbackResponseV1 {
  status: string;
  trace_id: string;
}

export interface HealthResponseV1 {
  status: string;
  version: string;
  provider: string;
  documents_indexed: number;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  language?: LanguageCode;
  sources?: SourceCitation[];
  refused?: boolean;
  refusalReason?: string | null;
  traceId?: string;
  feedbackRating?: number | null; // 1 (thumbs down) or 5 (thumbs up)
  feedbackSubmitted?: boolean;
}
