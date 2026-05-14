"""
Classes for the map representation:
Class Hub contains a name, coordinates, whether it is start or end hub,
zone type, max_drones and color.
Class connection contains the 2 hubs it connects and max_link_capacity.
Class Map contains number of drones, start and end hub, a list of hubs
and a list of connections.
"""


from enum import Enum
from pydantic import BaseModel, Field, model_validator


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
    max_drones: int = Field(default=1, gt=0)
    color: str | None = Field(default=None)

    # adjacency list
    adj: dict[Hub, float] = {}

    @model_validator(mode="after")
    def validate(self):
        if "-" in self.name or " " in self.name:
            raise ValueError("Hub name may not contain dashes or spaces!")
        return self

    def __hash__(self):
        return hash(self.name)


class Connection(BaseModel):
    """Represents a connection."""
    src: Hub
    dest: Hub
    capacity: int = Field(default=1, gt=0)

    @model_validator(mode="after")
    def validate(self):
        if self.src == self.dest \
            or (self.src.x == self.dest.x
                and self.src.y == self.dest.y):
            raise ValueError("Connection's destination "
                             "and source cannot be the same!")
        return self


class Map(BaseModel):
    """Represents a map."""
    nb_drones: int = Field(gt=0)
    start: Hub
    end: Hub
    hubs: list[Hub]
    connections: list[Connection]

    @model_validator(mode="after")
    def validate(self):
        if self.start == self.end \
            or self.start.name == self.end.name \
            or (self.start.x == self.end.x
                and self.start.y == self.end.y):
            raise ValueError("Start and end hub "
                             "cannot overlap!")
        return self
