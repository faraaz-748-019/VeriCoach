import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import * as apiService from '../services/api';
import type { ChatResponseV1 } from '../types/api';

vi.mock('../services/api', () => ({
  sendChatMessage: vi.fn(),
  sendFeedback: vi.fn(),
  checkBackendHealth: vi.fn(),
}));

describe('VeriCoach Frontend UI & Interaction Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders chat window, header, and language selector with accessible test IDs', () => {
    render(<App />);

    expect(screen.getByTestId('chat-window')).toBeInTheDocument();
    expect(screen.getByTestId('app-header')).toBeInTheDocument();
    expect(screen.getByTestId('app-title')).toHaveTextContent('VeriCoach');

    const languageSelect = screen.getByTestId('language-select');
    expect(languageSelect).toBeInTheDocument();
    expect(languageSelect).toHaveAttribute('data-accessibility-id', 'language-select');
    expect(screen.getByTestId('lang-option-en')).toBeInTheDocument();
    expect(screen.getByTestId('lang-option-hi')).toBeInTheDocument();
    expect(screen.getByTestId('lang-option-te')).toBeInTheDocument();

    expect(screen.getByTestId('chat-input')).toBeInTheDocument();
    expect(screen.getByTestId('send-button')).toBeInTheDocument();
  });

  it('switches languages correctly (English, Hindi, Telugu)', () => {
    render(<App />);

    const select = screen.getByTestId('language-select') as HTMLSelectElement;

    // Switch to Hindi
    fireEvent.change(select, { target: { value: 'hi' } });
    expect(screen.getByTestId('app-title')).toHaveTextContent('वेरीकोच');

    // Switch to Telugu
    fireEvent.change(select, { target: { value: 'te' } });
    expect(screen.getByTestId('app-title')).toHaveTextContent('వెరికోచ్');

    // Switch back to English
    fireEvent.change(select, { target: { value: 'en' } });
    expect(screen.getByTestId('app-title')).toHaveTextContent('VeriCoach');
  });

  it('sends a chat question, shows loading state, and renders assistant response with citations and feedback buttons', async () => {
    const mockChatResponse: ChatResponseV1 = {
      answer: 'No, you never need to enter your UPI PIN to receive money. [MOCK]',
      language: 'en',
      refused: false,
      refusal_reason: null,
      trace_id: 'test-trace-123',
      sources: [
        {
          doc_id: 'upi_pin_rules',
          title: 'UPI PIN Usage Rules and Receiving Money',
          snippet: 'A UPI PIN is required ONLY when sending money or checking your balance.',
          score: 0.94,
        },
      ],
    };

    vi.mocked(apiService.sendChatMessage).mockResolvedValueOnce(mockChatResponse);

    render(<App />);

    const input = screen.getByTestId('chat-input');
    const sendBtn = screen.getByTestId('send-button');

    fireEvent.change(input, { target: { value: 'Do I need UPI PIN to receive money?' } });
    fireEvent.click(sendBtn);

    // User message should appear immediately
    expect(screen.getByTestId('message-user')).toHaveTextContent('Do I need UPI PIN to receive money?');

    // Wait for assistant response
    await waitFor(() => {
      expect(screen.getByTestId('message-assistant')).toBeInTheDocument();
    });

    expect(screen.getByTestId('message-assistant')).toHaveTextContent(
      'No, you never need to enter your UPI PIN to receive money.'
    );

    // Verify citations toggle button
    const citationsToggle = screen.getByTestId('citations-toggle');
    expect(citationsToggle).toBeInTheDocument();
    expect(citationsToggle).toHaveAttribute('data-accessibility-id', 'citations-toggle');

    // Toggle citations panel open
    fireEvent.click(citationsToggle);
    expect(screen.getByTestId('citations-panel')).toBeInTheDocument();
    expect(screen.getByTestId('citation-item')).toBeInTheDocument();
    expect(screen.getByTestId('citation-title')).toHaveTextContent('UPI PIN Usage Rules and Receiving Money');
    expect(screen.getByTestId('citation-score')).toHaveTextContent('Match Score: 94%');

    // Verify thumbs up/down feedback buttons
    const thumbsUp = screen.getByTestId('feedback-thumbs-up');
    const thumbsDown = screen.getByTestId('feedback-thumbs-down');
    expect(thumbsUp).toHaveAttribute('data-accessibility-id', 'feedback-thumbs-up');
    expect(thumbsDown).toHaveAttribute('data-accessibility-id', 'feedback-thumbs-down');

    // Click thumbs up
    vi.mocked(apiService.sendFeedback).mockResolvedValueOnce({
      status: 'feedback_recorded',
      trace_id: 'test-trace-123',
    });

    fireEvent.click(thumbsUp);

    await waitFor(() => {
      expect(apiService.sendFeedback).toHaveBeenCalledWith('test-trace-123', 5);
      expect(screen.getByTestId('feedback-status')).toHaveTextContent('Thank you for your feedback!');
    });
  });

  it('displays error banner and allows retry when API request fails', async () => {
    vi.mocked(apiService.sendChatMessage).mockRejectedValueOnce(
      new Error('Unable to connect to backend server')
    );

    render(<App />);

    const input = screen.getByTestId('chat-input');
    fireEvent.change(input, { target: { value: 'Test query that fails' } });
    fireEvent.click(screen.getByTestId('send-button'));

    await waitFor(() => {
      expect(screen.getByTestId('error-banner')).toBeInTheDocument();
    });

    expect(screen.getByTestId('error-banner')).toHaveTextContent('Unable to connect to backend server');

    // Test dismiss
    const dismissBtn = screen.getByTestId('error-banner-dismiss');
    fireEvent.click(dismissBtn);

    expect(screen.queryByTestId('error-banner')).not.toBeInTheDocument();
  });

  it('displays offline banner when network offline event fires', () => {
    render(<App />);

    expect(screen.queryByTestId('offline-banner')).not.toBeInTheDocument();

    // Trigger offline event
    fireEvent(window, new Event('offline'));
    expect(screen.getByTestId('offline-banner')).toBeInTheDocument();
    expect(screen.getByTestId('offline-banner')).toHaveTextContent('You are currently offline');

    // Trigger online event
    fireEvent(window, new Event('online'));
    expect(screen.queryByTestId('offline-banner')).not.toBeInTheDocument();
  });

  it('allows opening settings modal and configuring backend URL', async () => {
    vi.mocked(apiService.checkBackendHealth).mockResolvedValueOnce({
      status: 'healthy',
      version: '1.0.0',
      provider: 'mock',
      documents_indexed: 30,
    });

    render(<App />);

    const settingsBtn = screen.getByTestId('settings-button');
    fireEvent.click(settingsBtn);

    expect(screen.getByTestId('settings-modal')).toBeInTheDocument();
    expect(screen.getByTestId('settings-backend-url-input')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('backend-health-status')).toBeInTheDocument();
    });

    const closeBtn = screen.getByTestId('settings-close-button');
    fireEvent.click(closeBtn);

    expect(screen.queryByTestId('settings-modal')).not.toBeInTheDocument();
  });
});
