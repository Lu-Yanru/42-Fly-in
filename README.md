*This project has been created as part of the 42 curriculum by yanlu.*

# Fly-in
## Description
This project implements an efficient drone routing system. It reads a map file representing a network of zones (hubs), and navigates a fleet of drones from a central **start hub** to a target **end hub** in the fewest possible simulation turns.

This is essentially a [multi-agent pathfinding (MAPF)](https://en.wikipedia.org/wiki/Multi-agent_pathfinding) problem with capacity constraints.

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
This project implements the **Cooperative A* (CA*)** algorithm. CA* routes drones one at a time through a space-time graph. After each drone is routed, its path is recorded in a shared reservation table, and the next drone treats those reservations as obstacles.

#### Space-time graph
A **space-time graph** extends each node with a time dimension, with each node being (zone, turn) pair. This means the same physical zone appears as a different node at each turn, e.g. `(A, 1)`, `(A, 2)`, `(A, 3)`. This allows the algorithm to reason about when a drone is somewhere and not just where it is.

The nodes are generated on the fly as A* expands the frontier and never for all the zones. This keeps the memory usage low.

The edges represents movements of the drones: `(zone, t) -> (neighbor, t + move_cost)`

Move costs are based on zone/movement types:
|Zone/movement type  | Cost |
|-----------|------|
|Normal     |1     |
|Restricted |2     |
|Priority   |0.9 (slightly preferred) |
|Block      |-- (no edge going to this node) |
|Wait       |1     |

#### Reservation table
The reservation table is a shared dictionary updated after each drone is routed. It records how many drones occupy each `(zone, turn)` cell and each `(connection, turn)` cell. When routing, any node that would exceed its capacity limit is treated as a wall so that the drone cannot go there.

Three types of reservations are maintained:

- Zone reservation:       `(zone, turn)`
- Connection reservation: `(zone_a, zone_b, turn)`
- Transit reservation:    `(from_zone, to_zone, turn)`

Transit reservations handle the restricted zone commit rule: a drone entering transit toward a restricted zone reserves the mid-transit cell, preventing another drone from entering the same connection simultaneously, and the destination cell is checked at planning time to ensure it will be free on arrival.

#### A* search algorithm
Each drone is routed using the **A*** algorithm to find the shortest path from start to end hub on the space-time graph respecting capacity constraints in the reservation table.

A* is an extension of Dijkstra's algorithm guided by a heuristic (an estimate used to make a decision faster, in the context of pathfinding, an estimate of how far a node is from the goal), which makes it incomplete (may not explore all nodes), but faster because of that.

A* maintains:
- A priority queue of nodes to explore, ordered by `f = g + h`. The node with the lowest `f` will be explored next.
    - `g`: The actual cost from `(start, 0)` to the current node.
    - `h`: The heuristic from the current node to the end node. This is commonly the Eucliean distance between the current node and the end node in pathfinding. But in this case, the acutal distance between zones do not matter, only the zone types and number of turns. Therefore, the estimated cost is the fewest number of turns it takes from the current node to the end node. This is calculated by running a reverse Dijktra from the end zone once at the beginning, ignoring all other drones. This gives us the the minimum number of turns (costs) from every zone to the end zone.
- A visited/cost record that tracks the best known `g` cost to reach each node, and which node it came from, so the path can be reconstructed at the end.

- Step 1: Initialize by adding the start node to the priority queue and the visited/cost record.
- Step 2: Calculate `f` for the neighboring nodes and add them to the priority queue, add new zones to the visited/cost record.
- Step 3: Find neighbors of the node with the highest priority.
- Step 4: Repeate step 2 and 3 until the end node is reached.
- Step 5: Trace back the shortest path from the visited/cost record.

#### Optimality and efficiency analysis
- Time complexity: `O(K × (V·T) × log(V·T))`
- Space complexity: `O(K × T)`

where:
- `V` = number of nodes
- `E` = number of edges
- `T` = turn horizon (maximum number of search turns before giving up on the search)
- `K` = number of drones

**Pros:**

- The reservation table naturally handles capacity constraints and avoids conflicts (in comparison to simple shortest path algorithms such as Dijkstra's algorithm or A*).
- Efficient, less time and space complexity compared to optimal but complex algorithms such as Conflict-Based Search (CBS) or Time-Expanded Graph + shortest path algorithms.

**Cons:**

- Suboptimal because CA* is priority-ordered, i.e. it routes drones sequentially, and the order matters. The first drone gets its globally optimal path. Every subsequent drone gets the best path given the reservations left by earlier drones, but that local optimum may not be globally optimal.

CA* offers a balanced solution between optimality, efficiency and implementation complexity. In practice, due to constraints of this project (all drones are the same, unique start and end hub means drones will always go towards the same direction), CA* finds the optimal solution in most cases and reliably meets the benchmarks. Thus, CA* is suitable for this project.

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
To enhance the user experience, a graphical interface which displays the network and drone positions is also implemented using the `pygame` library.

##### Layout
The hubs are represented as circles colored with their defined colors in the map file. If no color is specified for the specified color is not supported, gray is used as default.

The positions and sized of the hubs are calculated relative to the window center, so the network is always centered and all hubs can fit inside the window.

The abbreviated hub names are shown in the center of the circle.

#### Animation
Drones are represented as triangles that moves along the connections from hub to hub. The colors of the drones are calculated using drone_id in a loop. The drone positions are calculated so that they are always facing the destination hub. The animation speed can be adjusted by passing an argument to the `Visualizer` class (0.0 to 1.0).

The occupancy/max_capacity information are added as labels next to the hubs and connections to better monitor the capacity cosntraints. The occupancy information is updated every turn.

#### UI
Play/resume button
per turn prev/next
replay button

### Benchmarks

| Difficulty | Map | Target | Result |
|------------|-----|--------|--------|
| 🟢 Easy | Linear path with 2 drones | ≤ 6 turns | ✅ 4 turns|
| 🟢 Easy | Simple fork with 4 drones | ≤ 8 turns | ✅ 4 turns|
| 🟢 Easy | Basic capacity with 4 drones | ≤ 6 turns | ✅ 4 turns|
| 🟡 Medium | Dead end trap with 5 drones | ≤ 12 turns | ✅ 8 turns|
| 🟡 Medium | Circular loop with 6 drones | ≤ 15 turns | ✅ 10 turns|
| 🟡 Medium | Priority puzzle with 5 drones | ≤ 12 turns | ✅ 6 turns|
| 🔴 Hard | Maze nightmare with 8 drones | ≤ 30 turns | ✅ 13 turns|
| 🔴 Hard | Capacity hell with 12 drones | ≤ 35 turns | ✅ 16 turns|
| 🔴 Hard | Ultimate challenge with 15 drones | ≤ 45 turns | ✅ 26 turns|
| 🏆 Challenger | The Impossible Dream with 25 drones | ≤ 45 turns | ✅ 43 turns|

## Instructions
This project uses `uv` for dependency management and a `Makefile` to automate common tasks.

### Prerequisites
- Python >= 3.13
- uv >= 0.9.16

### Running the project
Install project dependencies:

    make install

Execute the project with default map:

    make run

Select map file path:

    uv run python main.py -m map_file_path

Visualize with the graphical interface with default map:

    make visualize

Select map file + visualization:

    uv run python main.py -m map_file_path -v

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
- [Youtube Graph Theory Playlist by WilliamFiset](https://www.youtube.com/playlist?list=PLDV1Zeh2NRsDGO4--qE8yH72HFL1Km93P)
- Silver, D. (2005). Cooperative Pathfinding. *Proceedings of the AAAI Conference on Artificial Intelligence and Interactive Digital Entertainment*, 1(1), 117–122. https://doi.org/10.1609/aiide.v1i1.18726
- [Pygame documentation](https://www.pygame.org/docs/)

AI was used to explain pathfinding algorithms with step-by-step examples and compare their pros and cons, as well as create some of the test suites.