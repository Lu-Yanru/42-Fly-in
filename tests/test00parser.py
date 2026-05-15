import pytest
import sys

from parser import Parser, ParseError
from map import ZoneType
from unittest.mock import patch


class TestParser:
    GOOD_MAP: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    GOOD_MAP2: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green max_drones=1]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red zone=restricted] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    EMPTY_MAP: str = ""

    INVALID_KEYS: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub1   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub2: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    BLOCKED_START: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green zone=block]   \n"
        " hub1   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub2: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    BLOCKED_END: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub1   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub2: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red zone=block] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    NO_NB_DRONE: str = (
        "# Easy Level 1: Simple linear path\n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    INVALID_NB_DRONE: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 0  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    NB_DRONE_NOT_FIRST: str = (
        "# Easy Level 1: Simple linear path\n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        "nb_drones: 0  # simple comment \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    NO_START: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    DUP_START: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"

        "start_hub: start2 4 0 [color=green]   \n"
    )

    NO_END: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    DUP_END: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"

        "end_hub: end 4 0\n"
    )

    NO_HUB_NAME: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :   1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    INVALID_HUB_NAME: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    way-point1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    DUP_HUB_NAME: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    NO_POS: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    INVALID_POS: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 two 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    INVALID_METADATA_KEY: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    INVALID_METADATA_VALUE: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=forty-two  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    OVERLAP_HUB: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 1 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    INVALID_CONNECTION_HUB: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start1-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    INVALID_CONNECTION_DEF: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    INVALID_CONNECTION_ONE_HUB: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    INVALID_CONNECTION_THREE_HUBS: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: start-waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    DUP_CONNECTION: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-waypoint1  [   max_link_capacity=2 ]\n"
    )

    INVALID_CONN_META_KEY: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 [blabla=42]\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=2 ]\n"
    )

    INVALID_CONN_META_VALUE: str = (
        "# Easy Level 1: Simple linear path\n"
        "nb_drones: 2  # simple comment \n"
        "\n"
        "   # More comments\n"
        "   start_hub: start 0 0 [color=green]   \n"
        " hub   :    waypoint1 1 0 [color=blue  max_drones=2]\n"
        "hub: waypoint2 2 0 [  zone=restricted  color=blue   max_drones=2   ]\n"
        "end_hub  :  goal    3   0   [   color=red] \n"
        "   \n"
        "connection  :   start-waypoint1 []\n"
        "connection: waypoint1-waypoint2 [   ] \n"
        "   connection: waypoint2-goal  [   max_link_capacity=0 ]\n"
    )

    def test_no_file(self, monkeypatch) -> None:
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", ""])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_file_no_permission(self, monkeypatch) -> None:
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", "tests/test.txt"])
    
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(ParseError, match="PermissionError"):
                parser = Parser()
                parser.parse_map()

    def test_good_map(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "good_map.txt"
        map_file.write_text(self.GOOD_MAP)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        parser = Parser()
        res = parser.parse_map()
        assert res.nb_drones == 2
        assert res.start.name == "start"
        assert res.end.name == "goal"
        assert len(res.hubs) == 2
        assert len(res.connections) == 3

    def test_good_map2(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "good_map2.txt"
        map_file.write_text(self.GOOD_MAP2)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        parser = Parser()
        res = parser.parse_map()
        assert res.nb_drones == 2
        assert res.start.name == "start"
        assert res.start.max_drones == 2
        assert res.end.name == "goal"
        assert res.end.zone_type == ZoneType.RESTRICTED
        assert len(res.hubs) == 2
        assert len(res.connections) == 3

    def test_empty_map(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "empty_map.txt"
        map_file.write_text(self.EMPTY_MAP)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()

    def test_invalid_keys(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "invalid_keys.txt"
        map_file.write_text(self.INVALID_KEYS)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_blocked_start(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "blocked_start.txt"
        map_file.write_text(self.BLOCKED_START)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_blocked_end(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "blocked_end.txt"
        map_file.write_text(self.BLOCKED_END)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_no_nb_drones(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "no_nb_drones.txt"
        map_file.write_text(self.NO_NB_DRONE)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_invalid_nb_drones(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "invalid_nb_drones.txt"
        map_file.write_text(self.INVALID_NB_DRONE)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()

    def test_nb_drones_not_first(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "nb_drones_not_first.txt"
        map_file.write_text(self.NB_DRONE_NOT_FIRST)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_no_start(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "no_start.txt"
        map_file.write_text(self.NO_START)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_dup_start(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "dup_start.txt"
        map_file.write_text(self.DUP_START)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_no_end(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "no_end.txt"
        map_file.write_text(self.NO_END)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_dup_end(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "dup_end.txt"
        map_file.write_text(self.DUP_END)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_no_hub_name(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "no_hub_name.txt"
        map_file.write_text(self.NO_HUB_NAME)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()

    def test_invalid_hub_name(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "invalid_hub_name.txt"
        map_file.write_text(self.INVALID_HUB_NAME)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()

    def test_dup_hub_name(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "dup_hub_name.txt"
        map_file.write_text(self.DUP_HUB_NAME)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()

    def test_no_pos(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "no_pos.txt"
        map_file.write_text(self.NO_POS)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_invalid_pos(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "invalid_pos.txt"
        map_file.write_text(self.INVALID_POS)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_invalid_metadata_key(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "invalid_metadata_key.txt"
        map_file.write_text(self.INVALID_METADATA_KEY)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()

    def test_invalid_metadata_value(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "invalid_metadata_value.txt"
        map_file.write_text(self.INVALID_METADATA_VALUE)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()

    def test_overlap_hub(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "overlap_hub.txt"
        map_file.write_text(self.OVERLAP_HUB)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_invalid_connection_hub(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "invalid_connection_hub.txt"
        map_file.write_text(self.INVALID_CONNECTION_HUB)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()

    def test_invalid_connection_def(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "invalid_connection_def.txt"
        map_file.write_text(self.INVALID_CONNECTION_DEF)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()

    def test_invalid_conn_one_hub(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "invalid_conn_one_hub.txt"
        map_file.write_text(self.INVALID_CONNECTION_ONE_HUB)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()

    def test_invalid_conn_three_hubs(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "invalid_conn_three_hubs.txt"
        map_file.write_text(self.INVALID_CONNECTION_THREE_HUBS)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()

    def test_dup_conn(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "dup_conn.txt"
        map_file.write_text(self.DUP_CONNECTION)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_invalid_conn_meta_key(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "invalid_conn_meta_key.txt"
        map_file.write_text(self.INVALID_CONN_META_KEY)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
    
    def test_invalid_conn_meta_value(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "invalid_conn_meta_value.txt"
        map_file.write_text(self.INVALID_CONN_META_VALUE)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
