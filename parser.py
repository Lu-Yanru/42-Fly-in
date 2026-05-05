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
        file = self._read_file()

        try:
            res = Map(
                nb_drones = self._get_nb_drones(file),
                # start,
                # end,
                # hubs,
                # connections
            )
        except (ValueError, ValidationError) as e:
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
            raise ParseError(f"FileNotFoundError: File '{self.args.map}' not found.")
        except PermissionError:
            raise ParseError(f"PermissionError: Cannot read file '{self.args.map}'.")
        except OSError:
            raise ParseError("OSError: An error occured when "
                             f"trying to open file '{self.args.map}'.")
        
        if not lines:
            raise ParseError(f"ParseError: File '{self.args.map}' is empty.")
        
        return self._clean_lines(lines)

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

    def _get_nb_drones(self, lines: list[str]) -> int:
        """
        Get nb_drones from the first line.
        """
        if not lines[0].startswith("nb_drones"):
            raise ParseError("ParseError: The first line does not define the number of drones.")
        try:
            res = int(lines[0].split(":")[1].strip())
        except ValueError:
            raise ParseError("ValueError: nb_drones setting is not an integer.")
        return res
