from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class FilmSchema(BaseModel):
    id: int
    title: str
    episode_id: int
    opening_crawl: Optional[str] = None
    director: Optional[str] = None
    producer: Optional[str] = None
    release_date: date
    created: datetime
    edited: datetime
    url: str

    class Config:
        from_attributes = True
