from sqlalchemy import Column, ForeignKey, Integer, Table

from api.storage.postgres import Base

character_film_association = Table(
    "character_films",
    Base.metadata,
    Column("character_id", Integer, ForeignKey("characters.id"), primary_key=True),
    Column("film_id", Integer, ForeignKey("films.id"), primary_key=True),
)

character_starship_association = Table(
    "character_starships",
    Base.metadata,
    Column("character_id", Integer, ForeignKey("characters.id"), primary_key=True),
    Column("starship_id", Integer, ForeignKey("starships.id"), primary_key=True),
)

film_starship_association = Table(
    "film_starships",
    Base.metadata,
    Column("film_id", Integer, ForeignKey("films.id"), primary_key=True),
    Column("starship_id", Integer, ForeignKey("starships.id"), primary_key=True),
)
