import pytest

from graph import Graph
from map import Hub, Connection, Map, ZoneType
from castar_coordinator import CAStarCoordinator


def make_hub(name: str, x: int = 0, y: int = 0, zone_type: ZoneType = ZoneType.NORMAL, max_drones: int = 1) -> Hub:
    return Hub(name=name, x=x, y=y, zone_type=zone_type, max_drones=max_drones)

def make_graph(hubs: list[Hub], connections: list[Connection],
              start: Hub, end: Hub) -> Graph:
    return Graph(Map(nb_drones=1, start=start, end=end, hubs=hubs, connections=connections))

def route(graph: Graph, nb_drones: int) -> list[list[tuple[str, int]]]:
    coordinator = CAStarCoordinator()
    coordinator.route_all_drones(
        nb_drones=nb_drones,
        graph=graph,
    )
    return coordinator.paths

# Basic tests
def test_single_drone_reaches_end() -> None:
    """Single drone must start at start and end at end."""
    start = make_hub("start", 0, 0)
    end = make_hub("end", 1, 0)
    graph = make_graph([], [Connection(src=start, dest=end)], start, end)

    paths = route(graph, nb_drones=1)

    assert len(paths) == 1
    assert paths[0][0][0] == "start"
    assert paths[0][-1][0] == "end"


def test_all_drones_reach_end() -> None:
    """Every drone path must terminate at end."""
    start = make_hub("start", 0, 0)
    end = make_hub("end", 1, 0)
    a = make_hub("A", 1, 1)
    b = make_hub("B", 1, -1)
    graph = make_graph(
        [a, b],
        [Connection(src=start, dest=a),
         Connection(src=start, dest=b),
         Connection(src=a, dest=end),
         Connection(src=b, dest=end)],
        start, end
    )

    paths = route(graph, nb_drones=2)

    assert all(p[-1][0] == "end" for p in paths)

def test_returns_one_path_per_drone() -> None:
    """Number of paths returned must equal nb_drones."""
    start = make_hub("start", 0, 0)
    end = make_hub("end", 2, 0)
    a = make_hub("A", 1, 1)
    b = make_hub("B", 1, -1)
    graph = make_graph(
        [a, b],
        [Connection(src=start, dest=a),
         Connection(src=start, dest=b),
         Connection(src=a, dest=end),
         Connection(src=b, dest=end)],
        start, end
    )

    paths = route(graph, nb_drones=2)

    assert len(paths) == 2


# Capacity constraints
def test_no_two_drones_in_same_zone_same_turn() -> None:
    """Zone capacity of 1 must never be exceeded by two drones."""
    start = make_hub("start", 0, 0)
    end = make_hub("end", 2, 0)
    a = make_hub("A", 1, 0, max_drones=1)
    graph = make_graph(
        [a],
        [Connection(src=start, dest=a),
         Connection(src=a, dest=end)],
        start, end
    )

    paths = route(graph, nb_drones=2)

    # Collect (zone, turn) occupancy counts
    occupancy: dict[tuple[str, int], int] = {}
    for path in paths:
        for zone, turn in path:
            key = (zone, turn)
            occupancy[key] = occupancy.get(key, 0) + 1

    for (zone, turn), count in occupancy.items():
        if zone in ("start", "end"):
            continue  # unlimited capacity
        hub = next(h for h in [a] if h.name == zone)
        assert count <= hub.max_drones, (
            f"Zone {zone} exceeded capacity at turn {turn}: "
            f"{count} drones > max {hub.max_drones}"
        )


def test_zone_with_higher_capacity_allows_multiple_drones() -> None:
    """A zone with max_drones=2 may hold two drones at the same turn."""
    start = make_hub("start", 0, 0)
    end = make_hub("end",2, 0)
    a = make_hub("A", 1, 0, max_drones=2)
    graph = make_graph(
        [a],
        [Connection(src=start, dest=a),
         Connection(src=a, dest=end)],
        start, end
    )

    # Should not raise — both drones can share A
    paths = route(graph, nb_drones=2)
    assert len(paths) == 2


