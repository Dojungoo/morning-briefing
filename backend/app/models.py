import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """App-local user, keyed on the platform's coders_id.

    coders.kr already knows who this visitor is (they signed in via
    `mcp.coders.kr/sso/login`); we keep a row in our own DB the first
    time we see them so app-local data can FK against a stable local
    UUID without joining out to the platform.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    coders_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    briefings: Mapped[list["Briefing"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )


class Briefing(Base):
    """One generated 'AI 보험·대체투자 모닝 브리핑' issue.

    Each issue bundles the four editorial sections (보험업계 / 대체투자·PF /
    금융지표 / 규제·리스크), a strip of market indicators, and the AI-written
    one-line insight ('오늘의 인사이트 한 줄'). The heavy lifting — crawl,
    summarise, compose — happens once at generation time and the result is
    cached here so every public read is a cheap DB hit.
    """

    __tablename__ = "briefings"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Generation lifecycle. A POST /generate persists a "pending" row and
    # returns immediately; a detached task crawls + summarises and flips this
    # to "ready" (or "failed"). The browser polls until it leaves "pending".
    # Synchronous generation would blow past the platform's ~50s request cap
    # (PLATFORM.md §5d). Existing rows default to "ready".
    status: Mapped[str] = mapped_column(
        sa.String(16), nullable=False, default="ready", server_default="ready"
    )
    # The trading/news day this issue covers (local KST date at generation).
    issue_date: Mapped[date] = mapped_column(sa.Date, nullable=False, index=True)
    # AI one-liner — the editorial hook at the top of the page.
    insight: Mapped[str] = mapped_column(sa.Text, nullable=False)
    # [{key,title,subtitle,items:[{headline,summary,source,url}]}] — 4 sections.
    sections: Mapped[list] = mapped_column(JSONB, nullable=False)
    # [{label,value,change,direction,note}] — market indicators strip.
    indicators: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # How many source headlines fed this issue (shown as a trust signal).
    source_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    # Which model produced the prose (e.g. claude-sonnet-4-6 or "fallback").
    model: Mapped[str] = mapped_column(sa.String(64), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), index=True
    )

    author: Mapped[User] = relationship(back_populates="briefings")
