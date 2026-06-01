#!usr/bin/env python3


import sys

from castar_coordinator import RoutingError
from graph import GraphError
from parser import Parser, ParseError
from simulator import Simulator
from visualizer import Visualizer


def main() -> None:
    parser = Parser()

    try:
        map = parser.parse_map()
        simulator = Simulator(map)
        simulator.print_log()
        simulator.compute_metrics()
        if parser.args.visualize:
            visualizer = Visualizer(map, simulator)
            visualizer.visualize()
    except ParseError as e:
        print(e, file=sys.stderr)
    except GraphError as e:
        print(e, file=sys.stderr)
    except RoutingError as e:
        print(e, file=sys.stderr)
    except KeyboardInterrupt:
        print("Interrupted by user.", file=sys.stderr)
    except Exception as e:
        print("An unexpected error occured: ", e, file=sys.stderr)


if __name__ == "__main__":
    main()
