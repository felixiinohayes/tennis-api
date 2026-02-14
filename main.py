from datetime import datetime
from fastapi import FastAPI

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

default_start_time = datetime.now()


class Profile(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    name: str
    tags: list[str]
    elo: int
    elo_change: int
    next_level: int
    progress_percent: int
    wins: int
    losses: int
    win_rate: int
    ranking: int
    total_players: int
    karma: int
    karma_status: str
    streak_count: int


class Player(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    name: str
    initials: str
    elo: int
    elo_change: int
    is_winner: bool


class Event(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    id: int
    sport: str
    start_time: str
    time_ago: str
    is_your_match: bool
    winner: Player
    loser: Player
    score: str
    created_at: str


players = [
    Player(
        name="Martín González", initials="MG", elo=1547, elo_change=24, is_winner=True
    ),
    Player(
        name="Lucas Fernández", initials="LF", elo=1523, elo_change=-22, is_winner=False
    ),
]

profile = Profile(
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
    total_players=100,
    karma=100,
    karma_status="positive",
    streak_count=10,
)

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/api/profile/me")
async def get_profile():
    return {
        "data": profile.model_dump(by_alias=True),
    }


@app.get("/api/events/recent")
async def get_recent_events(limit: int = 10):

    events = [
        Event(
            id=i,
            sport="tennis",
            start_time=default_start_time.isoformat(),
            time_ago="Hace 2 horas",
            is_your_match=True,
            winner=players[0],
            loser=players[1],
            score="6-4, 6-3",
            created_at=default_start_time.isoformat(),
        )
        for i in range(limit)
    ]
    events_response = [event.model_dump(by_alias=True) for event in events]
    return {
        "data": events_response,
    }
