"""
The ReservationTable class implements the reservation table with:
- zone_reservations: dict[tuple[str, int], int]
    — maps (zone_name, turn) to drone count
- connection_reservations: dict[tuple[str, str, int], int]
    — maps (zone_a, zone_b, turn) to drone count
- transit_reservations: dict[tuple[str, str, int], int]
    — maps (from_zone, to_zone, turn) to drone count
    for restricted zone mid-transit
"""


class ReservationTable:
    """
    Tracks capacity constrains in the space-time graph.
    Shared among all drones.
    """
    def __init__(self, start_name: str,
                 end_name: str) -> None:
        self.start_name = start_name
        self.end_name = end_name

        self._hub_res: dict[tuple[str, int], int] = {}
        self._conn_res: dict[tuple[str, str, int], int] = {}
        self._transit_res: dict[tuple[str, str, int], int] = {}

    # Check availabilities
    def is_hub_available(self, hub: str, turn: int,
                         max_drones: int) -> bool:
        """Checks if a hub is available."""
        if hub == self.end_name:
            return True
        if hub == self.start_name:
            return True
        return self._hub_res.get((hub, turn), 0) < max_drones

    def is_conn_available(self, src: str, dest: str,
                          turn: int, capacity: int) -> bool:
        """Checks if a connection is available."""
        key = self._normalize_conn_key(src, dest, turn)
        return self._conn_res.get(key, 0) < capacity

    def is_transit_available(self, src: str, dest: str,
                             turn: int, capacity: int,
                             dest_max_drones: int) -> bool:
        """
        Checks if a transit to a restricted zone is available.
        Also needs to check if the destination hub has capacity
        available for the next turn.
        """
        conn_free = self._transit_res.get((src, dest, turn), 0) < capacity
        dest_free = self.is_hub_available(dest, turn + 1, dest_max_drones)
        return conn_free and dest_free

    # Reserve capacity
    def reserve_hub(self, hub: str, turn: int) -> None:
        """
        Reserve a hub for a specific turn.
        """
        key = (hub, turn)
        self._hub_res[key] = self._hub_res.get(key, 0) + 1

    def reserve_conn(self, hub1: str, hub2: str, turn: int) -> None:
        """
        Reserve a connection between hub1 and hub2 for a specific turn.
        """
        key = self._normalize_conn_key(hub1, hub2, turn)
        self._conn_res[key] = self._conn_res.get(key, 0) + 1

    def reserve_transit(self, src: str, dest: str, turn: int) -> None:
        """
        Reserve a transit to a restricted zone for a specific turn
        also reserves the dest hub for the next turn.
        """
        key = (src, dest, turn)
        self._transit_res[key] = self._transit_res.get(key, 0) + 1
        self.reserve_hub(dest, turn + 1)

    def reserve_path(self, path: list[tuple[str, int]]) -> None:
        """
        Reserve all nodes on a drone path.
        Skip restricted zone reservations because reserve_transit
        reserve them already.
        """
        restricted: set[tuple[str, int]] = set()

        for i, (hub, turn) in enumerate(path):
            if i == 0:
                continue

            prev_hub, prev_turn = path[i - 1]

            # Drone waited, no connection to reserve
            if prev_hub == hub:
                continue

            self.reserve_conn(prev_hub, hub, prev_turn)

            # Reserve both transit and destination hub
            # for restricted hub
            if turn == prev_turn + 2:
                self.reserve_transit(prev_hub, hub, prev_turn + 1)
                restricted.add((hub, turn))

            # Skip restricted zone reservation
            if (hub, turn) not in restricted:
                self.reserve_hub(hub, turn)

    # Internal helpers
    @staticmethod
    def _normalize_conn_key(hub1: str, hub2: str,
                            turn: int) -> tuple[str, str, int]:
        """
        Normalize connection key to be in alphabetical order
        so (A, B) and (B, A) map to the same entry.
        """
        a, b = (hub1, hub2) if hub1 < hub2 else (hub2, hub1)
        return (a, b, turn)
