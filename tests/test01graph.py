import pytest

from map import Hub, Connection, Map, ZoneType
from graph import Graph, GraphError

def make_hub(name: str, x: int = 0, y: int = 0, zone_type: ZoneType = ZoneType.NORMAL) -> Hub:
    return Hub(name=name, x=x, y=y, zone_type=zone_type)

def make_map(hubs: list[Hub], connections: list[Connection],
              start: Hub, end: Hub) -> Map:
    return Map(nb_drones=1, start=start, end=end, hubs=hubs, connections=connections)

def test_get_neighbors_basic() -> None:
    start = make_hub("start", 0, 0)
    end = make_hub("end", 3, 0)
    a = make_hub("A", 1, 0)
    b = make_hub("B", 2, 0)
    conn = Connection(src=a, dest=b)
    map = make_map([a, b], [conn], start, end)
    graph = Graph(map)

    a_neighbors = [h.name for h, _ in graph.get_neighbors("A")]
    b_neighbors = [h.name for h, _ in graph.get_neighbors("B")]

    assert "B" in a_neighbors
    assert "A" in b_neighbors

def test_blocked_neighbors() -> None:
    start = make_hub("start", 0, 0)
    end = make_hub("end", 3, 0)
    a = make_hub("A", 1, 0)
    b = make_hub("B", 2, 0)
    c = make_hub("C", 4, 0, zone_type=ZoneType.BLOCK)
    conn1 = Connection(src=a, dest=b)
    conn2 = Connection(src=a, dest=c)
    map = make_map([a, b, c], [conn1, conn2], start, end)
    graph = Graph(map)

    a_neighbors = [h.name for h, _ in graph.get_neighbors("A")]

    assert "B" in a_neighbors
    assert "C" not in a_neighbors

def test_isolated_hub() -> None:
    start = make_hub("start", 0, 0)
    end = make_hub("end", 1, 0)
    map = make_map([], [], start, end)
    graph = Graph(map)

    neighbors = [h.name for h, _ in graph.get_neighbors("start")]

    assert neighbors == []

def test_heuristic_basic() -> None:
    start = make_hub("start", 0, 0)
    end = make_hub("end", 1, 0)
    conn = Connection(src=start, dest=end)
    map = make_map([], [conn], start, end)
    graph = Graph(map)

    h = graph.reverse_dijkstra()

    assert h["start"] == 1.0
    assert h["end"] == 0.0

def test_heuristic_restricted() -> None:
    start = make_hub("start", 0, 0)
    end = make_hub("end", 2, 0)
    a = make_hub("A", 1, 0, ZoneType.RESTRICTED)
    conn1 = Connection(src=start, dest=a)
    conn2 = Connection(src=a, dest=end)
    map = make_map([a], [conn1, conn2], start, end)
    graph = Graph(map)

    h = graph.reverse_dijkstra()

    assert h["start"] == 3.0
    assert h["A"] == 1.0
    assert h["end"] == 0.0

def test_heuristic_priority() -> None:
    start = make_hub("start", 0, 0)
    end = make_hub("end", 2, 0)
    a = make_hub("A", 1, 0)
    b = make_hub("B", 1, 1, ZoneType.PRIORITY)
    conn1 = Connection(src=start, dest=a)
    conn2 = Connection(src=a, dest=end)
    conn3 = Connection(src=start, dest=b)
    conn4 = Connection(src=b, dest=end)
    map = make_map([a, b], [conn1, conn2, conn3, conn4], start, end)
    graph = Graph(map)

    h = graph.reverse_dijkstra()

    assert h["start"] == 1.9
    assert h["A"] == 1.0
    assert h["B"] == 1.0
    assert h["end"] == 0.0

def test_disconnected_graph() -> None:
    start = make_hub("start", 0, 0)
    end = make_hub("end", 2, 0)
    map = make_map([], [], start, end)
    graph = Graph(map)

    with pytest.raises(GraphError):
        graph.reverse_dijkstra()

def test_heuristic_blocked() -> None:
    start = make_hub("start", 0, 0)
    end = make_hub("end", 2, 0)
    a = make_hub("A", 1, 0)
    b = make_hub("B", 1, 1, ZoneType.BLOCK)
    conn1 = Connection(src=start, dest=a)
    conn2 = Connection(src=a, dest=end)
    conn3 = Connection(src=start, dest=b)
    conn4 = Connection(src=b, dest=end)
    map = make_map([a, b], [conn1, conn2, conn3, conn4], start, end)
    graph = Graph(map)

    h = graph.reverse_dijkstra()

    assert h["start"] == 2.0
    assert h["A"] == 1.0
    assert h["B"] == float("inf")
    assert h["end"] == 0.0
