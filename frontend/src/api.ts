import { HealthInfo, Locale, SyntheticUser } from './types';

const API_BASE = 'http://localhost:8000';

export async function fetchHealth(): Promise<HealthInfo> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function sendChatMessage(message: string, locale: Locale): Promise<{
  response: string;
  provider: string;
  model: string;
}> {
  const res = await fetch(`${API_BASE}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, locale }),
  });
  if (!res.ok) throw new Error(`Chat request failed: ${res.statusText}`);
  return res.json();
}

export async function generateSyntheticUser(locale: Locale): Promise<SyntheticUser> {
  const res = await fetch(`${API_BASE}/api/v1/synthetic-user?locale=${locale}`);
  if (!res.ok) throw new Error('Failed to generate synthetic user');
  return res.json();
}

export async function bootstrapSyntheticData(locale: Locale, count: number = 2): Promise<{
  status: string;
  users_created: number;
  documents_indexed: number;
  chunks_indexed: number;
}> {
  const res = await fetch(`${API_BASE}/api/v1/bootstrap-synthetic`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ locale, count }),
  });
  if (!res.ok) throw new Error('Failed to bootstrap synthetic data');
  return res.json();
}

export async function clearKnowledgeBase(): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/documents`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to clear documents');
}
