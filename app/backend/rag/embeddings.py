"""Multilingual embedding generator supporting English, Hindi, and Telugu."""

from __future__ import annotations

from backend.providers.base import BaseLLMProvider

# Cross-lingual vocabulary mappings (Hindi & Telugu -> English financial concepts)
CROSS_LINGUAL_MAP: dict[str, list[str]] = {
    # UPI
    "यूपीआई": ["upi", "payments", "pin"],
    "पिन": ["pin", "secret", "password"],
    "యూపీఐ": ["upi", "payments", "pin"],
    "పిన్": ["pin", "secret", "password"],
    "క్యూఆర్": ["qr code", "scan"],
    "క్యూఆర్ కోడ్": ["qr code", "scan"],
    # KYC
    "केवाईसी": ["kyc", "identification", "documents", "aadhaar", "pan"],
    "दस्तावेज": ["documents", "ovd", "records"],
    "కేవైసీ": ["kyc", "identification", "documents", "aadhaar", "pan"],
    "దస్తావేజులు": ["documents", "proof"],
    "పత్రాలు": ["documents", "records"],
    # Credit Score
    "क्रेडिट स्कोर": ["credit score", "cibil", "rating"],
    "सिबिल": ["cibil", "credit score", "bureau"],
    "క్రెడిట్ స్కోర్": ["credit score", "cibil", "rating"],
    "సిబిల్": ["cibil", "credit score", "bureau"],
    # SIP & Mutual Funds
    "एसआईपी": ["sip", "mutual fund", "investing"],
    "म्यूचुअल फंड": ["mutual fund", "nav", "equity"],
    "మ్యూచువల్ ఫండ్": ["mutual fund", "sip", "nav"],
    "పెట్టుబడి": ["investment", "mutual fund", "sip"],
    # Fraud & Scams
    "धोखाधड़ी": ["fraud", "scam", "cybercrime", "helpline"],
    "स्कैम": ["scam", "fraud"],
    "మోసం": ["fraud", "scam", "cheating"],
    "సైబర్": ["cyber", "crime", "helpline 1930"],
    # Budgeting & Emergency Fund
    "बजट": ["budget", "50 30 20", "expenses"],
    "आपातकालीन": ["emergency fund", "liquid fund", "savings"],
    "బడ్జెట్": ["budget", "expenses", "50 30 20"],
    "అత్యవసర నిధి": ["emergency fund", "liquid fund", "savings buffer"],
    # Loans & EMI
    "लोन": ["loan", "emi", "interest", "borrowing"],
    "ईएमआई": ["emi", "installment", "amortization"],
    "కిస్తీ": ["installment", "emi"],
    "రుణం": ["loan", "borrowing", "emi"],
    # Insurance
    "बीमा": ["insurance", "term insurance", "cover"],
    "భీమా": ["insurance", "term insurance", "coverage"],
    "ఇన్సూరెన్స్": ["insurance", "policy"],
}


def normalize_multilingual_text(text: str) -> str:
    """Enrich non-English questions with English concept tokens for cross-lingual alignment."""
    enriched = [text]
    text_lower = text.lower()
    for source_term, target_terms in CROSS_LINGUAL_MAP.items():
        if source_term.lower() in text_lower:
            enriched.extend(target_terms)
    return " ".join(enriched)


class MultilingualEmbedder:
    """Coordinates embedding generation using the active LLM provider."""

    def __init__(self, provider: BaseLLMProvider) -> None:
        self.provider = provider

    def embed_query(self, text: str, language: str = "auto") -> list[float]:
        """Embed a search query with multilingual concept enhancement."""
        normalized = normalize_multilingual_text(text)
        return self.provider.embed(normalized)

    def embed_document(self, text: str) -> list[float]:
        """Embed document content."""
        return self.provider.embed(text)
