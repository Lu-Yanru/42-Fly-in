"""
Tests for Simulator

Strategy: Mock Map, Graph, and CAStarCoordinator so we can inject paths and
zones directly without needing a real map file or running the routing pipeline.
"""


import pytest
from unittest.mock import MagicMock, patch

from simulator import Simulator, Style
from map import Hub, ZoneType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_hub(name: str, x: int = 0, y: int = 0, zone_type: ZoneType = ZoneType.NORMAL, max_drones: int = 1) -> Hub:
    return Hub(name=name, x=x, y=y, zone_type=zone_type, max_drones=max_drones)


def make_simulator(
    paths: list[list[tuple[str, int]]],
    zones: dict[str, Hub],
    nb_drones: int | None = None,
) -> Simulator:
    """
    Build a Simulator with injected paths and zones, bypassing Map and routing.
    """
    mock_map = MagicMock()
    mock_map.nb_drones = nb_drones if nb_drones is not None else len(paths)

    mock_graph = MagicMock()
    mock_graph.zones = zones

    mock_coordinator = MagicMock()
    mock_coordinator.paths = paths
    mock_coordinator.get_makespan.return_value = (
        max(path[-1][1] for path in paths) if paths else 0
    )

    with (
        patch("simulator.Graph", return_value=mock_graph),
        patch("simulator.CAStarCoordinator", return_value=mock_coordinator),
    ):
        sim = Simulator(mock_map)

    return sim


# ---------------------------------------------------------------------------
# Log output tests
# ---------------------------------------------------------------------------

