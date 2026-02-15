from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db import get_db
from app.models import PlayerDB, MatchDB, MatchStatus
from app.schemas import SendChallenge

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


@router.post("")
async def send_challenge(
    payload: SendChallenge, user_id: str, db: Session = Depends(get_db)
):
    """Send a challenge (creates a match with status=PENDING)"""
    try:
        # Check if opponent exists
        opponent = (
            db.query(PlayerDB).filter(PlayerDB.user_id == payload.opponent_id).first()
        )
        if not opponent:
            raise HTTPException(status_code=404, detail="Opponent not found")

        # Check if challenger exists
        challenger = db.query(PlayerDB).filter(PlayerDB.user_id == user_id).first()
        if not challenger:
            raise HTTPException(status_code=404, detail="Challenger not found")

        # Generate match ID
        match_id = f"match-{user_id}-{payload.opponent_id}-{datetime.now(timezone.utc).timestamp()}"

        match = MatchDB(
            id=match_id,
            sport=payload.sport,
            challenger_id=user_id,
            challengee_id=payload.opponent_id,
            status=MatchStatus.PENDING,
            challenge_sent_at=datetime.now(timezone.utc),
        )
        db.add(match)
        db.commit()
        db.refresh(match)
        return {"status": "success", "match_id": match_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error creating challenge: {str(e)}"
        )


@router.post("/{match_id}/accept")
async def accept_challenge(match_id: str, user_id: str, db: Session = Depends(get_db)):
    """Accept a challenge (updates same match to status=ACCEPTED)"""
    match = db.query(MatchDB).filter(MatchDB.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if match.challengee_id != user_id:
        raise HTTPException(
            status_code=403, detail="You can only accept challenges sent to you"
        )

    if match.status != MatchStatus.PENDING:
        raise HTTPException(
            status_code=400, detail="Challenge is not in PENDING status"
        )

    match.status = MatchStatus.ACCEPTED
    match.accepted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(match)
    return {"status": "success"}


@router.post("/{match_id}/decline")
async def decline_challenge(match_id: str, user_id: str, db: Session = Depends(get_db)):
    """Decline a challenge (updates same match to status=CANCELLED)"""
    match = db.query(MatchDB).filter(MatchDB.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if match.challengee_id != user_id:
        raise HTTPException(
            status_code=403, detail="You can only decline challenges sent to you"
        )

    if match.status != MatchStatus.PENDING:
        raise HTTPException(
            status_code=400, detail="Challenge is not in PENDING status"
        )

    match.status = MatchStatus.CANCELLED
    db.commit()
    return {"status": "success"}


@router.post("/{match_id}/cancel")
async def cancel_challenge(match_id: str, user_id: str, db: Session = Depends(get_db)):
    """Cancel a challenge I sent (only while PENDING)"""
    match = db.query(MatchDB).filter(MatchDB.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if match.challenger_id != user_id:
        raise HTTPException(
            status_code=403, detail="You can only cancel challenges you sent"
        )

    if match.status != MatchStatus.PENDING:
        raise HTTPException(
            status_code=400, detail="Challenge is not in PENDING status"
        )

    match.status = MatchStatus.CANCELLED
    db.commit()
    return {"status": "success"}
