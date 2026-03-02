from datetime import datetime

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str
    password: str


class TradeOut(BaseModel):
    ticket: int
    symbol: str
    trade_type: str
    volume: float
    open_price: float
    close_price: float
    stop_loss: float
    take_profit: float
    profit: float
    open_time: datetime
    close_time: datetime
    tag: str | None
    notes: str | None

    class Config:
        from_attributes = True
