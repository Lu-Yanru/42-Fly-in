#!usr/bin/env python3


import sys
from parser import Parser, ParseError
from graph import Graph, GraphError
from castar_coordinator import CAStarCoordinator, RoutingError


def main() -> None:
    parser = Parser()

    try:
        map = parser.parse_map()
        graph = Graph(map)
        castar = CAStarCoordinator()
        castar.route_all_drones(map.nb_drones, graph)
        print("Total turns: ", castar.get_makespan())
    except ParseError as e:
        print(e, file=sys.stderr)
    except GraphError as e:
        print(e, file=sys.stderr)
    except RoutingError as e:
        print(e, file=sys.stderr)
    except Exception as e:
        print("An unexpected error occured: ", e, file=sys.stderr)


if __name__ == "__main__":
    main()
