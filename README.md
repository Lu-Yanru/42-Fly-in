*This project has been created as part of the 42 curriculum by yanlu.*

# Fly-in
## Description
This project implements an efficient drone routing system. It reads a map file representing a network of zones (hubs), and navigates a fleet of drones from a central **start hub** to a target **end hub** in the fewest possible simulation turns.

### Constraints

#### Map
- Start and end zones are unique.
- Zone types:
    - normal – Standard zone with 1 turn movement cost (default)
    - blocked – Inaccessible zone. Drones must not enter or pass through this zone. Any path using it is invalid.
    - restricted – A sensitive or dangerous zone. Movement to this zone costs 2 turns.
    - priority – A preferred zone. Movement to this zone costs 1 turn but should be prioritized in pathfinding.
- A zone may contain up to `max_drones` (default 1) simultanously. Except for start and end zone, which can be contain all drones at the same time.
- Connections (edges) connects two zones and are bidirectional.
- Up to `max_link_capacity` (default 1) may traverse the same connection simultaneously.

#### Movement
- The simulation proceeds in discrete turns. In each turn, every drone may:
    - Move to an adjacent connected zone, respecting the capacity constraint.
    - Move to a connection towards a restricted zone. In this case, this drone must reach the restricted drone in the next turn and cannot wait on the connection.
    - Wait in place.
- Drones may move simultaneously.
- Drones moving out of a zone free up capacity for that same turn.
- The simulation ends when all drones have reached the end zone.

### Algorithm

### Visualization
The step-by-step movements of the drones are visualized in the following formats:

#### Terminal output
The colored terminal output shows drone movement steps and zone states.

Each simulation turn is represented bz a line. A line lists all drone movements in this turn ins the following format:

    # Drone id - name
    D<ID>-<zone>
    # or 
    D<ID>-<connection>

Drones that do not move in a given turn are omitted from that line.
Drones that reach the end zone are considered delivered and are no longer tracked.

Example:

    D1-roof1 D2-corridorA
    D1-roof2 D2-tunnelB
    D1-goal D2-goal

#### Graphical interface
To enhance the user experience, a graphical interface is also implemented which displays the network and drone positions.

### Benchmarks

| Difficulty | Map | Target | Status |
| 🟢 Easy | Linear path with 2 drones | ≤ 6 turns | ✅ |
| 🟢 Easy | Simple fork with 3 drones | ≤ 6 turns | ✅ |
| 🟢 Easy | Basic capacity with 4 drones | ≤ 8 turns | ✅ |
| 🟡 Medium | Dead end trap with 5 drones | ≤ 15 turns | ✅ |
| 🟡 Medium | Circular loop with 6 drones | ≤ 20 turns | ✅ |
| 🟡 Medium | Priority puzzle with 4 drones | ≤ 12 turns | ✅ |
| 🔴 Hard | Maze nightmare with 8 drones | ≤ 45 turns | ✅ |
| 🔴 Hard | Capacity hell with 12 drones | ≤ 60 turns | ✅ |
| 🔴 Hard | Ultimate challenge with 15 drones | ≤ 35 turns | ✅ |
| 🏆 Challenger | The Impossible Dream with 25 drones | ≤ 45 turns | ✅ |

## Instructions
This project uses `uv` for dependency management and a `Makefile` to automate common tasks.

### Prerequisites
- Python >= 3.13
- uv >= 0.9.16

### Running the project
Install project dependencies:

    make install

Execute the project:

    make run

Select map file path:

    uv run python main.py -m map_file_path

Visualize with the graphical interface:

    make visualize

Run the script in debug mode using `pdb`:

    make debug

Code linting using `flake8` and `mypy`:

    make lint

Remove temporary files and caches:

    make clean

### Map file format
Example:

    nb_drones: 5

    start_hub: hub 0 0 [color=green]
    end_hub: goal 10 10 [color=yellow]
    hub: roof1 3 4 [zone=restricted color=red]
    hub: roof2 6 2 [zone=normal color=blue]
    hub: corridorA 4 3 [zone=priority color=green max_drones=2]
    hub: tunnelB 7 4 [zone=normal color=red]
    hub: obstacleX 5 5 [zone=blocked color=gray]
    connection: hub-roof1
    connection: hub-corridorA
    connection: roof1-roof2
    connection: roof2-goal
    connection: corridorA-tunnelB [max_link_capacity=2]
    connection: tunnelB-goal

Rules:
- The first line must define the number of drones in the format `nb_drones: <number>`. Drone number has to be positive.
- Each zone is defined on one line in the following format:
    - The start zone: `start_hub: <name> <x> <y> [metadata]`
    - The end zone: `end_hub: <name> <x> <y> [metadata]`
    - A regular zone: `hub: <name> <x> <y> [metadata]`
    - `start_hub` and `end_hub` must be unique.
    - Zone coordinates must be integers.
    - Zone names must be unique and do not contain dashes or spaces.
- Connections are defined using `connection: <hub1_name>-<hub2_name> [metadata]`.
    - Connections reference only previously defined zones.
    - Duplicate connections (`a-b` and `b-a`) are forbidden.
- All metadata is optional and enclosed in brackets `[]` with default values. Metadata tags can appear in any order.
    - Zone type: `zone=<type>` (default: `normal`). Must be one of: `normal, blocked, restricted, priority`.
    - The color of the visual representation: `color=<value>` (default: `none`). Accepts any valid single-word strings. Fall back to default if the color is not defined.
    - Maximum drones that can occupy this
zone simultaneously: `max_drones=<number>` (default: `1`). Must be a positive integer.
    - Maximum drones that can
traverse this connection simultaneously: `max_link_capacity=<number>` (default: `1`). Must be a positive integer.
- Comments start with `#` are ignored.

## Resources