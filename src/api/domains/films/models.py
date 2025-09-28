from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domains.associations import (
    character_film_association,
    film_starship_association,
)
from api.storage.postgres import Base

if TYPE_CHECKING:
    from api.domains.characters.models import Character
    from api.domains.starships.models import Starship


class Film(Base):
    __tablename__ = "films"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    episode_id: Mapped[int] = mapped_column(Integer, nullable=False)
    opening_crawl: Mapped[str] = mapped_column(Text)
    director: Mapped[str] = mapped_column(String(100))
    producer: Mapped[str] = mapped_column(String(200))
    release_date: Mapped[date] = mapped_column(Date)
    created: Mapped[datetime] = mapped_column(nullable=False)
    edited: Mapped[datetime] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(String(200), unique=True)

    # Relationships
    characters: Mapped[list["Character"]] = relationship(
        "Character", secondary=character_film_association, back_populates="films"
    )
    starships: Mapped[list["Starship"]] = relationship(
        "Starship", secondary=film_starship_association, back_populates="films"
    )
