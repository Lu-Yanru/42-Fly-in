import pytest

from reservation_table import ReservationTable


@pytest.fixture
def table() -> ReservationTable:
    return ReservationTable(start_name="start", end_name="end")


# Hub availability
def test_hub_available_when_empty(table: ReservationTable) -> None:
    assert table.is_hub_available("A", 1, 1) is True

def test_hub_available_when_capacity(table: ReservationTable) -> None:
    table.reserve_hub("A", 1)
    assert table.is_hub_available("A", 1, 2) is True

def test_hub_available_when_full(table: ReservationTable) -> None:
    table.reserve_hub("A", 1)
    assert table.is_hub_available("A", 1, 1) is False

def test_hub_available_when_another_turn(table: ReservationTable) -> None:
    table.reserve_hub("A", 1)
    assert table.is_hub_available("A", 2, 1) is True


# Connection availability
def test_conn_available_when_empty(table: ReservationTable) -> None:
    assert table.is_conn_available("A", "B", 1, 1) is True

def test_conn_available_when_capacity(table: ReservationTable) -> None:
    table.reserve_conn("A", "B", 1)
    assert table.is_conn_available("A", "B", 1, 2) is True

def test_conn_available_when_full(table: ReservationTable) -> None:
    table.reserve_conn("A", "B", 1)
    assert table.is_conn_available("A", "B", 1, 1) is False

def test_conn_available_other_direction(table: ReservationTable) -> None:
    table.reserve_conn("B", "A", 1)
    assert table.is_conn_available("A", "B", 1, 1) is False

def test_conn_available_different_turn(table: ReservationTable) -> None:
    table.reserve_conn("A", "B", 1)
    assert table.is_conn_available("A", "B", 2, 1) is True

# Transit availability
def test_transit_available_when_empty(table: ReservationTable) -> None:
    assert table.is_transit_available("A", "B", 1, 1, 1) is True

def test_transit_available_when_capacity(table: ReservationTable) -> None:
    table.reserve_transit("A", "B", 1)
    assert table.is_transit_available("A", "B", 1, 2, 2) is True

def test_transit_available_when_link_full(table: ReservationTable) -> None:
    table.reserve_transit("A", "B", 1)
    assert table.is_transit_available("A", "B", 1, 1, 2) is False

def test_transit_available_when_dest_full(table: ReservationTable) -> None:
    table.reserve_hub("B", 2)
    assert table.is_transit_available("A", "B", 1, 2, 1) is False

def test_transit_also_reserve_dest(table: ReservationTable) -> None:
    table.reserve_transit("A", "B", 1)
    assert table.is_hub_available("B", 2, 1) is False

def test_transit_other_direction(table: ReservationTable) -> None:
    table.reserve_hub("A", 1)
    table.reserve_transit("A", "B", 1)
    table.reserve_hub("B", 1)
    assert table.is_conn_available("B", "A", 1, 2) is True
    assert table.is_hub_available("A", 2, 1) is True


# Reserve path
def test_path_reserve_zones(table: ReservationTable) -> None:
    path = [("start", 0), ("A", 1), ("end", 2)]
    table.reserve_path(path)

    assert table.is_hub_available("A", 1, 1) is False

def test_path_reserve_conn(table: ReservationTable) -> None:
    path = [("start", 0), ("A", 1), ("end", 2)]
    table.reserve_path(path)

    assert table.is_conn_available("start", "A", 0, 1) is False
    assert table.is_conn_available("A", "end", 1, 1) is False

def test_path_wait(table: ReservationTable) -> None:
    path = [("start", 0), ("A", 1), ("A", 2), ("end", 3)]
    table.reserve_path(path)

    assert table.is_conn_available("A", "end", 1, 1) is True

def test_path_restricted(table: ReservationTable) -> None:
    path = [("start", 0), ("A", 1), ("B", 3), ("end", 4)]
    table.reserve_path(path)

    assert table.is_transit_available("A", "B", 2, 1, 1) is False
    assert table.is_hub_available("B", 3, 1) is False

def test_path_reserve_conn(table: ReservationTable) -> None:
    path = [("start", 0), ("A", 1), ("end", 3)]
    table.reserve_path(path)

    assert table.is_hub_available("end", 3, 2) is True