def test_no_two_drones_share_link_beyond_capacity() -> None:
    """Link with capacity=1 must not be used by two drones on the same turn."""
    start = make_hub("start", 0, 0)
    end = make_hub("end", 2, 0)
    a = make_hub("A", 1, 0)
    graph = make_graph(
        [a],
        [Connection(src=start, dest=a, capacity=1),
         Connection(src=a, dest=end, capacity=1)],
        start, end
    )

    paths = route(graph, nb_drones=2)

    # Count link usage per turn
    link_usage: dict[tuple[str, str, int], int] = {}
    for path in paths:
        for i in range(1, len(path)):
            prev_zone, prev_turn = path[i - 1]
            curr_zone, curr_turn = path[i]
            if prev_zone == curr_zone:
                continue  # wait — no link used
            key_a, key_b = sorted([prev_zone, curr_zone])
            key = (key_a, key_b, prev_turn)
            link_usage[key] = link_usage.get(key, 0) + 1

    for (za, zb, turn), count in link_usage.items():
        assert count <= 1, (
            f"Link {za}-{zb} exceeded capacity at turn {turn}: {count} drones"
        )


def test_link_with_higher_capacity_allows_multiple_drones() -> None:
    """A link with capacity=2 may be used by two drones on the same turn."""
    start = make_hub("start", 0, 0)
    end = make_hub("end", 1, 0)
    graph = make_graph(
        [],
        [Connection(src=start, dest=end, capacity=2)],
        start, end
    )

    # Both drones use the same link at turn 0 — must not raise
    paths = route(graph, nb_drones=2)
    assert len(paths) == 2


def test_restricted_zone_arrival_takes_two_turns() -> None:
    """A drone entering a restricted zone must arrive two turns later."""
    start = make_hub("start", 0, 0)
    end = make_hub("end", 2, 0)
    restricted = make_hub("R", 1, 0, zone_type=ZoneType.RESTRICTED)
    graph = make_graph(
        [restricted],
        [Connection(src=start, dest=restricted),
         Connection(src=restricted, dest=end)],
        start, end
    )

    paths = route(graph, nb_drones=1)
    path = paths[0]

    for i in range(1, len(path)):
        prev_zone, prev_turn = path[i - 1]
        curr_zone, curr_turn = path[i]
        if curr_zone == "R":
            assert curr_turn - prev_turn == 2, (
                "Entering restricted zone must cost exactly 2 turns"
            )


def test_two_drones_stagger_through_restricted_zone() -> None:
    """Two drones cannot be mid-transit into the same restricted zone
    at the same turn — they must stagger."""
    start = make_hub("start", 0, 0)
    end = make_hub("end", 2, 0)
    restricted = make_hub("R", 1, 0, zone_type=ZoneType.RESTRICTED, max_drones=2)
    graph = make_graph(
        [restricted],
        [Connection(src=start, dest=restricted, capacity=1),
         Connection(src=restricted, dest=end)],
        start, end
    )

    paths = route(graph, nb_drones=2)

    # Collect transit turns (departure turn when entering restricted zone)
    transit_turns: list[int] = []
    for path in paths:
        for i in range(1, len(path)):
            prev_zone, prev_turn = path[i - 1]
            curr_zone, _ = path[i]
            if curr_zone == "R":
                transit_turns.append(prev_turn)

    # With capacity=1, no two drones may be in transit at the same turn
    assert len(transit_turns) == len(set(transit_turns)), (
        "Two drones entered restricted zone transit at the same turn"
    )

def test_two_drones_can_enter_restricted_zone_when_enough_capacity() -> None:
    """Two drones can be mid-transit into the same restricted zone
    at the same turn if there is enough capacity."""
    start = make_hub("start", 0, 0)
    end = make_hub("end", 2, 0)
    restricted = make_hub("R", 1, 0, zone_type=ZoneType.RESTRICTED, max_drones=2)
    graph = make_graph(
        [restricted],
        [Connection(src=start, dest=restricted, capacity=2),
         Connection(src=restricted, dest=end, capacity=2)],
        start, end
    )

    paths = route(graph, nb_drones=2)

    # With capacity=2, two drones can be in transit at the same turn
    # So they can go togehter the whole way
    assert len(paths[0]) == len(paths[1])

# Makespan
def test_makespan_equals_last_arrival_turn() -> None:
    """Makespan must equal the maximum arrival turn across all paths."""
    start = make_hub("start", 0, 0)
    end = make_hub("end", 2, 0)
    a = make_hub("A", 1, 1)
    b = make_hub("B", 1, -1)
    graph = make_graph(
        [a, b],
        [Connection(src=start, dest=a),
         Connection(src=start, dest=b),
         Connection(src=a, dest=end),
         Connection(src=b, dest=end)],
        start, end
    )

    coordinator = CAStarCoordinator()
    coordinator.route_all_drones(nb_drones=2, graph=graph)
    makespan = coordinator.get_makespan()

    assert makespan == 2
