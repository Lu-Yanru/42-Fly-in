"""
The Visualizer class provides a graphical interface
which displays the network and drone positions
usign the pygame library.
"""


import pygame

from drone_sprite import DroneSprite
from map import Map
from simulator import Simulator


class Visualizer:
    def __init__(self, map: Map, simulator: Simulator,
                 drone_speed: float = 0.02,
                 turn_pause: int = 400) -> None:
        self.map = map
        self.all_hubs = map.hubs + [map.start, map.end]
        self.simulator = simulator

        # Track capacity
        self._reservations = simulator.reservations
        self._current_turn = 0

        # pygame setup
        pygame.init()
        self._screen_w = 1280
        self._screen_h = 720
        self._padding = 100
        self.screen = pygame.display.set_mode((self._screen_w, self._screen_h))
        pygame.display.set_caption("Fly-in")

        # Color, font and layout
        self._default_color = "gray"
        self._compute_layout()
        self._font = pygame.font.SysFont(None, max(12, self._radius))

        # Animation
        self._drone_speed = drone_speed  # how much progress per frame 0.0-1.0
        self._turn_pause = turn_pause  # how many ms pause per turn

        self._hub_positions: dict[str, tuple[int, int]] = {
            hub.name: (self._calc_x_pos(hub.x), self._calc_y_pos(hub.y))
            for hub in self.all_hubs
        }
        self._drones = [
            DroneSprite(i, path, self._radius)
            for i, path in enumerate(self.simulator.paths)
        ]

    def visualize(self) -> None:
        # pygame setup
        clock = pygame.time.Clock()
        running = True
        turn_timer = 0.0

        while running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Limits FPS to 60
            # Delta time in miliseconds since last frame
            dt = clock.tick(60)

            # Advance smooth animation every frame
            for drone in self._drones:
                drone.update(self._drone_speed)

            # Advance to next segment only after pause
            # and all active drones have finished their current segment
            all_arrived = all(
                d.done or d.progress >= 1.0 for d in self._drones
            )
            if all_arrived:
                turn_timer += dt
                if turn_timer >= self._turn_pause:
                    turn_timer = 0.0
                    self._current_turn += 1
                    for drone in self._drones:
                        drone.advance_segment()
            # Reset turn_timer if there are still drones moving in the segment
            else:
                turn_timer = 0.0

            # fill the screen with a color
            # to wipe away anything from last frame
            self.screen.fill("purple")

            self._draw_connections()
            self._draw_hubs()
            self._draw_drones()

            # flip() the display to put your work on screen
            pygame.display.flip()

        pygame.quit()

    # Drawing map
    # Draw hubs
    def _draw_hubs(self) -> None:
        """
        Draw all hubs as circles.
        """
        for hub in self.all_hubs:
            color = hub.color
            if color is None:
                color = self._default_color
            x = self._calc_x_pos(hub.x)
            y = self._calc_y_pos(hub.y)
            self._draw_hub_circle(x, y, color.lower())
            self._draw_hub_label(hub.name, x, y)

            # Capacity label below the hub
            current = self._reservations._hub_res.get((hub.name,
                                                       self._current_turn), 0)
            max_cap = hub.max_drones
            cap_text = f"{current}/{max_cap}"
            self._draw_capacity_hub_label(cap_text, x - self._radius - 5,
                                          y + self._radius + 5)

    def _draw_hub_circle(self, x: int, y: int, color: str) -> None:
        """
        Draw the hub circle itself.
        Draw a sightly larger black circle around the colored circle itself
        so the hubs don't blend in with the background when they have
        the same color.
        """
        outline = 2
        pygame.draw.circle(self.screen, "black", (x, y),
                           self._radius + outline)
        if color.lower() == "rainbow":
            self._draw_rainbow_circle(x, y)
        else:
            try:
                pygame.draw.circle(self.screen, color, (x, y),
                                   self._radius)
            except ValueError:
                pygame.draw.circle(self.screen, self._default_color,
                                   (x, y), self._radius)

    def _draw_rainbow_circle(self, x: int, y: int) -> None:
        """
        Draw a rainbow circle by drawing concentric rings
        from the outside in, each ring a slightly different hue.
        """
        hues = [0, 30, 60, 120, 180, 240, 270]
        ring_count = len(hues)
        for i, hue in enumerate(hues):
            r = self._radius - i * (self._radius // ring_count)
            if r <= 0:
                break
            color = pygame.Color(0, 0, 0)
            color.hsva = (hue, 100, 100, 100)
            pygame.draw.circle(self.screen, color, (x, y), r)

    def _draw_hub_label(self, name: str, x: int, y: int) -> None:
        """
        Draw the name of the hub at the center of the circle.
        """
        text = self._font.render(self._abbreviate_zone_name(name),
                                 True, "white")
        rect = text.get_rect(center=(x, y))
        self.screen.blit(text, rect)

    # Draw connections
    def _draw_connections(self) -> None:
        """
        Draw connections based on map information.
        """
        for conn in self.map.connections:
            src_hub = conn.src
            src_x = self._calc_x_pos(src_hub.x)
            src_y = self._calc_y_pos(src_hub.y)
            dest_hub = conn.dest
            dest_x = self._calc_x_pos(dest_hub.x)
            dest_y = self._calc_y_pos(dest_hub.y)
            pygame.draw.line(self.screen, "gray", (src_x, src_y),
                             (dest_x, dest_y), width=2)

            # Capacity label at midpoint
            mx, my = (src_x + dest_x) / 2, (src_y + dest_y) / 2
            # Connection key is orderd alphabetically
            a = min(conn.src.name, conn.dest.name)
            b = max(conn.src.name, conn.dest.name)
            current = self._reservations._conn_res.get((a, b,
                                                        self._current_turn), 0)
            cap_text = f"{current}/{conn.capacity}"
            self._draw_capacity_conn_label(cap_text, mx, my)

    # Draw drones
    def _draw_drones(self) -> None:
        """
        Draw drones based on their position in the path.
        Group drones by their current segment (src, dest).
        Apply offset if there are several drones in one group
        so they don't overlapp.
        """
        lane_spacing = self._radius * 0.35

        groups: dict[tuple[str, str], list[DroneSprite]] = {}
        for drone in self._drones:
            if drone.done:
                continue
            src = drone.path[drone.segment][0]
            if drone.segment < len(drone.path) - 1:
                dest = drone.path[drone.segment + 1][0]
            else:
                dest = src
            key = (src, dest)
            groups.setdefault(key, []).append(drone)

        # Assign offset within each group
        for group in groups.values():
            n = len(group)
            for i, drone in enumerate(group):
                drone.update(self._drone_speed)
                # Centre the spread:
                # e.g. n=1 → [0], n=2 → [-0.5, 0.5], n=3 → [-1, 0, 1]
                offset = (i - (n - 1) / 2) * lane_spacing
                drone.draw(self.screen, self._hub_positions, offset=offset)

    # Draw capacity label
    def _draw_capacity_hub_label(self, text: str, x: float, y: float) -> None:
        """
        Draw a label next to a hub or connection with
        "curently_in_use_capacity/max_capacity" info.
        """
        label = self._font.render(text, True, "black")
        # Make a dark rectangle background for readability
        padding = 1
        bg_rect = label.get_rect(center=(x, y)).inflate(padding * 2,
                                                        padding * 2)
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect)
        self.screen.blit(label, label.get_rect(center=(x, y)))

    def _draw_capacity_conn_label(self, text: str, x: float, y: float) -> None:
        """
        Draw a label next to a hub or connection with
        "curently_in_use_capacity/max_capacity" info.
        """
        label = self._font.render(text, True, "white")
        # Make a dark rectangle background for readability
        padding = 1
        bg_rect = label.get_rect(center=(x, y)).inflate(padding * 2,
                                                        padding * 2)
        pygame.draw.rect(self.screen, (30, 30, 30), bg_rect)
        self.screen.blit(label, label.get_rect(center=(x, y)))

    # Layout helpers
    def _compute_layout(self) -> None:
        """
        Compute scale, offset and radius so all hubs fit centered in the window
        with padding.
        """
        xs = [h.x for h in self.all_hubs]
        ys = [h.y for h in self.all_hubs]

        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)

        spanx = maxx - minx
        spany = maxy - miny

        # Calculate scale
        # Uniform for x and y, no streching
        if spanx > 0:
            scalex = (self._screen_w - 2 * self._padding) / spanx
        else:
            scalex = None
        if spany > 0:
            scaley = (self._screen_h - 2 * self._padding) / spany
        else:
            scaley = None
        if scalex is None and scaley is not None:
            self._scale = scaley
        elif scalex is not None and scaley is None:
            self._scale = scalex
        elif scalex is not None and scaley is not None:
            self._scale = min(scalex, scaley)
        else:
            self._scale = 1.0

        # Center the scaled content in the window with offsets
        if spanx > 0:
            scaledw = spanx * self._scale
            self._offset_x = ((self._screen_w - scaledw) / 2 -
                              minx * self._scale)
        else:
            self._offset_x = self._screen_w / 2 - minx * self._scale
        if spany > 0:
            scaledh = spany * self._scale
            self._offset_y = ((self._screen_h - scaledh) / 2 -
                              miny * self._scale)
        else:
            self._offset_y = self._screen_h / 2 - minx * self._scale

        # Radius proportional to scale
        self._radius = max(10, min(40, int(self._scale * 0.2)))

    def _calc_x_pos(self, x: int) -> int:
        """
        Caluclate to x position of the center of the hub circule.
        """
        return int(x * self._scale + self._offset_x)

    def _calc_y_pos(self, y: int) -> int:
        """
        Caluclate to y position of the center of the hub circule.
        """
        return int(y * self._scale + self._offset_y)

    @staticmethod
    def _abbreviate_zone_name(name: str) -> str:
        """
        Takes a zone name and returns an abbreviated version.
        waypoint -> w
        waypoint1 -> w1
        waiting_area -> wa
        waiting_area1 -> wa1
        """
        res = ""
        num = ""

        for ch in reversed(name):
            if not ch.isnumeric():
                break
            num += ch
        if len(num) > 0:
            num = num[::-1]

        splitted_name = name.split("_")
        if len(splitted_name) == 1:
            return name[0] + num
        else:
            for word in splitted_name:
                res += word[0]
            return res + num
