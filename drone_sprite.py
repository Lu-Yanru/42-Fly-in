"""
The DroneSprite class creates and animates the drones's
visual representations that moves along the network
based on scheduled paths.
"""


import pygame


class DroneSprite:
    """Visual representation of a drone."""
    def __init__(self, drone_id: int,
                 path: list[tuple[str, int]], radius: float) -> None:
        self.id = drone_id
        self.path = path
        self._segment = 0  # index into path for current start hub
        self.progress = 0.0  # 0.0 at start of segment, 1.0 at the end
        self._done = False

        self._size = int(radius * 0.75)

        # Color drone by looping through hues using golden angle spread
        hue = (drone_id * 137) % 360
        self._color = pygame.Color(0, 0, 0)
        self._color.hsva = (hue, 90, 95, 100)

    def draw(self, screen: pygame.Surface,
             hub_positions: dict[str, tuple[int, int]]) -> None:
        """
        Draw a drone as a triangle.
        Pointing right by default.
        Size is slighly smaller than hub radius.
        """
        if self._done:
            return

        x, y = self._current_pos(hub_positions)

        points = self._calculate_triangle_points(x, y, hub_positions)

        pygame.draw.polygon(screen, self._color, points)
        pygame.draw.polygon(screen, "black", points, 2)  # outline

    def update(self, speed: float) -> None:
        """
        Advance progress along the current segment.
        """
        if self._done:
            return
        self.progress += speed
        if self.progress >= 1.0:
            self.progress = 0.0
            self._segment += 1
            if self._segment >= len(self.path) - 1:
                self._done = True
                self._segment = len(self.path) - 1

    def _current_pos(self, hub_positions: dict[str, tuple[int, int]]) \
            -> tuple[float, float]:
        """
        Calculate the current position of the drone based on the lerp
        between current and next hub based on progress.
        """
        src = self.path[self._segment][0]

        # Last segment
        if self._done or self._segment >= len(self.path) - 1:
            x, y = hub_positions[src]
            return float(x), float(y)

        dest = self.path[self._segment + 1][0]
        src_x, src_y = hub_positions[src]
        dest_x, dest_y = hub_positions[dest]
        res_x = src_x + (dest_x - src_x) * self.progress
        res_y = src_y + (dest_y - src_y) * self.progress
        return res_x, res_y

    def _calculate_triangle_points(self, x: float, y: float,
                                   hub_positions: dict[str, tuple[int, int]]) \
            -> list[tuple[float, float]]:
        """
        Calculate the coordinates of each points of the drone triangle
        based on their current position and the direction
        it is facing. Default facing right.
        """
        src = self.path[self._segment][0]

        # Raw direction vector
        # Not the last segment
        if self._segment < len(self.path) - 1:
            dest = self.path[self._segment + 1][0]
            src_x, src_y = hub_positions[src]
            dest_x, dest_y = hub_positions[dest]
            dir_x, dir_y = dest_x - src_x, dest_y - src_y
        else:
            dir_x, dir_y = 1, 0  # Default facing right

        # Normalize to unit vector
        distance = (dir_x ** 2 + dir_y ** 2) ** 0.5
        if distance == 0:
            dx, dy = 1, 0
        else:
            dx, dy = dir_x / distance, dir_y / distance

        # Rotate triangle points by direction
        # Triangle points relative to center, pointing right:
        s = self._size
        raw_points = [
            (s, 0),  # nose: far right
            (-s // 2, -s // 2),  # left_wing: upper left
            (-s // 2, s // 2),  # right_wing: lower left
        ]
        rotated = [
            (x + px * dx - py * dy,
             y + px * dy + py * dx)
            for px, py in raw_points
        ]
        return rotated