class TestPrintSimulationLog:

    def test_single_drone_normal_move(self, capsys: pytest.CaptureFixture[str]) -> None:
        """A single normal move prints D1-<zone> on the correct turn."""
        zones = {
            "start": make_hub("start"),
            "end":   make_hub("end"),
        }
        paths = [[("start", 0), ("end", 1)]]
        sim = make_simulator(paths, zones)
        sim.print_log()

        out = capsys.readouterr().out
        assert "D1-end" in out

    def test_single_drone_wait_is_omitted(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Wait steps (same zone, consecutive turns) are not printed."""
        zones = {
            "start": make_hub("start"),
            "end":   make_hub("end"),
        }
        # Drone waits at start on turn 1, then moves to end on turn 2
        paths = [[("start", 0), ("start", 1), ("end", 2)]]
        sim = make_simulator(paths, zones)
        sim.print_log()

        out = capsys.readouterr().out
        # Turn 1 should not appear (only a wait happened)
        assert "D1-start" not in out
        assert "D1-end" in out

    def test_restricted_zone_transit(self, capsys: pytest.CaptureFixture[str]) -> None:
        """
        Restricted move: transit turn shows D<ID>-<from>-<to>,
        arrival turn shows D<ID>-<to>.
        """
        zones = {
            "start":    make_hub("start"),
            "rzone":    make_hub("rzone", zone_type=ZoneType.RESTRICTED),
        }
        # Turn gap of 2 signals restricted transit
        paths = [[("start", 0), ("rzone", 2)]]
        sim = make_simulator(paths, zones)
        sim.print_log()

        out = capsys.readouterr().out
        assert "Turn 1:" in out
        assert "D1-start-rzone" in out
        assert "Turn 2:" in out
        assert "D1-rzone" in out

    def test_multiple_drones_same_turn(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Multiple drones moving in the same turn all appear under that turn."""
        zones = {
            "start": make_hub("start"),
            "a":     make_hub("a"),
            "b":     make_hub("b"),
        }
        paths = [
            [("start", 0), ("a", 1)],
            [("start", 0), ("b", 1)],
        ]
        sim = make_simulator(paths, zones)
        sim.print_log()

        out = capsys.readouterr().out
        assert "Turn 1:" in out
        assert "D1-a" in out
        assert "D2-b" in out

    def test_drone_not_shown_after_delivery(self, capsys: pytest.CaptureFixture[str]) -> None:
        """A drone that arrives early does not appear in later turns."""
        zones = {
            "start": make_hub("start"),
            "end":   make_hub("end"),
            "mid":   make_hub("mid"),
        }
        paths = [
            [("start", 0), ("end", 1)],           # arrives turn 1
            [("start", 0), ("mid", 1), ("end", 2)],
        ]
        sim = make_simulator(paths, zones)
        sim.print_log()

        out = capsys.readouterr().out
        lines = out.splitlines()

        # Find turn 2 block and confirm D1 is absent
        turn2_idx = next(i for i, l in enumerate(lines) if "Turn 2:" in l)
        turn2_content = "\n".join(lines[turn2_idx:])
        assert "D1-" not in turn2_content.split("Turn 3:")[0]

    def test_empty_turns_are_skipped(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Turns where no drone moves are not printed at all."""
        zones = {
            "start": make_hub("start"),
            "end":   make_hub("end"),
        }
        # Drone waits turns 1–2, moves on turn 3
        paths = [[("start", 0), ("start", 1), ("start", 2), ("end", 3)]]
        sim = make_simulator(paths, zones)
        sim.print_log()

        out = capsys.readouterr().out
        assert "Turn 1:" not in out
        assert "Turn 2:" not in out
        assert "Turn 3:" in out

    def test_multi_hop_path(self, capsys: pytest.CaptureFixture[str]) -> None:
        """A drone traversing multiple zones appears once per turn."""
        zones = {
            "start": make_hub("start"),
            "mid":   make_hub("mid"),
            "end":   make_hub("end"),
        }
        paths = [[("start", 0), ("mid", 1), ("end", 2)]]
        sim = make_simulator(paths, zones)
        sim.print_log()

        out = capsys.readouterr().out
        assert "Turn 1:" in out
        assert "D1-mid" in out
        assert "Turn 2:" in out
        assert "D1-end" in out


# ---------------------------------------------------------------------------
# Color coding tests
# ---------------------------------------------------------------------------

class TestColorZone:

    def test_known_color_wraps_zone_name(self) -> None:
        """A zone with a supported color wraps the name in ANSI codes."""
        zones = {"alpha": make_hub("alpha", color="red")}
        sim = make_simulator([[("alpha", 0), ("alpha", 1)]], zones)

        result = sim._color_zone("alpha")
        assert result == f"{ANSI_COLORS['red']}alpha{ANSI_RESET}"

    def test_no_color_returns_plain(self) -> None:
        """A zone with no color returns the plain zone name."""
        zones = {"alpha": make_hub("alpha", color="")}
        sim = make_simulator([[("alpha", 0), ("alpha", 1)]], zones)

        assert sim._color_zone("alpha") == "alpha"

    def test_unsupported_color_returns_plain(self) -> None:
        """A zone with an unsupported color returns the plain zone name."""
        zones = {"alpha": make_hub("alpha", color="chartreuse")}
        sim = make_simulator([[("alpha", 0), ("alpha", 1)]], zones)

        assert sim._color_zone("alpha") == "alpha"

    def test_unsupported_color_prints_warning(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An unsupported color prints a warning message."""
        zones = {"alpha": make_hub("alpha", color="chartreuse")}
        sim = make_simulator([[("alpha", 0), ("alpha", 1)]], zones)

        sim._color_zone("alpha")
        out = capsys.readouterr().out
        assert "Warning" in out
        assert "chartreuse" in out
        assert "alpha" in out

    def test_unsupported_color_warning_printed_once(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Warning for an unsupported color is printed only once per zone."""
        zones = {"alpha": make_hub("alpha", color="chartreuse")}
        sim = make_simulator([[("alpha", 0), ("alpha", 1)]], zones)

        sim._color_zone("alpha")
        sim._color_zone("alpha")
        sim._color_zone("alpha")
        out = capsys.readouterr().out
        assert out.count("Warning") == 1

    def test_two_zones_unsupported_each_warn_once(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Each zone with an unsupported color gets exactly one warning."""
        zones = {
            "alpha": make_hub("alpha", color="chartreuse"),
            "beta":  make_hub("beta",  color="ultraviolet"),
        }
        sim = make_simulator([[("alpha", 0), ("alpha", 1)]], zones)

        for _ in range(3):
            sim._color_zone("alpha")
            sim._color_zone("beta")

        out = capsys.readouterr().out
        assert out.count("Warning") == 2

    def test_color_lookup_is_case_insensitive(self) -> None:
        """Color names are matched case-insensitively."""
        zones = {"alpha": make_hub("alpha", color="RED")}
        sim = make_simulator([[("alpha", 0), ("alpha", 1)]], zones)

        result = sim._color_zone("alpha")
        assert result == f"{ANSI_COLORS['red']}alpha{ANSI_RESET}"

    def test_unknown_zone_returns_plain(self) -> None:
        """A zone name not in the graph returns the plain name without error."""
        sim = make_simulator([[("start", 0), ("start", 1)]], {})
        assert sim._color_zone("nonexistent") == "nonexistent"

    def test_colored_zone_appears_in_log(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Zone color codes appear in the printed log output."""
        zones = {
            "start": make_hub("start"),
            "dest":  make_hub("dest", color="blue"),
        }
        paths = [[("start", 0), ("dest", 1)]]
        sim = make_simulator(paths, zones)
        sim.print_log()

        out = capsys.readouterr().out
        assert ANSI_COLORS["blue"] in out
        assert ANSI_RESET in out

    def test_restricted_transit_both_zones_colored(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Both zone names in a restricted transit label are individually colored."""
        zones = {
            "start": make_hub("start", color="green"),
            "rzone": make_hub("rzone", zone_type=ZoneType.RESTRICTED, color="red"),
        }
        paths = [[("start", 0), ("rzone", 2)]]
        sim = make_simulator(paths, zones)
        sim.print_log()

        out = capsys.readouterr().out
        assert ANSI_COLORS["green"] in out
        assert ANSI_COLORS["red"] in out


# ---------------------------------------------------------------------------
# Metrics tests
# ---------------------------------------------------------------------------

class TestComputeMetrics:

    def test_drones_moved_per_turn_single_drone(self) -> None:
        """Single drone moving each turn increments count correctly."""
        zones = {
            "start": make_hub("start"),
            "mid":   make_hub("mid"),
            "end":   make_hub("end"),
        }
        paths = [[("start", 0), ("mid", 1), ("end", 2)]]
        sim = make_simulator(paths, zones)
        metrics = sim._compute_metrics()

        assert metrics.drones_moved_per_turn == {1: 1, 2: 1}

    def test_drones_moved_per_turn_multiple_drones(self) -> None:
        """Two drones moving in the same turn count as 2."""
        zones = {
            "start": make_hub("start"),
            "a":     make_hub("a"),
            "b":     make_hub("b"),
        }
        paths = [
            [("start", 0), ("a", 1)],
            [("start", 0), ("b", 1)],
        ]
        sim = make_simulator(paths, zones)
        metrics = sim._compute_metrics()

        assert metrics.drones_moved_per_turn.get(1) == 2

    def test_drones_moved_excludes_wait_turns(self) -> None:
        """A wait step does not count as a drone moved."""
        zones = {
            "start": make_hub("start"),
            "end":   make_hub("end"),
        }
        paths = [[("start", 0), ("start", 1), ("end", 2)]]
        sim = make_simulator(paths, zones)
        metrics = sim._compute_metrics()

        assert metrics.drones_moved_per_turn.get(1, 0) == 0
        assert metrics.drones_moved_per_turn.get(2) == 1

    def test_average_turns_single_drone(self) -> None:
        """Average turns equals path length for a single drone."""
        zones = {
            "start": make_hub("start"),
            "end":   make_hub("end"),
        }
        paths = [[("start", 0), ("end", 3)]]
        sim = make_simulator(paths, zones)
        metrics = sim._compute_metrics()

        assert metrics.average_turns_per_drone == pytest.approx(3.0)

    def test_average_turns_multiple_drones(self) -> None:
        """Average turns is the mean of each drone's elapsed turns."""
        zones = {
            "start": make_hub("start"),
            "end":   make_hub("end"),
        }
        paths = [
            [("start", 0), ("end", 2)],   # 2 turns
            [("start", 0), ("end", 4)],   # 4 turns
        ]
        sim = make_simulator(paths, zones)
        metrics = sim._compute_metrics()

        assert metrics.average_turns_per_drone == pytest.approx(3.0)

    def test_total_cost_normal_moves(self) -> None:
        """Normal zone moves each cost 1.0."""
        zones = {
            "start": make_hub("start"),
            "mid":   make_hub("mid", zone_type=ZoneType.NORMAL),
            "end":   make_hub("end", zone_type=ZoneType.NORMAL),
        }
        paths = [[("start", 0), ("mid", 1), ("end", 2)]]
        sim = make_simulator(paths, zones)
        metrics = sim._compute_metrics()

        assert metrics.total_path_cost == pytest.approx(2.0)

    def test_total_cost_restricted_move(self) -> None:
        """Restricted zone move costs 2.0."""
        zones = {
            "start": make_hub("start"),
            "rzone": make_hub("rzone", zone_type=ZoneType.RESTRICTED),
        }
        paths = [[("start", 0), ("rzone", 2)]]
        sim = make_simulator(paths, zones)
        metrics = sim._compute_metrics()

        assert metrics.total_path_cost == pytest.approx(2.0)

    def test_total_cost_priority_move(self) -> None:
        """Priority zone move costs 0.9."""
        zones = {
            "start":  make_hub("start"),
            "pzone":  make_hub("pzone", zone_type=ZoneType.PRIORITY),
        }
        paths = [[("start", 0), ("pzone", 1)]]
        sim = make_simulator(paths, zones)
        metrics = sim._compute_metrics()

        assert metrics.total_path_cost == pytest.approx(0.9)

    def test_total_cost_wait_adds_one(self) -> None:
        """Each wait step adds 1.0 to total cost."""
        zones = {
            "start": make_hub("start"),
            "end":   make_hub("end"),
        }
        # One wait, one normal move
        paths = [[("start", 0), ("start", 1), ("end", 2)]]
        sim = make_simulator(paths, zones)
        metrics = sim._compute_metrics()

        assert metrics.total_path_cost == pytest.approx(2.0)  # 1 wait + 1 move

    def test_total_cost_mixed_moves(self) -> None:
        """Mixed move types sum correctly across multiple drones."""
        zones = {
            "start":  make_hub("start"),
            "normal": make_hub("normal", zone_type=ZoneType.NORMAL),
            "pzone":  make_hub("pzone",  zone_type=ZoneType.PRIORITY),
            "rzone":  make_hub("rzone",  zone_type=ZoneType.RESTRICTED),
        }
        paths = [
            [("start", 0), ("normal", 1)],        # cost 1.0
            [("start", 0), ("pzone",  1)],         # cost 0.9
            [("start", 0), ("rzone",  2)],         # cost 2.0
        ]
        sim = make_simulator(paths, zones)
        metrics = sim._compute_metrics()

        assert metrics.total_path_cost == pytest.approx(3.9)

    def test_metrics_printed_after_log(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Metrics section appears in output after the movement log."""
        zones = {
            "start": make_hub("start"),
            "end":   make_hub("end"),
        }
        paths = [[("start", 0), ("end", 1)]]
        sim = make_simulator(paths, zones)
        sim.print_log()

        out = capsys.readouterr().out
        log_pos     = out.find("Turn 1:")
        metrics_pos = out.find("Simulation Metrics")
        assert log_pos < metrics_pos

    def test_metrics_contain_no_ansi_codes(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Metrics section contains no ANSI color codes."""
        zones = {
            "start": make_hub("start", color="red"),
            "end":   make_hub("end",   color="blue"),
        }
        paths = [[("start", 0), ("end", 1)]]
        sim = make_simulator(paths, zones)
        sim.print_log()

        out = capsys.readouterr().out
        metrics_section = out.split("Simulation Metrics")[-1]
        assert "\033[" not in metrics_section
