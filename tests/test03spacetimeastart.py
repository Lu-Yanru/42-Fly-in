import pytest

from graph import Graph
from map import Hub, Connection, Map, ZoneType
from reservation_table import ReservationTable
from space_time_astar import AStarRouter


def make_hub(name: str, x: int = 0, y: int = 0, zone_type: ZoneType = ZoneType.NORMAL) -> Hub:
    return Hub(name=name, x=x, y=y, zone_type=zone_type)

def make_graph(hubs: list[Hub], connections: list[Connection],
              start: Hub, end: Hub) -> Graph:
    return Graph(Map(nb_drones=1, start=start, end=end, hubs=hubs, connections=connections))

def make_table(graph: Graph) -> ReservationTable:
    return ReservationTable(start_name=graph.start_name, end_name=graph.end_name)

def find(graph: Graph, table: ReservationTable, start_turn: int = 0) -> list[tuple[str, int]] | None:
    h = graph.reverse_dijkstra()
    return AStarRouter().find_path(
        start=graph.start_name,
        end=graph.end_name,
        graph=graph,
        reservations=table,
        heuristic=h,
        start_turn=start_turn,
        turn_horizon=20
    )

def test_astar_basic() -> None:
    start = make_hub("start", 0, 0)
    end = make_hub("end", 1, 0)
    conn = Connection(src=start, dest=end)
    graph = make_graph([], [conn], start, end)
    table = make_table(graph)

    path = find(graph, table)

    assert path is not None
    assert path[0] == ("start", 0)
    assert path[1] == ("end", 1)

def test_astar_priority() -> None:
    start = make_hub("start", 0, 0)
    p = make_hub("P", 1, 1, zone_type=ZoneType.PRIORITY)
    n = make_hub("N", 1, 0)
    end = make_hub("end", 2, 0)
    conn = Connection(src=start, dest=p)
    conn1 = Connection(src=start, dest=n)
    conn2 = Connection(src=p, dest=end)
    conn3 = Connection(src=n, dest=end)
    graph = make_graph([p, n], [conn, conn1, conn2, conn3], start, end)
    table = make_table(graph)

    path = find(graph, table)

    zones = [z for z, _ in path]
    assert path is not None
    assert path[1] == ("P", 1)
    assert "N" not in zones

def test_astar_restricted() -> None:
    start = make_hub("start", 0, 0)
    r = make_hub("R", 1, 1, zone_type=ZoneType.RESTRICTED)
    end = make_hub("end", 2, 0)
    conn = Connection(src=start, dest=r)
    conn1 = Connection(src=r, dest=end)
    graph = make_graph([r], [conn, conn1], start, end)
    table = make_table(graph)

    path = find(graph, table)

    assert path is not None
    assert path[1] == ("R", 2)
    assert path[2] == ("end", 3)

def test_astar_wait() -> None:
    start = make_hub("start", 0, 0)
    a = make_hub("A", 1, 0)
    end = make_hub("end", 2, 0)
    conn = Connection(src=start, dest=a)
    conn1 = Connection(src=a, dest=end)
    graph = make_graph([a], [conn, conn1], start, end)
    table = make_table(graph)

    table.reserve_hub("A", 1)

    path = find(graph, table)

    assert path is not None
    assert path[1] == ("start", 1)
    assert path[2] == ("A", 2)

def test_astar_alternative_route() -> None:
    start = make_hub("start", 0, 0)
    p = make_hub("P", 1, 1)
    n = make_hub("N", 1, 0)
    end = make_hub("end", 2, 0)
    conn = Connection(src=start, dest=p)
    conn1 = Connection(src=start, dest=n)
    conn2 = Connection(src=p, dest=end)
    conn3 = Connection(src=n, dest=end)
    graph = make_graph([p, n], [conn, conn1, conn2, conn3], start, end)
    table = make_table(graph)

    table.reserve_hub("N", 1)

    path = find(graph, table)

    zones = [z for z, _ in path]
    assert path is not None
    assert "P" in zones
    assert "N" not in zones

def test_astar_link_capacity() -> None:
    start = make_hub("start", 0, 0)
    p = make_hub("P", 1, 1)
    n = make_hub("N", 1, 0)
    end = make_hub("end", 2, 0)
    conn = Connection(src=start, dest=p)
    conn1 = Connection(src=start, dest=n)
    conn2 = Connection(src=p, dest=end)
    conn3 = Connection(src=n, dest=end)
    graph = make_graph([p, n], [conn, conn1, conn2, conn3], start, end)
    table = make_table(graph)

    table.reserve_conn("start", "N", 0)

    path = find(graph, table)

    zones = [z for z, _ in path]
    assert path is not None
    assert "P" in zones
    assert "N" not in zones

def test_astar_full_transit() -> None:
    start = make_hub("start", 0, 0)
    r = make_hub("R", 1, 1, zone_type=ZoneType.RESTRICTED)
    end = make_hub("end", 2, 0)
    conn = Connection(src=start, dest=r)
    conn1 = Connection(src=r, dest=end)
    graph = make_graph([r], [conn, conn1], start, end)
    table = make_table(graph)

    table.reserve_transit("start", "R", 1)

    path = find(graph, table)

    assert path is not None
    assert path[1] == ("start", 1)
    assert path[2] == ("R", 3)
    assert path[3] == ("end", 4)

def test_astar_path_validity() -> None:
    start = make_hub("start", 0, 0)
    r = make_hub("R", 1, 1, zone_type=ZoneType.RESTRICTED)
    a = make_hub("A", 1, 0)
    b = make_hub("B", 2, 0)
    end = make_hub("end", 3, 0)
    conn = Connection(src=start, dest=a)
    conn1 = Connection(src=start, dest=r)
    conn2 = Connection(src=r, dest=end)
    conn3 = Connection(src=a, dest=b)
    conn4 = Connection(src=b, dest=end)
    graph = make_graph([r, a, b], [conn, conn1, conn2, conn3, conn4], start, end)
    table = make_table(graph)

    path = find(graph, table)
    print(path)

    assert path is not None
    
    for (z1, t1), (z2, t2) in zip(path, path[1:]):
        assert t2 - t1 in (1, 2)
        if z1 == z2:
            continue
        neighbor_names = {h.name for h, _ in graph.get_neighbors(z1)}
        assert z2 in neighbor_names