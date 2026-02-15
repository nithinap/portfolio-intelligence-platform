from __future__ import annotations

from src.common.db import Base, SessionLocal, engine
from src.core.models import Portfolio, Position, Transaction


def seed() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        exists = session.query(Portfolio).filter(Portfolio.name == "demo-portfolio").first()
        if exists:
            return

        portfolio = Portfolio(name="demo-portfolio")
        session.add(portfolio)
        session.flush()

        session.add_all(
            [
                Position(portfolio_id=portfolio.id, ticker="AAPL", quantity=10, avg_cost=170.0),
                Position(portfolio_id=portfolio.id, ticker="MSFT", quantity=6, avg_cost=330.0),
                Position(portfolio_id=portfolio.id, ticker="NVDA", quantity=4, avg_cost=820.0),
            ]
        )
        session.add(
            Transaction(
                portfolio_id=portfolio.id,
                ticker="AAPL",
                side="BUY",
                quantity=10,
                price=170.0,
            )
        )
        session.commit()


if __name__ == "__main__":
    seed()
