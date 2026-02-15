from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.db import get_db
from app.models import MatchDB, MatchStatus
from app.schemas import MatchSummary, Player, ChallengesResponse

router = APIRouter(tags=["activity"])


def _match_to_summary(match: MatchDB) -> MatchSummary:
    """Helper function to convert MatchDB to MatchSummary"""
    return MatchSummary(
        match_id=match.id,
        sport=match.sport,
        status=match.status.value,
        challenge_sent_at=match.challenge_sent_at,
        accepted_at=match.accepted_at,
        completed_at=match.completed_at,
        challenger=Player(
            id=match.challenger_player.user_id,
            name=match.challenger_player.name,
            initials=match.challenger_player.initials,
            elo=match.challenger_player.elo,
        ),
        challengee=Player(
            id=match.challengee_player.user_id,
            name=match.challengee_player.name,
            initials=match.challengee_player.initials,
            elo=match.challengee_player.elo,
        ),
        proposed_result=match.proposed_result,
        result_status=match.result_status.value if match.result_status else None,
        winner=Player(
            id=match.winner_player.user_id,
            name=match.winner_player.name,
            initials=match.winner_player.initials,
            elo=match.winner_player.elo,
        )
        if match.winner_player
        else None,
        loser=Player(
            id=match.loser_player.user_id,
            name=match.loser_player.name,
            initials=match.loser_player.initials,
            elo=match.loser_player.elo,
        )
        if match.loser_player
        else None,
        proposed_by=Player(
            id=match.proposed_by_player.user_id,
            name=match.proposed_by_player.name,
            initials=match.proposed_by_player.initials,
            elo=match.proposed_by_player.elo,
        )
        if match.proposed_by_player
        else None,
    )


@router.get("/challenges/incoming", response_model=ChallengesResponse)
async def get_incoming_challenges(user_id: str, db: Session = Depends(get_db)):
    """Get incoming challenges (matches in PENDING where I am challengee)"""
    matches = (
        db.query(MatchDB)
        .options(
            joinedload(MatchDB.challenger_player),
            joinedload(MatchDB.challengee_player),
            joinedload(MatchDB.winner_player),
            joinedload(MatchDB.loser_player),
            joinedload(MatchDB.proposed_by_player),
        )
        .filter(
            MatchDB.status == MatchStatus.PENDING,
            MatchDB.challengee_id == user_id,
        )
        .order_by(MatchDB.challenge_sent_at.desc())
        .all()
    )

    challenges = [_match_to_summary(match) for match in matches]

    return ChallengesResponse(
        challenges=challenges,
        count=len(challenges),
        has_challenges=len(challenges) > 0,
    )


@router.get("/matches/active", response_model=List[MatchSummary])
async def get_active_matches(user_id: str, db: Session = Depends(get_db)):
    """Get active matches (matches in ACCEPTED, not completed/cancelled)"""
    matches = (
        db.query(MatchDB)
        .options(
            joinedload(MatchDB.challenger_player),
            joinedload(MatchDB.challengee_player),
            joinedload(MatchDB.winner_player),
            joinedload(MatchDB.loser_player),
            joinedload(MatchDB.proposed_by_player),
        )
        .filter(
            MatchDB.status == MatchStatus.ACCEPTED,
            (MatchDB.challenger_id == user_id) | (MatchDB.challengee_id == user_id),
        )
        .order_by(MatchDB.accepted_at.desc())
        .all()
    )

    return [_match_to_summary(match) for match in matches]


@router.get("/activity/recent", response_model=List[MatchSummary])
async def get_friends_activity(
    user_id: str, db: Session = Depends(get_db), limit: int = 10
):
    """Get friends activity (recent completed matches)"""
    matches = (
        db.query(MatchDB)
        .options(
            joinedload(MatchDB.challenger_player),
            joinedload(MatchDB.challengee_player),
            joinedload(MatchDB.winner_player),
            joinedload(MatchDB.loser_player),
            joinedload(MatchDB.proposed_by_player),
        )
        .filter(
            MatchDB.status == MatchStatus.COMPLETED,
            (MatchDB.challenger_id == user_id) | (MatchDB.challengee_id == user_id),
        )
        .order_by(MatchDB.completed_at.desc())
        .limit(limit)
        .all()
    )

    return [_match_to_summary(match) for match in matches]
