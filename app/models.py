from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Enum, String, Integer, DateTime, ForeignKey
from datetime import datetime
from enum import Enum as PyEnum


class Base(DeclarativeBase):
    pass


class PlayerDB(Base):
    __tablename__ = "players"

    user_id: Mapped[str] = mapped_column(
        String(80), ForeignKey("users.id"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    initials: Mapped[str] = mapped_column(String(80), nullable=False)
    elo: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)

    wins = relationship(
        "MatchDB", foreign_keys="MatchDB.winner_id", back_populates="winner_player"
    )
    losses = relationship(
        "MatchDB", foreign_keys="MatchDB.loser_id", back_populates="loser_player"
    )
    challenges_sent = relationship(
        "MatchDB",
        foreign_keys="MatchDB.challenger_id",
        back_populates="challenger_player",
    )
    challenges_received = relationship(
        "MatchDB",
        foreign_keys="MatchDB.challengee_id",
        back_populates="challengee_player",
    )


class MatchStatus(PyEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ResultStatus(PyEnum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class MatchDB(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    sport: Mapped[str] = mapped_column(String(80), nullable=False)

    challenge_sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), nullable=False)

    # participants (always known)
    challenger_id: Mapped[str] = mapped_column(
        String(80), ForeignKey("players.user_id"), nullable=False
    )
    challengee_id: Mapped[str] = mapped_column(
        String(80), ForeignKey("players.user_id"), nullable=False
    )

    # proposed result (optional until submitted)
    proposed_result: Mapped[str | None] = mapped_column(String(80), nullable=True)
    result_status: Mapped[ResultStatus | None] = mapped_column(
        Enum(ResultStatus), nullable=True
    )
    proposed_by_id: Mapped[str | None] = mapped_column(
        String(80), ForeignKey("players.user_id"), nullable=True
    )

    # final result (only after accepted)
    winner_id: Mapped[str | None] = mapped_column(
        String(80), ForeignKey("players.user_id"), nullable=True
    )
    loser_id: Mapped[str | None] = mapped_column(
        String(80), ForeignKey("players.user_id"), nullable=True
    )

    # Relationships
    challenger_player = relationship(
        "PlayerDB", foreign_keys=[challenger_id], back_populates="challenges_sent"
    )
    challengee_player = relationship(
        "PlayerDB", foreign_keys=[challengee_id], back_populates="challenges_received"
    )
    winner_player = relationship(
        "PlayerDB", foreign_keys=[winner_id], back_populates="wins"
    )
    loser_player = relationship(
        "PlayerDB", foreign_keys=[loser_id], back_populates="losses"
    )
    proposed_by_player = relationship("PlayerDB", foreign_keys=[proposed_by_id])


class UserDB(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(80), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(80), nullable=False)

    player = relationship("PlayerDB", uselist=False)
