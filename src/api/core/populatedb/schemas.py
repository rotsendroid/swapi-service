from datetime import datetime

from pydantic import BaseModel

from api.core.schemas import BaseSuccessfullResponse


class PopulateDBResponse(BaseSuccessfullResponse):
    pass


class FilmInputSchema(BaseModel):
    title: str
    episode_id: int
    opening_crawl: str
    director: str
    producer: str
    release_date: str
    characters: list[str]
    planets: list[str]
    starships: list[str]
    vehicles: list[str]
    species: list[str]
    created: datetime
    edited: datetime
    url: str


class CharacterInputSchema(BaseModel):
    name: str
    height: str
    mass: str
    hair_color: str
    skin_color: str
    eye_color: str
    birth_year: str
    gender: str
    homeworld: str
    films: list[str]
    species: list[str]
    vehicles: list[str]
    starships: list[str]
    created: datetime
    edited: datetime
    url: str


class StarshipInputSchema(BaseModel):
    name: str
    model: str
    manufacturer: str
    cost_in_credits: str
    length: str
    max_atmosphering_speed: str
    crew: str
    passengers: str
    cargo_capacity: str
    consumables: str
    hyperdrive_rating: str
    MGLT: str
    starship_class: str
    pilots: list[str]
    films: list[str]
    created: datetime
    edited: datetime
    url: str
