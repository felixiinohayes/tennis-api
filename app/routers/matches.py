from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone
from app.db import get_db
from app.models import PlayerDB, MatchDB, MatchStatus, ResultStatus
from app.schemas import CreateChallenge, MatchRead, ProposeResult, Player

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.post("")
async def create_challenge(payload: CreateChallenge, db: Session = Depends(get_db)):
    try:
        # Check if players exist
        challenger = (
            db.query(PlayerDB).filter(PlayerDB.user_id == payload.challenger_id).first()
        )
        recipient = (
            db.query(PlayerDB).filter(PlayerDB.user_id == payload.recipient_id).first()
        )

        if not challenger:
            raise HTTPException(
                status_code=404,
                detail=f"Challenger player '{payload.challenger_id}' not found",
            )
        if not recipient:
            raise HTTPException(
                status_code=404,
                detail=f"Recipient player '{payload.recipient_id}' not found",
            )

        match = MatchDB(
            id=payload.match_id,
            sport=payload.sport,
            challenger_id=payload.challenger_id,
            challengee_id=payload.recipient_id,
            challenge_sent_at=payload.challenge_sent_at,
            status=MatchStatus.PENDING,
        )
        db.add(match)
        db.commit()
        db.refresh(match)
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating match: {str(e)}")


@router.delete("/{id}")
async def delete_match(id: str, db: Session = Depends(get_db)):
    match = db.query(MatchDB).filter(MatchDB.id == id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    db.delete(match)
    db.commit()
    return {"status": "deleted", "match_id": id}


@router.delete("")
async def delete_all_matches(db: Session = Depends(get_db)):
    count = db.query(MatchDB).delete()
    db.commit()
    return {"status": "deleted", "count": count}


@router.get("/recent", response_model=List[MatchRead])
async def get_recent_matches(db: Session = Depends(get_db), limit: int = 10):
    try:
        matches = (
            db.query(MatchDB)
            .options(
                joinedload(MatchDB.winner_player), joinedload(MatchDB.loser_player)
            )
            .filter(MatchDB.completed_at.isnot(None))
            .order_by(MatchDB.completed_at.desc())
            .limit(limit)
            .all()
        )

        matches_response = []
        for match_db in matches:
            # Check if relationships are loaded
            if not match_db.winner_player or not match_db.loser_player:
                # If relationships aren't loaded, skip this match
                continue

            # Skip if completed_at is None (defensive check, though filter should prevent this)
            if match_db.completed_at is None:
                continue

            match_response = MatchRead(
                match_id=match_db.id,
                sport=match_db.sport,
                winner=Player(
                    user_id=match_db.winner_player.user_id,
                    name=match_db.winner_player.name,
                    initials=match_db.winner_player.initials,
                    elo=match_db.winner_player.elo,
                ),
                loser=Player(
                    user_id=match_db.loser_player.user_id,
                    name=match_db.loser_player.name,
                    initials=match_db.loser_player.initials,
                    elo=match_db.loser_player.elo,
                ),
                score=match_db.proposed_result or "",
                completed_at=match_db.completed_at,
            )
            matches_response.append(match_response)

        return matches_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching matches: {str(e)}")


@router.post("/{match_id}/result")
async def propose_result(
    match_id: str, payload: ProposeResult, user_id: str, db: Session = Depends(get_db)
):
    """Propose result (updates same match, sets result_status=PROPOSED)"""
    match = db.query(MatchDB).filter(MatchDB.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    if match.status != MatchStatus.ACCEPTED:
        raise HTTPException(
            status_code=400, detail="Match must be ACCEPTED to propose a result"
        )

    if match.challenger_id != user_id and match.challengee_id != user_id:
        raise HTTPException(
            status_code=403, detail="You must be a participant to propose a result"
        )

    if payload.winner_id not in [match.challenger_id, match.challengee_id]:
        raise HTTPException(
            status_code=400, detail="Winner must be one of the participants"
        )

    loser_id = (
        match.challengee_id
        if payload.winner_id == match.challenger_id
        else match.challenger_id
    )

    match.proposed_result = payload.score
    match.proposed_by_id = user_id
    match.result_status = ResultStatus.PROPOSED
    match.winner_id = payload.winner_id
    match.loser_id = loser_id

    db.commit()
    db.refresh(match)
    return {"status": "success"}


@router.post("/{match_id}/result/confirm")
async def confirm_result(match_id: str, user_id: str, db: Session = Depends(get_db)):
    """Confirm result (finalizes match: COMPLETED + result_status=ACCEPTED, sets winner/loser, updates ELO)"""
    match = (
        db.query(MatchDB)
        .options(
            joinedload(MatchDB.winner_player),
            joinedload(MatchDB.loser_player),
        )
        .filter(MatchDB.id == match_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    if match.status != MatchStatus.ACCEPTED:
        raise HTTPException(
            status_code=400, detail="Match must be ACCEPTED to confirm a result"
        )

    if match.result_status != ResultStatus.PROPOSED:
        raise HTTPException(status_code=400, detail="No proposed result to confirm")

    # Can only confirm if you're the other participant (not the one who proposed)
    if match.proposed_by_id == user_id:
        raise HTTPException(
            status_code=400, detail="You cannot confirm your own proposed result"
        )

    if match.challenger_id != user_id and match.challengee_id != user_id:
        raise HTTPException(
            status_code=403, detail="You must be a participant to confirm a result"
        )

    # Update ELO (simple implementation - adjust as needed)
    winner = match.winner_player
    loser = match.loser_player

    # Simple ELO calculation (you can make this more sophisticated)
    expected_winner = 1 / (1 + 10 ** ((loser.elo - winner.elo) / 400))
    expected_loser = 1 - expected_winner

    k_factor = 32
    winner.elo = int(winner.elo + k_factor * (1 - expected_winner))
    loser.elo = int(loser.elo + k_factor * (0 - expected_loser))

    # Finalize match
    match.status = MatchStatus.COMPLETED
    match.result_status = ResultStatus.ACCEPTED
    match.completed_at = datetime.now(timezone.utc)

    db.commit()
    return {"status": "success"}


@router.post("/{match_id}/result/reject")
async def reject_result(match_id: str, user_id: str, db: Session = Depends(get_db)):
    """Reject result (sets result_status=REJECTED and clears proposed result)"""
    match = db.query(MatchDB).filter(MatchDB.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    if match.status != MatchStatus.ACCEPTED:
        raise HTTPException(
            status_code=400, detail="Match must be ACCEPTED to reject a result"
        )

    if match.result_status != ResultStatus.PROPOSED:
        raise HTTPException(status_code=400, detail="No proposed result to reject")

    # Can only reject if you're the other participant (not the one who proposed)
    if match.proposed_by_id == user_id:
        raise HTTPException(
            status_code=400, detail="You cannot reject your own proposed result"
        )

    if match.challenger_id != user_id and match.challengee_id != user_id:
        raise HTTPException(
            status_code=403, detail="You must be a participant to reject a result"
        )

    # Reject and clear proposed result
    match.result_status = ResultStatus.REJECTED
    match.proposed_result = None
    match.proposed_by_id = None
    match.winner_id = None
    match.loser_id = None

    db.commit()
    return {"status": "success"}
