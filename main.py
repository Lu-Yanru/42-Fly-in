#!usr/bin/env python3


import sys
from parser import Parser, ParseError


def main() -> None:
    parser = Parser()

    try:
        map = parser.parse_map()
    except ParseError as e:
        print(e, file=sys.stderr)


if __name__ == "__main__":
    main()
