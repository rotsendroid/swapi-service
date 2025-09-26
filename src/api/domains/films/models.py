from datetime import date, datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domains.associations import (
    character_film_association,
)
from api.storage.postgres import Base

if TYPE_CHECKING:
    from api.domains.characters.models import Character
    from api.domains.starships.models import Starship

film_starship_association = Table(
    "film_starships",
    Base.metadata,
    Column("film_id", Integer, ForeignKey("films.id"), primary_key=True),
    Column("starship_id", Integer, ForeignKey("starships.id"), primary_key=True),
)


class Film(Base):
    __tablename__ = "films"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
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
    characters: Mapped[List["Character"]] = relationship(
        "Character", secondary=character_film_association, back_populates="films"
    )
    starships: Mapped[List["Starship"]] = relationship(
        "Starship", secondary=film_starship_association, back_populates="films"
    )

    def __repr__(self):
        return f"<Film(title='{self.title}', episode_id={self.episode_id})>"
