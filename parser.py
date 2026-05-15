"""
Class Parser parses CLI, validates and stores the map info.
Class ParseError for errors when parsing the map.
"""


from argparse import ArgumentParser, Namespace
from pydantic import ValidationError

from map import Map, Hub, Connection, ZoneType


class ParseError(Exception):
    """Errors related to parsing the map."""
    pass


class Parser:
    def __init__(self) -> None:
        self.args = self.parse_args()

    def parse_map(self) -> Map:
        """
        Parse the content of the map file
        into a Map object.
        """
        try:
            file = self._read_file()
            nb_drones = self._get_nb_drones(file)
            start = self._get_start_end_hub(file, nb_drones, True)
            end = self._get_start_end_hub(file, nb_drones, False, True)
            hubs = self._get_hubs(file, nb_drones, start, end)
            connections = self._get_connections(file, hubs, start, end)

            res = Map(
                nb_drones=nb_drones,
                start=start,
                end=end,
                hubs=hubs,
                connections=connections
            )
        except (ValueError, ValidationError, ParseError) as e:
            raise ParseError(e)

        return res

    def parse_args(self) -> Namespace:
        """
        Parse CLI. Accepted arguments:
        -m map file path. Default to easy/01.
        -v Toggle to show graphical interface.
        """
        parser_args = ArgumentParser(
            prog="python3 main.py"
        )

        parser_args.add_argument(
            "-m", "--map",
            default="maps/easy/01_linear_path.txt",
            help="Path to the map file."
        )

        parser_args.add_argument(
            "-v", "--visualize",
            action="store_true",
            help="Toggle to display the graphical interface."
        )

        return parser_args.parse_args()

    def _read_file(self) -> list[str]:
        """
        Read the file content line by line and store them into a dict.
        Lines starting with # are ignored.
        Return:
            A list of each content line of the file.
        """
        try:
            with open(self.args.map, "r") as file:
                lines = file.readlines()
        except FileNotFoundError:
            raise ParseError("FileNotFoundError: File "
                             f"'{self.args.map}' not found.")
        except PermissionError:
            raise ParseError("PermissionError: Cannot read "
                             f"file '{self.args.map}'.")
        except OSError:
            raise ParseError("OSError: An error occured when "
                             f"trying to open file '{self.args.map}'.")

        if not lines:
            raise ParseError(f"ParseError: File '{self.args.map}' is empty.")

        cleaned = self._clean_lines(lines)

        try:
            self._check_invalid_keys(cleaned)
        except ParseError as e:
            raise ParseError(e)

        return cleaned

    def _clean_lines(self, lines: list[str]) -> list[str]:
        """
        Remove comments from file content.
        """
        res: list[str] = []
        for line in lines:
            if line.startswith("#"):
                continue
            elif "#" in line:
                new_line = line.split("#")[0].strip()
                if new_line:
                    res.append(new_line)
            elif not line.strip():
                continue
            else:
                res.append(line.strip())

        return res

    def _check_invalid_keys(self, lines: list[str]) -> None:
        """
        Check if map contains invalid keys.
        Or if unqiue keys (start_hub, end_hub, nb_drones)
        are uniquely defined.
        """
        valid_keys = ["start_hub", "end_hub", "hub", "connection", "nb_drones"]

        count_start = 0
        count_end = 0
        count_drones = 0
        for line in lines:
            key = line.split(":")[0].strip()
            if key not in valid_keys:
                raise ParseError(f"ParseError: '{key}' is not a valid key.")
            if key == "start_hub":
                count_start += 1
            elif key == "end_hub":
                count_end += 1
            elif key == "nb_drones":
                count_drones += 1

        if count_start != 1:
            raise ParseError("ParseError: start_hub not uniquely defined.")
        if count_end != 1:
            raise ParseError("ParseError: end_hub not uniquely defined.")
        if count_drones != 1:
            raise ParseError("ParseError: nb_drones not uniquely defined.")

    def _get_nb_drones(self, lines: list[str]) -> int:
        """
        Get nb_drones from the first line.
        """
        if not lines[0].startswith("nb_drones"):
            raise ParseError("ParseError: The first line does not "
                             "define the number of drones.")
        try:
            res = int(lines[0].split(":")[1].strip())
        except ValueError:
            raise ParseError("ValueError: nb_drones setting "
                             "is not an integer.")
        return res

    def _get_start_end_hub(self, lines: list[str], nb_drones: int,
                           is_start: bool = False,
                           is_end: bool = False) -> Hub:
        """
        Get a the start or end hub from the map file.
        """
        if is_start:
            hub = "start_hub"
        elif is_end:
            hub = "end_hub"
        else:
            hub = "hub"

        if is_start or is_end:
            try:
                target_line = self._get_start_end_hub_line(lines, hub)
            except ParseError as e:
                raise ParseError(e)

        return self._process_hub_line(target_line, nb_drones,
                                      hub, is_start, is_end)

    def _get_start_end_hub_line(self, lines: list[str], hub: str) -> str:
        """
        Check whether start_hub or end_hub is uniquely defined
        and returns the line where it is defined.
        Raise a ParseError if the start or end hub is not uniquely defined.
        """
        count = 0
        for line in lines:
            if line.startswith(hub):
                count += 1
                target_line = line

        if count == 0:
            raise ParseError(f"ParseError: No {hub} defined.")
        if count > 1:
            raise ParseError(f"ParseError: Multiple {hub}s defined.")

        return target_line

    def _process_hub_line(self, line: str, nb_drones: int, hub: str = "hub",
                          is_start: bool = False, is_end: bool = False) -> Hub:
        """
        Process one line of hub definition and store them in a Hub object.
        """
        defs = line.split(":")[1].strip().split(maxsplit=3)
        if len(defs) != 3 and len(defs) != 4:
            raise ParseError(f"ParseError: {hub} '{line}' "
                             "not correctly defined.")

        hub_name = defs[0]
        try:
            x = int(defs[1])
        except ValueError:
            raise ParseError(f"ParseError: {hub} '{hub_name}' x coordinate "
                             "is not an integer.")

        try:
            y = int(defs[2])
        except ValueError:
            raise ParseError(f"ParseError: {hub} '{hub_name}' y coordinate "
                             "is not an integer.")

        zone_type = ZoneType.NORMAL
        max_drones = 1
        color = None
        if len(defs) == 4:
            if not defs[3].startswith("[") or not defs[3].endswith("]"):
                raise ParseError(f"ParseError: Invalid {hub} '{hub_name}' "
                                 "metadata definition.")

            metadata = defs[3].strip("[]").split()
            valid_metadata = ["color", "zone", "max_drones"]

            keys: list[str] = []
            for option in metadata:
                if len(option.split("=")) != 2:
                    raise ParseError(f"ParseError: Invalid {hub} '{hub_name}'"
                                     " metadata definition.")

                key, value = option.split("=")
                if key.strip() not in valid_metadata:
                    raise ParseError(f"ParseError: Invalid {hub} '{hub_name}'"
                                     " metadata definition.")
                if key in keys:
                    raise ParseError(f"ParseError: Metadata key '{key}' "
                                     "defined multiple times.")
                keys.append(key)
                if key.strip() == "zone":
                    zone_type = value
                elif key.strip() == "color":
                    color = value
                elif key.strip() == "max_drones":
                    try:
                        max_drones = int(value)
                    except ValueError:
                        raise ParseError("ParseError: max_drones definition "
                                         f"'{value}' for hub '{hub_name}' "
                                         "is not an integer.")

                if (is_start or is_end) and zone_type == ZoneType.BLOCK:
                    raise ParseError(f"ParseError: {hub}"
                                     "cannot be blocked.")

        try:
            res_hub = Hub(
                name=hub_name,
                x=x,
                y=y,
                is_start=is_start,
                is_end=is_end,
                zone_type=zone_type,
                max_drones=max_drones if not is_start and not is_end
                else nb_drones,
                color=color,
            )
        except (ValueError, ValidationError) as e:
            raise ParseError(e)
        return res_hub

    def _get_hubs(self, lines: list[str], nb_drones: int,
                  start: Hub, end: Hub) -> list[Hub]:
        """Get a list of hubs besides start and end hubs."""
        hubs: list[Hub] = []

        for line in lines:
            if line.startswith("hub"):
                try:
                    res_hub = self._process_hub_line(line, nb_drones)
                except ParseError as e:
                    raise ParseError(e)
                hubs.append(res_hub)

        if self._check_unique_hub(hubs, start, end):
            return hubs
        else:
            raise ParseError("ParseError: Hubs are not unique.")

    def _check_unique_hub(self, hubs: list[Hub],
                          start: Hub, end: Hub) -> bool:
        """
        Check if the hub are unique
        (no duplicated names for coordinates).
        Returns True if they are unique, False otherwise.
        """
        names: list[str] = []
        coordinates: list[tuple[int, int]] = []

        if start.name != end.name:
            names.append(start.name)
            names.append(end.name)
        else:
            return False

        if (start.x, start.y) != (end.x, end.y):
            coordinates.append((start.x, start.y))
            coordinates.append((end.x, end.y))
        else:
            return False

        for hub in hubs:
            if hub.name in names:
                return False
            names.append(hub.name)

            if (hub.x, hub.y) in coordinates:
                return False
            coordinates.append((hub.x, hub.y))

        return True

    def _get_connections(self, lines: list[str], hubs: list[Hub],
                         start: Hub, end: Hub) -> list[Connection]:
        """Get a list of connections defined in the map file."""
        connections: list[Connection] = []

        for line in lines:
            if line.startswith("connection"):
                try:
                    res_conn = self._process_conn_line(line, hubs, start, end)
                except ParseError as e:
                    raise ParseError(e)
                connections.append(res_conn)

        if not self._check_duplicate_connections(connections):
            raise ParseError("ParseError: Duplicate connections.")

        return connections

    def _process_conn_line(self, line: str, hubs: list[Hub],
                           start: Hub, end: Hub) -> Connection:
        """
        Process a line of connection definition
        and store it in a Connection object.
        """
        defs = line.split(":")[1].strip().split(maxsplit=1)

        if len(defs) != 1 and len(defs) != 2:
            raise ParseError(f"ParseError: Invalid connection '{line}' "
                             "definiton.")

        if len(defs[0].split("-")) != 2:
            raise ParseError(f"ParseError: Invalid connection '{line}' "
                             "definiton.")

        hub1_name, hub2_name = defs[0].split("-")

        src = None
        dest = None
        all_hubs = hubs + [start, end]
        for hub in all_hubs:
            if hub.name == hub1_name:
                src = hub
            elif hub.name == hub2_name:
                dest = hub

        if src is None:
            raise ParseError(f"ParseError: '{hub1_name}' "
                             "is not a defined hub.")
        if dest is None:
            raise ParseError(f"ParseError: '{hub2_name}' "
                             "is not a defined hub.")

        capacity = 1
        if len(defs) == 2:
            if not defs[1].startswith("[") or not defs[1].endswith("]"):
                raise ParseError(f"ParseError: Invalid connection '{line}' "
                                 "metadata definition.")

            metadata = defs[1].strip("[]").split()
            if len(metadata) > 1:
                raise ParseError(f"ParseError: Invalid connection '{line}' "
                                 "metadata definition.")
            if len(metadata) == 1:
                key, value = metadata[0].split("=")

                if key.strip() != "max_link_capacity":
                    raise ParseError("ParseError: Invalid connection "
                                     f"'{line}' "
                                     "metadata definition.")

                try:
                    capacity = int(value)
                except ValueError:
                    raise ParseError("ParseError: max_link_capacity "
                                     f"in '{line}' is not an integer.")

        try:
            return Connection(
                src=src,
                dest=dest,
                capacity=capacity
            )
        except (ValueError, ValidationError) as e:
            raise ParseError(e)

    def _check_duplicate_connections(self,
                                     connections: list[Connection]) -> bool:
        """
        Check if the connections contain duplicates.
        Returns True if connections are valid (no duplicates),
        False otherwise.
        """
        conns: list[tuple[str, str]] = []
        for conn in connections:
            c1 = (conn.src.name, conn.dest.name)
            c2 = (conn.dest.name, conn.src.name)
            if c1 in conns or c2 in conns:
                return False
            conns.append(c1)
            conns.append(c2)

        return True
