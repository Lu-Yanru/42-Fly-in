"""
Classes for the map representation:
Class Drone represents a drone that has an id, the name of the current
zone it is in, the path it takes and whether it is delevered or not.
Class Hub contains a name, coordinates, whether it is start or end hub,
zone type, max_drones and color.
Class connection contains the 2 hubs it connects and max_link_capacity.
Class Map contains number of drones, start and end hub, a list of hubs
and a list of connections.
"""


from enum import Enum
from pydantic import BaseModel, Field, model_validator


class Drone(BaseModel):
    id: int
    current_zone: str
    path: list[tuple[str, int]]
    delivered: bool


class ZoneType(Enum):
    """Possible zone type values."""
    NORMAL = "normal"
    BLOCK = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Hub(BaseModel):
    """Represents a hub."""
    name: str = Field(min_length=1)
    x: int
    y: int
    is_start: bool = Field(default=False)
    is_end: bool = Field(default=False)
    zone_type: ZoneType = Field(default=ZoneType.NORMAL)
    max_drones: int = Field(default=1, ge=0)
    color: str | None = Field(default=None)

    @model_validator(mode="after")
    def post_validate(self) -> "Hub":
        if "-" in self.name or " " in self.name:
            raise ValueError("Hub name may not contain dashes or spaces!")

        if self.zone_type != ZoneType.BLOCK \
                and self.max_drones == 0:
            raise ValueError("A non-blocked zone type must have capacity of"
                             "at least one drone.")

        return self


class Connection(BaseModel):
    """Represents a connection."""
    src: Hub
    dest: Hub
    capacity: int = Field(default=1, ge=0)

    @model_validator(mode="after")
    def post_validate(self) -> "Connection":
        if self.src == self.dest \
            or (self.src.x == self.dest.x
                and self.src.y == self.dest.y):
            raise ValueError("Connection's destination "
                             "and source cannot be the same!")

        if self.src.zone_type != ZoneType.BLOCK \
            and self.dest.zone_type != ZoneType.BLOCK \
                and self.capacity == 0:
            raise ValueError("A connection to a non-blocked zone"
                             "must have capacity of at least one drone.")

        return self


class Map(BaseModel):
    """Represents a map."""
    nb_drones: int = Field(gt=0)
    start: Hub
    end: Hub
    hubs: list[Hub]
    connections: list[Connection]

    @model_validator(mode="after")
    def post_validate(self) -> "Map":
        if self.start == self.end \
            or self.start.name == self.end.name \
            or (self.start.x == self.end.x
                and self.start.y == self.end.y):
            raise ValueError("Start and end hub "
                             "cannot overlap!")

        if self.start.max_drones < self.nb_drones \
                or self.end.max_drones < self.nb_drones:
            raise ValueError("Start and end hub must have capacity "
                             "for all drones!")

        return self
