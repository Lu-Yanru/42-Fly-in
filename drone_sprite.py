"""
The DroneSprite class creates and animates the drones's
visual representations that moves along the network
based on scheduled paths.
"""


from dataclasses import dataclass
import pygame


@dataclass
class AnimationStep:
    src: str
    dest: str
    turn: int
    is_first_transit: bool = False
    is_second_transit: bool = False


class DroneSprite:
    """Visual representation of a drone."""
    def __init__(self, drone_id: int,
                 path: list[tuple[str, int]], radius: float) -> None:
        self.id = drone_id
        self.path = path
        self.segment = 0  # index for animation steps
        self.progress = 0.0  # 0.0 at start of step, 1.0 at the end
        self.done = False
        self.just_arrived = False

        self._size = int(radius * 0.75)

        # Color drone by looping through hues using golden angle spread
        hue = (drone_id * 137) % 360
        self._color = pygame.Color(0, 0, 0)
        self._color.hsva = (hue, 90, 95, 100)

        # Animation
        self._steps = self._build_animation_steps()

    def draw(self, screen: pygame.Surface,
             hub_positions: dict[str, tuple[int, int]],
             offset: float = 0.0) -> None:
        """
        Draw a drone as a triangle.
        Pointing right by default.
        Size is slighly smaller than hub radius.
        """
        if self.done:
            return

        x, y = self._current_pos(hub_positions)

        points = self._calculate_triangle_points(x, y, hub_positions, offset)

        pygame.draw.polygon(screen, self._color, points)
        pygame.draw.polygon(screen, "black", points, 2)  # outline

    def update(self, speed: float) -> None:
        """
        Advance progress along the current segment.
        """
        if self.done or self.progress >= 1.0:
            return
        prev_progress = self.progress
        self.progress = min(1.0, self.progress + speed)
        # Signal first arrival when progress in last frame <1.0
        # and current progress >= 1.0
        self.just_arrived = prev_progress < 1.0 and self.progress >= 1.0

    def advance_segment(self) -> None:
        """
        Advance once per turn to introduce a pause
        between turns in the animation.
        Returns True if the drone just completed the path
        this call.
        """
        if self.done or self.progress < 1.0:
            return
        self.progress = 0.0
        self.segment += 1
        if self.segment >= len(self._steps):
            self.done = True
            self.segment = len(self._steps) - 1

    # Create animation steps
    def _build_animation_steps(self) -> list[AnimationStep]:
        """
        Create per turn steps to animate.
        """
        steps: list[AnimationStep] = []

        i = 0
        while i < len(self.path) - 1:
            src, turn_src = self.path[i]
            dest, turn_dest = self.path[i + 1]
            delta = turn_dest - turn_src
            # Restricted move, split into 2 steps
            if delta == 2:
                mid_turn = turn_src + 1
                steps.append(AnimationStep(src, dest, mid_turn, True, False))
                steps.append(AnimationStep(src, dest, turn_dest, False, True))
            else:
                steps.append(AnimationStep(src, dest, turn_dest, False))
            i += 1

        return steps

    def _current_pos(self, hub_positions: dict[str, tuple[int, int]]) \
            -> tuple[float, float]:
        """
        Calculate the current position of the drone based on the lerp
        between current and next hub based on progress.
        """
        step = self._steps[self.segment]

        src_x, src_y = hub_positions[step.src]
        dest_x, dest_y = hub_positions[step.dest]
        mid_x, mid_y = (src_x + dest_x) / 2, (src_y + dest_y) / 2

        # Start dron src_hub to mid_connection
        if step.is_first_transit:
            start_x, start_y = float(src_x), float(src_y)
            target_x, target_y = mid_x, mid_y
        # Start from mid-connection to dest_hub
        elif step.is_second_transit:
            start_x, start_y = mid_x, mid_y
            target_x, target_y = float(dest_x), float(dest_y)
        # Start from src_hub to dest_hub
        else:
            start_x, start_y = float(src_x), float(src_y)
            target_x, target_y = float(dest_x), float(dest_y)

        res_x = start_x + (target_x - start_x) * self.progress
        res_y = start_y + (target_y - start_y) * self.progress
        return res_x, res_y

    def _calculate_triangle_points(self, x: float, y: float,
                                   hub_positions: dict[str, tuple[int, int]],
                                   offset: float = 0.0) \
            -> list[tuple[float, float]]:
        """
        Calculate the coordinates of each points of the drone triangle
        based on their current position and the direction
        it is facing. Default facing right.
        """
        step = self._steps[self.segment]

        src_x, src_y = hub_positions[step.src]
        dest_x, dest_y = hub_positions[step.dest]
        dir_x, dir_y = dest_x - src_x, dest_y - src_y

        # Normalize to unit vector
        distance = (dir_x ** 2 + dir_y ** 2) ** 0.5
        if distance == 0:
            dx, dy = 1, 0
        else:
            dx, dy = dir_x / distance, dir_y / distance

        # Apply offset when multiple drones are together
        x += -dy * offset
        y += dx * offset

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
