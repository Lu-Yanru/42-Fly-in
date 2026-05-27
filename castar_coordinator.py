"""
The CAStarCoordinator class implements the CA* algorithm
with multiple drones.
"""


from graph import Graph, GraphError
from reservation_table import ReservationTable
from space_time_astar import AStarRouter


class RoutingError(Exception):
    """Error when routing a drone."""
    pass


class CAStarCoordinator:
    def __init__(self, nb_drones: int, graph: Graph) -> None:
        self.paths: list[list[tuple[str, int]]] = []

        self.nb_drones = nb_drones
        self.graph = graph

        self.router = AStarRouter()
        self.reservations = ReservationTable(start_name=graph.start_name,
                                             end_name=graph.end_name)

        try:
            self.heuristic = graph.reverse_dijkstra()
        except GraphError as e:
            raise GraphError(e)

    def route_all_drones(self) -> None:
        """
        Routes all drones using CA*.
        Returns a list of paths of all drones.
        """
        turn_horizon = len(self.graph.hubs) * 2 * self.nb_drones

        for id in range(1, self.nb_drones + 1):
            path = self.router.find_path(
                start=self.graph.start_name,
                end=self.graph.end_name,
                graph=self.graph,
                reservations=self.reservations,
                heuristic=self.heuristic,
                start_turn=0,
                turn_horizon=turn_horizon
            )

            if path is None:
                raise RoutingError("RoutingError: "
                                   f"Cannot find a path for drone {id}.")

            self.reservations.reserve_path(path)
            self.paths.append(path)

    def get_makespan(self) -> int:
        """
        Total turns it takes for all drones to reach end hub.
        """
        return max(path[-1][1] for path in self.paths)
