import { getApiBaseUrl, getApiKey } from '../config/api';
import type {
  ChatRequestV1,
  ChatResponseV1,
  FeedbackRequestV1,
  FeedbackResponseV1,
  HealthResponseV1,
  LanguageCode,
} from '../types/api';

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function getHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const apiKey = getApiKey();
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }
  return headers;
}

export async function sendChatMessage(
  question: string,
  language: LanguageCode,
  sessionId?: string
): Promise<ChatResponseV1> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/v1/chat`;

  const payload: ChatRequestV1 = {
    question: question.trim(),
    language,
    session_id: sessionId,
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let errorMsg = `Server error (${response.status})`;
      try {
        const errorJson = await response.json();
        if (errorJson?.detail) {
          errorMsg = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch {
        // Fallback to text status
      }
      throw new ApiError(errorMsg, response.status);
    }

    const data: ChatResponseV1 = await response.json();
    return data;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : 'Network request failed';
    throw new ApiError(`Unable to connect to backend (${baseUrl}): ${message}`);
  }
}

export async function sendFeedback(
  traceId: string,
  rating: number, // 1 to 5
  comment?: string
): Promise<FeedbackResponseV1> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/v1/feedback`;

  const payload: FeedbackRequestV1 = {
    trace_id: traceId,
    rating,
    comment,
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new ApiError(`Feedback submission failed (${response.status})`, response.status);
    }

    const data: FeedbackResponseV1 = await response.json();
    return data;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : 'Network request failed';
    throw new ApiError(`Failed to submit feedback: ${message}`);
  }
}

export async function checkBackendHealth(): Promise<HealthResponseV1> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/v1/health`;

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: getHeaders(),
    });

    if (!response.ok) {
      throw new ApiError(`Health check failed (${response.status})`, response.status);
    }

    return await response.json();
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : 'Network request failed';
    throw new ApiError(`Health check error: ${message}`);
  }
}
