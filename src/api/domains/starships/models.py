from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domains.associations import (
    character_starship_association,
    film_starship_association,
)
from api.storage.postgres import Base

if TYPE_CHECKING:
    from api.domains.characters.models import Character
    from api.domains.films.models import Film


class Starship(Base):
    __tablename__ = "starships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100))
    manufacturer: Mapped[str] = mapped_column(String(100))
    cost_in_credits: Mapped[Optional[str]] = mapped_column(String(20))
    length: Mapped[Optional[str]] = mapped_column(String(20))
    max_atmosphering_speed: Mapped[Optional[str]] = mapped_column(String(20))
    crew: Mapped[Optional[str]] = mapped_column(String(50))
    passengers: Mapped[Optional[str]] = mapped_column(String(20))
    cargo_capacity: Mapped[Optional[str]] = mapped_column(String(20))
    consumables: Mapped[Optional[str]] = mapped_column(String(50))
    hyperdrive_rating: Mapped[Optional[str]] = mapped_column(String(10))
    mglt: Mapped[Optional[str]] = mapped_column(String(10))
    starship_class: Mapped[Optional[str]] = mapped_column(String(50))
    created: Mapped[datetime] = mapped_column(nullable=False)
    edited: Mapped[datetime] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(String(200), unique=True)

    # Relationships
    pilots: Mapped[List["Character"]] = relationship(
        "Character",
        secondary=character_starship_association,
        back_populates="starships",
    )
    films: Mapped[List["Film"]] = relationship(
        "Film", secondary=film_starship_association, back_populates="starships"
    )

    def __repr__(self):
        return f"<Starship(name='{self.name}', model='{self.model}')>"
