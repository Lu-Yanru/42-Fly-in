#!usr/bin/env python3


import sys
from parser import Parser, ParseError
from graph import Graph, GraphError


def main() -> None:
    parser = Parser()

    try:
        map = parser.parse_map()
        graph = Graph(map)
        heuristic = graph.reverse_dijkstra()
        print(heuristic)
    except ParseError as e:
        print(e, file=sys.stderr)
    except GraphError as e:
        print(e, file=sys.stderr)


if __name__ == "__main__":
    main()
