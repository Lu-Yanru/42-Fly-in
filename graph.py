"""
The Graph class is the basic representation of the map
as a static graph.
It contains:
- hubs: dict[str, Hub]          — all zones by name
- connections: list[Connection]  — all edges
- _adj: dict[str, list[tuple[Hub, Connection]]]
                                — adjacency list per zone
"""


from map import Hub, Connection, Map, ZoneType


class Graph:
    """
    Creates a static graph representation from the map.
    """
    def __init__(self, map: Map) -> None:
        self.start_name = map.start.name
        self.end_name = map.end.name
        self.hubs = self._get_all_hubs(map)
        self.connections = map.connections
        self._adj = self._create_adjacency()

    def get_hub(self, name: str) -> Hub:
        """Get a hub by name."""
        return self.hubs[name]
    
    def get_neighbors(self, name: str) \
        -> list[tuple[Hub, Connection]]:
        """
        Get the neighbors of a hub
        by name of this hub.
        Blocked hubs excluded.
        """
        res: list[tuple[Hub, Connection]] = []

        for hub, conn in self._adj.get(name, []):
            if hub.zone_type != ZoneType.BLOCK:
                res.append((hub, conn))

        return res

    def move_cost(self, dest: Hub) -> float:
        """
        Return the movement cost of entering
        a destiantion zone.
        """
        match dest.zone_type:
            case ZoneType.NORMAL:
                return 1.0
            case ZoneType.PRIORITY:
                return 0.9
            case ZoneType.RESTRICTED:
                return 2.0
            case ZoneType.BLOCK:
                return float("inf")

    def _get_all_hubs(self, map: Map) -> dict[str, Hub]:
        """
        Create a dictionary of all hubs with their name
        as key and the Hub object as value.
        """
        res: dict[str, Hub] = {}

        res[map.start.name] = map.start
        res[map.end.name] = map.end

        for hub in map.hubs:
            res[hub.name] = hub

        return res

    def _create_adjacency(self) \
        -> dict[str, list[tuple[Hub, Connection]]]:
        """
        Create an adjacency dictionary with hub name as key
        and a list of tuples of [neighbour_hub, connection]
        as value.
        """
        res: dict[str, list[tuple[Hub, Connection]]] = {
            name: [] for name in self.hubs.keys()
        }

        for conn in self.connections:
            res[conn.src.name].append((conn.dest, conn))
            res[conn.dest.name].append((conn.src, conn))

        return res
