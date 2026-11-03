"""Deterministic MOCK LLM provider — zero network, answers from retrieved context."""

from __future__ import annotations

import hashlib
import math
import re

from backend.providers.base import BaseLLMProvider, LLMResponse

_EMBEDDING_DIM = 384

# Financial synonyms and cross-lingual concept dictionary for deterministic mock embeddings
_CROSS_LINGUAL_MOCK_MAP: dict[str, list[str]] = {
    # Hindi
    "यूपीआई": ["upi", "pin"],
    "पिन": ["pin", "upi"],
    "पैसे": ["money", "funds"],
    "प्राप्त": ["receive", "receiving"],
    "केवाईसी": ["kyc", "documents", "aadhaar", "pan"],
    "दस्तावेज": ["documents", "ovd"],
    "क्रेडिट": ["credit", "score", "cibil"],
    "स्कोर": ["score", "cibil"],
    "सिबिल": ["cibil", "score"],
    "एसआईपी": ["sip", "mutual", "fund"],
    "म्यूचुअल": ["mutual", "fund"],
    "फंड": ["fund", "mutual"],
    "धोखाधड़ी": ["fraud", "scam"],
    "बजट": ["budget", "50 30 20"],
    "आपातकालीन": ["emergency", "fund"],
    "लोन": ["loan", "emi"],
    "ईएमआई": ["emi", "installment"],
    "बीमा": ["insurance", "term"],
    # Telugu
    "యూపీఐ": ["upi", "pin"],
    "పిన్": ["pin", "upi"],
    "డబ్బులు": ["money", "funds", "receive"],
    "తీసుకోవడానికి": ["receive", "receiving"],
    "రావడానికి": ["receive", "receiving"],
    "ఖాతా": ["account", "bank"],
    "ఖాతాలో": ["account", "bank"],
    "కేవైసీ": ["kyc", "documents", "aadhaar", "pan"],
    "దస్తావేజులు": ["documents", "ovd"],
    "క్రెడిట్": ["credit", "score", "cibil"],
    "స్కోర్": ["score", "cibil"],
    "సిబిల్": ["cibil", "score"],
    "మ్యూచువల్": ["mutual", "fund"],
    "ఫండ్": ["fund", "mutual"],
    "పెట్టుబడి": ["investment", "sip", "fund"],
    "మోసం": ["fraud", "scam"],
    "బడ్జెట్": ["budget", "50 30 20"],
    "అత్యవసర": ["emergency", "fund"],
    "నిధి": ["fund", "emergency"],
    "రుణం": ["loan", "emi"],
    "కిస్తీ": ["installment", "emi"],
    "ఈఎంఐ": ["emi", "installment"],
    "భీమా": ["insurance", "term"],
}


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic provider that requires zero network.
    Answers strictly and deterministically from retrieved context provided in the prompt.
    """

    MODEL = "mock-deterministic-rag-v1"

    def complete(self, prompt: str, **kwargs: object) -> LLMResponse:
        # Check if prompt contains retrieved context documents
        context_match = re.search(
            r"Retrieved Context Documents:\s*(.*?)(?:\n\nUser Question:|\Z)",
            prompt,
            re.DOTALL,
        )
        context_block = context_match.group(1).strip() if context_match else ""

        if not context_block:
            legacy_match = re.search(
                r"Context from the user's documents:\s*(.*?)(?:\n\nUser question:|\Z)",
                prompt,
                re.DOTALL,
            )
            context_block = legacy_match.group(1).strip() if legacy_match else ""

        if (
            not context_block
            or context_block == "[No relevant documents found in knowledge base]"
        ):
            answer = (
                "I could not find information about that in the knowledge base. "
                "I can only provide educational information based on verified documents."
            )
        else:
            lines = [
                re.sub(r"^[\s\-*0-9.]+", "", line).strip()
                for line in context_block.split("\n")
                if line.strip()
            ]
            substantive_lines = [
                line
                for line in lines
                if len(line) > 20 and not line.startswith("[Doc ")
            ]

            if substantive_lines:
                primary_fact = substantive_lines[0]
                answer = f"[MOCK] Based on retrieved context: {primary_fact}"
            else:
                answer = f"[MOCK] Answer based on context: {lines[0] if lines else 'Information verified.'}"

        prompt_words = len(prompt.split())
        completion_words = len(answer.split())

        return LLMResponse(
            text=answer,
            provider=self.provider_name,
            model=self.MODEL,
            prompt_tokens=prompt_words,
            completion_tokens=completion_words,
        )

    def embed(self, text: str) -> list[float]:
        """
        Deterministic, cross-lingual semantic embedding via term hashing.
        Words, subwords, and cross-lingual concepts map to vector dimensions,
        ensuring matching concepts yield high cosine similarity.
        """
        vector = [0.0] * _EMBEDDING_DIM
        cleaned = text.lower()

        # Extract words/tokens
        words = re.findall(r"[\w]+", cleaned)
        expanded_tokens: list[str] = list(words)

        # Cross-lingual expansion
        for token in words:
            if token in _CROSS_LINGUAL_MOCK_MAP:
                expanded_tokens.extend(_CROSS_LINGUAL_MOCK_MAP[token])

        # Also check substring match for Indic script terms
        for indic_term, english_terms in _CROSS_LINGUAL_MOCK_MAP.items():
            if indic_term in cleaned and indic_term not in words:
                expanded_tokens.extend(english_terms)

        for token in expanded_tokens:
            token_bytes = token.encode("utf-8")
            h = int(hashlib.sha256(token_bytes).hexdigest(), 16)
            idx = h % _EMBEDDING_DIM
            sign = 1.0 if ((h >> 16) & 1) == 0 else -1.0
            vector[idx] += sign * (1.0 + (len(token) / 10.0))

        # Bigrams for phrase matching
        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            h = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16)
            idx = h % _EMBEDDING_DIM
            vector[idx] += 1.5

        # Normalize to unit length
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 1e-9:
            return [v / norm for v in vector]

        # Fallback if text has no tokens
        return [1.0 / math.sqrt(_EMBEDDING_DIM)] * _EMBEDDING_DIM

    @property
    def provider_name(self) -> str:
        return "mock"
