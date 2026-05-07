import pytest
import sys

from parser import Parser, ParseError
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

    EMPTY_MAP: str = ""

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

    def test_empty_map(self, tmp_path, monkeypatch) -> None:
        map_file = tmp_path / "empty_map.txt"
        map_file.write_text(self.EMPTY_MAP)
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", str(map_file)])

        with pytest.raises(ParseError):
            parser = Parser()
            parser.parse_map()
