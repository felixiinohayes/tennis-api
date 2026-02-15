from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from datetime import datetime
from typing import List


class RequestModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Profile(RequestModel):
    id: str
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
    karma: int
    karma_status: str
    streak_count: int


class Player(BaseModel):
    user_id: str
    name: str
    initials: str
    elo: int


class CreateChallenge(RequestModel):
    match_id: str
    sport: str
    challenger_id: str
    recipient_id: str
    challenge_sent_at: datetime
    match_date: datetime


class AcceptChallenge(RequestModel):
    match_id: str
    challenge_accepted_at: datetime
    match_date: datetime | None = None


class SendChallenge(RequestModel):
    opponent_id: str
    sport: str


class ProposeResult(RequestModel):
    winner_id: str
    score: str


class MatchSummary(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )
    match_id: str
    sport: str
    status: str
    challenge_sent_at: datetime
    accepted_at: datetime | None = None
    completed_at: datetime | None = None
    challenger: Player
    challengee: Player
    proposed_result: str | None = None
    result_status: str | None = None
    winner: Player | None = None
    loser: Player | None = None
    proposed_by: Player | None = None


class ChallengesResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    challenges: List[MatchSummary]
    count: int
    has_challenges: bool


class MatchRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )
    match_id: str
    sport: str
    winner: Player
    loser: Player
    score: str
    completed_at: datetime


class LoginRequest(RequestModel):
    username: str
    password: str


class RegisterRequest(RequestModel):
    username: str
    password: str
    name: str
    email: str


class AuthResponse(RequestModel):
    token: str
    user_id: str
    username: str
