from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import PlayerDB
from app.schemas import Player, Profile

router = APIRouter(prefix="/api/players", tags=["players"])

profile_felix = Profile(
    id="felix",
    name="Felix Iino Hayes",
    tags=["tennis"],
    elo=1500,
    elo_change=0,
    next_level=1000,
    progress_percent=50,
    wins=10,
    losses=10,
    win_rate=50,
    ranking=10,
    karma=100,
    karma_status="positive",
    streak_count=10,
)


@router.post("")
async def create_player(payload: Player, db: Session = Depends(get_db)):
    player = PlayerDB(
        id=payload.id,
        name=payload.name,
        initials=payload.initials,
        elo=payload.elo,
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return {"status": "success"}


@router.delete("/{user_id}")
async def delete_player(user_id: str, db: Session = Depends(get_db)):
    player = db.query(PlayerDB).filter(PlayerDB.user_id == user_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    db.delete(player)
    db.commit()
    return {"status": "deleted", "player_id": user_id}


@router.delete("")
async def delete_all_players(db: Session = Depends(get_db)):
    count = db.query(PlayerDB).delete()
    db.commit()
    return {"status": "deleted", "count": count}


@router.get("")
async def get_all_players(db: Session = Depends(get_db)):
    players = db.query(PlayerDB).all()
    return players


@router.get("/me")
async def get_profile():
    return profile_felix


@router.get("/{id}")
async def get_player(id: str, db: Session = Depends(get_db)):
    player = db.query(PlayerDB).filter(PlayerDB.id == id).first()
    return player
