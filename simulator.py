"""
The Simulator class runs the simulation.
It uses a CAStarCoordinator to calculate the paths for each drone
and prints out formatted output on the terminal.
"""


import sys

from castar_coordinator import CAStarCoordinator, RoutingError
from graph import Graph, GraphError
from map import Map, ZoneType


# Symbols and ANSI escape sequences for colors.
# ANSI format: \033[ = escape character, followed by a code, ending with 'm'
class Style:
    # Text colors
    COLORS = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "gray": "\033[90m",
        "grey": "\033[90m",
        "orange":  "\033[38;5;214m",
        "purple":  "\033[38;5;129m",
        "pink":    "\033[38;5;213m",
        "brown":   "\033[38;5;130m",
        "maroon":  "\033[38;5;88m",
        "gold":    "\033[38;5;220m",
        "darkred": "\033[38;5;52m",
        "violet":  "\033[38;5;177m",
        "crimson": "\033[38;5;160m",
        "lime": "\033[38;5;118m",
    }

    BOLD = "\033[1m"

    # Resets all styles back to terminal default
    RESET = "\033[0m"


class Simulator:
    def __init__(self, map: Map, use_color: bool = True) -> None:
        """
        Create a Simulator with a Map object.
        Contains a Graph object and a CAStartCoordinator object
        and uses them to calculate a list of drone paths
        and the makespan.
        """
        self.use_color = use_color and sys.stdout.isatty()
        self._unsupported_color: set[str] = set()

        self.nb_drones = map.nb_drones
        self.graph = Graph(map)
        self.coordinator = CAStarCoordinator()

        try:
            self.coordinator.route_all_drones(map.nb_drones, self.graph)
            self.paths = self.coordinator.paths
            self.makespan = self.coordinator.get_makespan()
            self.turn_log = self._get_movements_in_turn()
        except (GraphError, RoutingError) as e:
            raise RoutingError(e)

    def print_log(self) -> None:
        """
        Prints out drone movements one turn per line
        based on the list of paths.
        """
        for turn, movements in self.turn_log.items():
            for idx, movement in enumerate(movements):
                print(movement, end="")
                if idx < len(movements) - 1:
                    print(" ", end="")
            print("")

    def compute_metrics(self) -> None:
        """
        Compute and print out metrics of the simulation,
        including total number of turns (makespan),
        number of drones moved per turn,
        average number of turns per drone,
        and total path cost.
        """
        print(self._style("\nMetrics:", Style.BOLD))
        print("Total number of turns:", self.makespan)

        avg_drone_per_turn = self._drone_moves_per_turn()
        print("Average number of drones moved per turn:",
              f"{avg_drone_per_turn:.2f}")

        sum_turns = 0
        for path in self.paths:
            sum_turns += path[-1][1]
        avg_turn_per_drone = sum_turns / self.nb_drones
        print("Average number of turns per drone:",
              f"{avg_turn_per_drone:.2f}")

        total_cost = self._calculate_total_path_cost()
        print("Total path cost:", f"{total_cost:.2f}")

    def _get_movements_in_turn(self) -> dict[int, list[str]]:
        """
        Get all movements in a turn from the list of paths.
        Return return a list of movements for each turn.
        Move to normal or priority zone
        or arrival at restricted zone: D<ID>-<zone>
        Move to connection to restricted zone: D<ID>-<connection>
        """
        turn_log: dict[int, list[str]] = {}

        for drone_idx, path in enumerate(self.paths):
            drone_id = drone_idx + 1

            for step_idx in range(1, len(path)):
                prev_zone, prev_turn = path[step_idx - 1]
                curr_zone, curr_turn = path[step_idx]

                # Skip waits
                if prev_zone == curr_zone:
                    continue

                # Restricted zone
                if curr_turn - prev_turn == 2:
                    # Mid-flight turn (prev_turn + 1) shows connection
                    transit_turn = prev_turn + 1
                    connection_label = (
                        f"D{drone_id}-{self._color_zone(prev_zone)}"
                        f"-{self._color_zone(curr_zone)}"
                    )
                    turn_log.setdefault(transit_turn,
                                        []).append(connection_label)

                # Normal move or arrival at restricted zone
                arrival_label = f"D{drone_id}-{self._color_zone(curr_zone)}"
                turn_log.setdefault(curr_turn, []).append(arrival_label)

        return turn_log

    # Color helpers
    def _color_zone(self, zone_name: str) -> str:
        """
        Return zone_name wrapped in ANSI color,
        or plain if unsupported or not specified.
        """
        zone = self.graph.get_hub(zone_name)
        if zone is None:
            return zone_name
        if zone.color is None:
            return zone_name
        zone_color = zone.color.lower()
        color = Style.COLORS.get(zone_color)
        if color is None:
            if zone_color not in self._unsupported_color:
                print(f"Color '{zone.color}' for zone '{zone_name}' "
                      "unsupported. Using the default color instead.",
                      file=sys.stderr)
                self._unsupported_color.add(zone_color)
            return zone_name
        return self._style(zone_name, color)

    def _style(self, text: str, *codes: str) -> str:
        """
        Wrap text in ANSI escape codes if color is enabled.
        Multiple codes can be added together.
        Always rests the style so not affect the next line.
        """
        if not self.use_color:
            return text
        return "".join(codes) + text + Style.RESET

    # Metrics helpers
    def _drone_moves_per_turn(self) -> float:
        """
        Caculate the average drone moves per turn,
        excluding waiting.
        Total number of drone moves / number of turns.
        """
        drone_moves_per_turn: dict[int, int] = {}
        for path in self.paths:
            for step_idx in range(1, len(path)):
                prev_zone, prev_turn = path[step_idx - 1]
                curr_zone, curr_turn = path[step_idx]
                if prev_zone == curr_zone:
                    continue
                if self.graph.get_hub(curr_zone).zone_type \
                        == ZoneType.RESTRICTED:
                    move = 2
                else:
                    move = 1
                drone_moves_per_turn[prev_turn + 1] = (
                    drone_moves_per_turn.get(prev_turn + 1, 0) + move
                )

        total_moves = sum(drone_moves_per_turn.values())
        return total_moves / self.makespan

    def _calculate_total_path_cost(self) -> float:
        """
        Calcualte the total path cost
        (sum of weighted movement costs across all drones).
        """
        total_cost = 0.0
        for drone in self.paths:
            for zone, turn in drone:
                if turn == 0:
                    continue
                type = self.graph.get_hub(zone).zone_type
                if type == ZoneType.PRIORITY:
                    total_cost += 0.9
                elif type == ZoneType.RESTRICTED:
                    total_cost += 2.0
                else:
                    total_cost += 1.0
        return total_cost
