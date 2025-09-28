from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from api.domains.films.schemas import FilmSchema
from api.domains.starships.schemas import StarshipSchema


class CharacterSchema(BaseModel):
    id: int
    name: str
    height: Optional[str] = None
    mass: Optional[str] = None
    hair_color: Optional[str] = None
    skin_color: Optional[str] = None
    eye_color: Optional[str] = None
    birth_year: Optional[str] = None
    gender: Optional[str] = None
    created: datetime
    edited: datetime
    url: str
    films: list[FilmSchema] = []
    starships: list[StarshipSchema] = []

    class Config:
        from_attributes = True
