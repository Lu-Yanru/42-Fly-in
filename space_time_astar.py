"""
Implement the A* algorithm on a space-time graph.

The SpaceTimeNode class defines a SpaceTimeNode with the hub name,
turn number, g score and f score (g + h).
The AStarRouter class defines the main A* algorithm logic on
the space-time graph.
"""


from dataclasses import dataclass, field
import heapq

from graph import Graph
from map import Hub, ZoneType
from reservation_table import ReservationTable


@dataclass
class SpaceTimeNode:
    hub: str
    turn: int
    g: float
    f: float
    came_from: "SpaceTimeNode | None" = field(default=None, compare=False)

    def __lt__(self, other: "SpaceTimeNode") -> bool:
        """
        For min-heap, when comparing two SpaceTimeNodes,
        primarily compare f, if tie then compare turn secondarily.
        This prefers nodes that arrive eariler.
        """
        return (self.f, self.turn) < (other.f, other.turn)


class AStarRouter:

    def find_path(
            self,
            start: str,
            end: str,
            graph: Graph,
            reservations: ReservationTable,
            heuristic: dict[str, float],
            start_turn: int,
            turn_horizon: int
            ) -> list[tuple[str, int]] | None:
        """
        Use A* to find the shortest path on a space-time graph
        for one drone.
        Returns the path (a list of (hub, turn) tuple),
        or None if no path was found within turn_horizon.
        """
        start_node = SpaceTimeNode(
            hub=start,
            turn=start_turn,
            g=0.0,
            f=heuristic.get(start, float("inf"))
        )

        # Priority queue
        heap: list[SpaceTimeNode] = [start_node]
        # Visited/cost record for each (hub, turn) pair
        best_g: dict[tuple[str, int], float] = {
            (start, start_turn): 0.0
        }

        while heap:
            current = heapq.heappop(heap)

            # Skip if has a bigger g
            if current.g > \
                    best_g.get((current.hub, current.turn), float("inf")):
                continue

            # Return path if goal is reached
            if current.hub == end:
                res = self._reconstruct_path(current)
                return res

            # Stop searching if turn_horizon is reached
            if current.turn >= turn_horizon:
                continue

            neighbors = self._get_neighbors(
                    current, graph, reservations, heuristic, turn_horizon
                    )
            for neighbor in neighbors:
                key = (neighbor.hub, neighbor.turn)
                if neighbor.g < best_g.get(key, float("inf")):
                    best_g[key] = neighbor.g
                    heapq.heappush(heap, neighbor)

        return None

    def _get_neighbors(
            self,
            current: SpaceTimeNode,
            graph: Graph,
            reservations: ReservationTable,
            heuristic: dict[str, float],
            turn_horizon: int
            ) -> list[SpaceTimeNode]:
        """
        Get neighbors of the current SpaceTimeNode.
        """
        neighbors: list[SpaceTimeNode] = []

        # If wait
        wait = self._wait(current, graph, reservations, heuristic)
        if wait is not None:
            neighbors.append(wait)

        # If move
        for hub, connection in graph.get_neighbors(current.hub):
            next = hub.name

            if hub.zone_type == ZoneType.RESTRICTED:
                node = self._restricted_move(
                    current, next, hub, connection.capacity,
                    graph, reservations, heuristic, turn_horizon
                )
            else:
                node = self._move(
                    current, next, hub, connection.capacity,
                    graph, reservations, heuristic
                )

            if node is not None:
                neighbors.append(node)

        return neighbors

    def _wait(
            self,
            current: SpaceTimeNode,
            graph: Graph,
            reservations: ReservationTable,
            heuristic: dict[str, float]
            ) -> SpaceTimeNode | None:
        """
        Returns the neighboring SpaceTimeNode if the drone waits.
        None if the drone cannot wait.
        """
        hub = graph.get_hub(current.hub)
        next_turn = current.turn + 1

        if not reservations.is_hub_available(current.hub,
                                             next_turn, hub.max_drones):
            return None

        g = current.g + 1.0
        return SpaceTimeNode(
            hub=current.hub,
            turn=next_turn,
            g=g,
            f=g + heuristic.get(current.hub, float("inf")),
            came_from=current
        )

    def _move(
            self,
            current: SpaceTimeNode,
            next: str,
            dest_hub: Hub,
            conn_capacity: int,
            graph: Graph,
            reservations: ReservationTable,
            heuristic: dict[str, float]
            ) -> SpaceTimeNode | None:
        """
        Returns a neighboring SpaceTimeNode if the drone moves to a
        normal or priority zone (1 turn).
        None if no such neighbor available.
        """
        next_turn = current.turn + 1
        move_cost = graph.get_cost(dest_hub)

        hub_available = reservations.is_hub_available(
            next, next_turn, dest_hub.max_drones
        )
        conn_available = reservations.is_conn_available(
            current.hub, next, current.turn, conn_capacity
        )
        if not hub_available or not conn_available:
            return None

        g = current.g + move_cost
        return SpaceTimeNode(
            hub=next,
            turn=next_turn,
            g=g,
            f=g + heuristic.get(next, float("inf")),
            came_from=current
        )

    def _restricted_move(
            self,
            current: SpaceTimeNode,
            next: str,
            dest_hub: Hub,
            conn_capacity: int,
            graph: Graph,
            reservations: ReservationTable,
            heuristic: dict[str, float],
            turn_horizon: int
            ) -> SpaceTimeNode | None:
        """
        Returns a neighboring SpaceTimeNode if the drone moves to a
        restricted zone (2 turns).
        None if no such neighbor available.
        """
        arrival_turn = current.turn + 2

        if arrival_turn > turn_horizon:
            return None

        transit_available = reservations.is_transit_available(
            current.hub, next, current.turn + 1,
            conn_capacity, dest_hub.max_drones
        )
        if not transit_available:
            return None

        g = current.g + graph.get_cost(dest_hub)
        return SpaceTimeNode(
            hub=next,
            turn=arrival_turn,
            g=g,
            f=g + heuristic.get(next, float("inf")),
            came_from=current
        )

    @staticmethod
    def _reconstruct_path(node: SpaceTimeNode) -> list[tuple[str, int]]:
        """
        Reconstruct a path from a given node to the start node.
        Returns a list of (zone, turn).
        """
        path: list[tuple[str, int]] = []

        current: SpaceTimeNode | None = node
        while current is not None:
            path.append((current.hub, current.turn))
            current = current.came_from

        path.reverse()
        return path
