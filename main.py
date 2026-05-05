#!usr/bin/env python3


from parser import Parser, ParseError


def main() -> None:
    parser = Parser()

    try:
        map = parser.parse_map()
        if map.nb_drones == 0:
            return
    except ParseError as e:
        print(e)




if __name__ == "__main__":
    main()
