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
                 drone_speed: float = 0.02) -> None:
        self.map = map
        self.all_hubs = map.hubs + [map.start, map.end]
        self.simulator = simulator

        pygame.init()
        self._screen_w = 1280
        self._screen_h = 720
        self._padding = 100
        self.screen = pygame.display.set_mode((self._screen_w, self._screen_h))
        pygame.display.set_caption("Fly-in")

        self._default_color = "gray"
        self._drone_speed = drone_speed

        self._compute_layout()
        self._font = pygame.font.SysFont(None, max(12, self._radius))

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

        while running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # fill the screen with a color
            # to wipe away anything from last frame
            self.screen.fill("purple")

            self._draw_connections()
            self._draw_hubs()
            last_drone = None
            for drone in self._drones:
                drone.update(self._drone_speed)
                drone.draw(self.screen, self._hub_positions)
                last_drone = drone

            if last_drone is not None and last_drone.progress >= 1.0:
                pygame.time.wait(1000)

            # flip() the display to put your work on screen
            pygame.display.flip()

            clock.tick(60)

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
