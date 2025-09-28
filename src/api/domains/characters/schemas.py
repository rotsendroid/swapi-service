from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CharacterRelationSchema(BaseModel):
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

    class Config:
        from_attributes = True


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
    films: list[FilmRelationSchema] = []
    starships: list[StarshipRelationSchema] = []

    class Config:
        from_attributes = True


# Import here to avoid circular imports
from api.domains.films.schemas import FilmRelationSchema  # noqa: E402
from api.domains.starships.schemas import StarshipRelationSchema  # noqa: E402

# Rebuild models after all schemas are imported
CharacterSchema.model_rebuild()
