from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domains.associations import (
    character_film_association,
    character_starship_association,
)
from api.storage.postgres import Base

if TYPE_CHECKING:
    from api.domains.films.models import Film
    from api.domains.starships.models import Starship


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    height: Mapped[Optional[str]] = mapped_column(String(10))
    mass: Mapped[Optional[str]] = mapped_column(String(10))
    hair_color: Mapped[Optional[str]] = mapped_column(String(50))
    skin_color: Mapped[Optional[str]] = mapped_column(String(50))
    eye_color: Mapped[Optional[str]] = mapped_column(String(50))
    birth_year: Mapped[Optional[str]] = mapped_column(String(20))
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    created: Mapped[datetime] = mapped_column(nullable=False)
    edited: Mapped[datetime] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(String(200), unique=True)

    # Relationships
    films: Mapped[List["Film"]] = relationship(
        "Film", secondary=character_film_association, back_populates="characters"
    )
    starships: Mapped[List["Starship"]] = relationship(
        "Starship", secondary=character_starship_association, back_populates="pilots"
    )

    def __repr__(self):
        return f"<Character(name='{self.name}')>"
