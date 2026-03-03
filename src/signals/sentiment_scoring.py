from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

import httpx

POSITIVE_WORDS = {
    "strong",
    "improved",
    "growth",
    "accelerated",
    "record",
    "gain",
    "beat",
    "positive",
    "upside",
    "expansion",
}

NEGATIVE_WORDS = {
    "weak",
    "decline",
    "slowed",
    "drop",
    "miss",
    "negative",
    "downside",
    "risk",
    "contraction",
    "loss",
}


class SentimentScorer(Protocol):
    def score(self, text: str) -> float | None:
        ...


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]{3,}", text.lower())


class LexiconSentimentScorer:
    def score(self, text: str) -> float | None:
        terms = _tokenize(text)
        if not terms:
            return 0.0
        pos = sum(1 for term in terms if term in POSITIVE_WORDS)
        neg = sum(1 for term in terms if term in NEGATIVE_WORDS)
        return (pos - neg) / len(terms)


class OpenAISentimentScorer:
    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        base_url: str,
        timeout_seconds: int,
    ):
        self.api_key = api_key or ""
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def score(self, text: str) -> float | None:
        if not self.api_key:
            return None
        system_prompt = (
            "You are a financial sentiment classifier. "
            "Return JSON only with numeric field `score` in [-1, 1]."
        )
        user_prompt = (
            "Score the sentiment of this financial text in [-1,1]. "
            "Negative is bearish, positive is bullish.\n\n"
            f"Text:\n{text[:3000]}"
        )
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        url = f"{self.base_url}/chat/completions"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            body = resp.json()
            choices = body.get("choices") or []
            if not choices:
                return None
            content = choices[0].get("message", {}).get("content")
            if not isinstance(content, str):
                return None
            parsed = json.loads(content)
            score = parsed.get("score")
            if not isinstance(score, int | float):
                return None
            return max(-1.0, min(1.0, float(score)))
        except Exception:
            return None


@dataclass
class SentimentScore:
    value: float
    provider_used: str


def score_with_fallback(
    text: str,
    *,
    primary_provider: str,
    openai_api_key: str | None,
    openai_model: str,
    openai_base_url: str,
    openai_timeout_seconds: int,
) -> SentimentScore:
    lexicon = LexiconSentimentScorer()
    normalized = primary_provider.strip().lower()
    if normalized == "openai":
        model_scorer = OpenAISentimentScorer(
            api_key=openai_api_key,
            model=openai_model,
            base_url=openai_base_url,
            timeout_seconds=openai_timeout_seconds,
        )
        model_score = model_scorer.score(text)
        if model_score is not None:
            return SentimentScore(value=model_score, provider_used="openai")
        return SentimentScore(value=lexicon.score(text) or 0.0, provider_used="lexicon-fallback")
    return SentimentScore(value=lexicon.score(text) or 0.0, provider_used="lexicon")
