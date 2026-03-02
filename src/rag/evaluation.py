from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from src.rag.qa import answer_question


@dataclass
class QaEvalCase:
    question: str
    top_k: int = 5
    ticker: str | None = None
    source: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    min_citations: int = 1
    min_confidence: float = 0.2


@dataclass
class QaEvalCaseResult:
    question: str
    confidence: float
    citation_count: int
    passed: bool
    reasons: list[str]


@dataclass
class QaEvalSummary:
    total_cases: int
    pass_rate: float
    citation_coverage: float
    avg_confidence: float
    cases: list[QaEvalCaseResult]


def evaluate_qa_cases(session: Session, cases: list[QaEvalCase]) -> QaEvalSummary:
    if not cases:
        return QaEvalSummary(
            total_cases=0,
            pass_rate=0.0,
            citation_coverage=0.0,
            avg_confidence=0.0,
            cases=[],
        )

    case_results: list[QaEvalCaseResult] = []
    pass_count = 0
    with_citations = 0
    confidence_sum = 0.0

    for case in cases:
        qa = answer_question(
            session,
            case.question,
            top_k=case.top_k,
            ticker=case.ticker,
            source=case.source,
            date_from=case.date_from,
            date_to=case.date_to,
        )
        citation_count = len(qa.citations)
        confidence = qa.confidence
        with_citations += int(citation_count > 0)
        confidence_sum += confidence

        reasons: list[str] = []
        if citation_count < case.min_citations:
            reasons.append(
                f"citations_below_min:{citation_count}<{case.min_citations}"
            )
        if confidence < case.min_confidence:
            reasons.append(
                f"confidence_below_min:{confidence:.3f}<{case.min_confidence:.3f}"
            )
        passed = len(reasons) == 0
        pass_count += int(passed)
        case_results.append(
            QaEvalCaseResult(
                question=case.question,
                confidence=confidence,
                citation_count=citation_count,
                passed=passed,
                reasons=reasons,
            )
        )

    total = len(cases)
    return QaEvalSummary(
        total_cases=total,
        pass_rate=round(pass_count / total, 3),
        citation_coverage=round(with_citations / total, 3),
        avg_confidence=round(confidence_sum / total, 3),
        cases=case_results,
    )
