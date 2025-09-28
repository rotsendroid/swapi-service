from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StarshipSchema(BaseModel):
    id: int
    name: str
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    cost_in_credits: Optional[str] = None
    length: Optional[str] = None
    max_atmosphering_speed: Optional[str] = None
    crew: Optional[str] = None
    passengers: Optional[str] = None
    cargo_capacity: Optional[str] = None
    consumables: Optional[str] = None
    hyperdrive_rating: Optional[str] = None
    mglt: Optional[str] = None
    starship_class: Optional[str] = None
    created: datetime
    edited: datetime
    url: str

    class Config:
        from_attributes = True
