from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

import httpx


@dataclass
class SourceContext:
    chunk_id: str
    source: str
    ticker: str | None
    published_at: datetime | None
    excerpt: str


class AnswerGenerator(Protocol):
    def generate(self, question: str, contexts: list[SourceContext]) -> str | None:
        ...


class DeterministicAnswerGenerator:
    def generate(self, question: str, contexts: list[SourceContext]) -> str | None:
        del question
        summary_lines = [f"- [{ctx.chunk_id}] {ctx.excerpt}" for ctx in contexts[:3]]
        if not summary_lines:
            return "No grounded evidence was available to answer this question."
        return "Grounded summary from retrieved documents:\n" + "\n".join(summary_lines)


class OpenAIAnswerGenerator:
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

    def generate(self, question: str, contexts: list[SourceContext]) -> str | None:
        if not self.api_key:
            return None
        if not contexts:
            return None

        context_block = "\n".join(
            [
                (
                    f"[{ctx.chunk_id}] source={ctx.source} ticker={ctx.ticker or 'N/A'} "
                    f"published_at={ctx.published_at.isoformat() if ctx.published_at else 'N/A'} "
                    f"excerpt={ctx.excerpt}"
                )
                for ctx in contexts
            ]
        )
        system_prompt = (
            "You are a grounded financial QA assistant. "
            "Answer only using the provided evidence excerpts. "
            "If evidence is insufficient, say so clearly. "
            "Cite chunk IDs in square brackets for each claim."
        )
        user_prompt = (
            f"Question: {question}\n\n"
            f"Evidence:\n{context_block}\n\n"
            "Return a concise answer with citations."
        )
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        url = f"{self.base_url}/chat/completions"

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
            choices = body.get("choices") or []
            if not choices:
                return None
            message = choices[0].get("message", {})
            content = message.get("content")
            if not isinstance(content, str):
                return None
            return content.strip()
        except Exception:
            return None


def get_answer_generator(
    provider_name: str,
    *,
    openai_api_key: str | None = None,
    openai_model: str = "gpt-4o-mini",
    openai_base_url: str = "https://api.openai.com/v1",
    openai_timeout_seconds: int = 20,
) -> AnswerGenerator:
    normalized = provider_name.strip().lower()
    if normalized == "openai":
        return OpenAIAnswerGenerator(
            api_key=openai_api_key,
            model=openai_model,
            base_url=openai_base_url,
            timeout_seconds=openai_timeout_seconds,
        )
    return DeterministicAnswerGenerator()
