"""
The Visualizer class provides a graphical interface
which displays the network and drone positions
usign the pygame library.
"""


import pygame

from map import Map
from simulator import Simulator


class Visualizer:
    def __init__(self, map: Map, simulator: Simulator) -> None:
        self.map = map
        self.simulator = Simulator
        SCREEN_W = 1280
        SCREEN_H = 720
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

    def visualize(self) -> None:
        # pygame setup
        pygame.init()
        pygame.display.set_caption("Fly-in")
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

            self._draw_hubs()

            # flip() the display to put your work on screen
            pygame.display.flip()

            clock.tick(60)

        pygame.quit()

    def _draw_hubs(self) -> None:
        all_hubs = self.map.hubs + [self.map.start, self.map.end]
        for hub in all_hubs:
            color = hub.color
            if color is None:
                color = "gray"
            pygame.draw.circle(self.screen, color, (hub.x * 40, hub.y * 40), 40)

    def _calc_x_pos(self, x: int) -> int:
        """
        Caluclate to x position of the center of the hub circule.
        """
        return x
