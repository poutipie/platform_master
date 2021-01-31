import pygame
import itertools
import abc
from typing import List, Tuple, Optional
from enum import Enum

Bounds = Tuple[Tuple[int, int], Tuple[int, int]]

class AABBCollision:
    """
        Functions for AABB (Axis Aligned Bounding Box) Collision Detection
    """

    def AABB_vector_compact(bounds1: Bounds, bounds2: Bounds)  -> Tuple[int, int]:

        x: float = 0.0
        y: float = 0.0

        if (bounds1[0][0] <= bounds2[0][1] and bounds2[0][0] <= bounds1[0][1]) and (bounds1[1][0] <= bounds2[1][1] and bounds2[1][0] <= bounds1[1][1]):
            x = bounds2[0][0] - bounds1[0][1] if abs(bounds1[0][1] - bounds2[0][0]) < abs(bounds2[0][1] - bounds1[0][0]) else bounds2[0][1] - bounds1[0][0]
            y = bounds2[1][0] - bounds1[1][1] if abs(bounds1[1][1] - bounds2[1][0]) < abs(bounds2[1][1] - bounds1[1][0]) else bounds2[1][1] - bounds1[1][0] 
        else:
            return 0, 0
        
        # Select shortest path if colliding on both axes
        if abs(x) < abs(y):
            y = 0
        else: 
            x = 0
        
        return x, y

    def AABB_vector(bounds1: Bounds, bounds2: Bounds) -> Tuple[int, int]:
        """
            Return a vector that moves the object defined by bounds1 away from object defined by bounds2.
            Returns (0, 0) if no collision is occurring
        """
        res = [0.0, 0.0]

        if AABBCollision.AABB_is_colliding(bounds1, bounds2):
            res = [
                AABBCollision._AABB_vector_1d(bounds1[0], bounds2[0]),
                AABBCollision._AABB_vector_1d(bounds1[1], bounds2[1])
            ]
        
        # Select shortest path if colliding on both axes
        if abs(res[0]) < abs(res[1]):
            res[1] = 0
        else: 
            res[0] = 0
        
        return tuple(res)

    def AABB_is_colliding(bounds1: Bounds, bounds2: Bounds):
        return AABBCollision._AABB_is_colliding_1d(bounds1[0], bounds2[0]) and AABBCollision._AABB_is_colliding_1d(bounds1[1], bounds2[1]) 
    
    def _AABB_vector_1d(x1: tuple, x2: tuple):
        return x2[0] - x1[1] if abs(x1[1] - x2[0]) < abs(x2[1] - x1[0]) else x2[1] - x1[0]

    def _AABB_is_colliding_1d(x1: tuple, x2: tuple):
        return x1[0] <= x2[1] and x2[0] <= x1[1]

class PhysicsObject:

    class Tag(Enum):
        STATIC = 0
        DYNAMIC = 1
        PLAYER = 2

    newid = itertools.count()

    def __init__(self, x, y, width, height, tags: Optional[List[Tag]] = None):

        self.id = next(PhysicsObject.newid)

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.tags: List[Tag] = [] if tags == None else tags


    @abc.abstractmethod
    def update(self):
        pass

    @abc.abstractmethod
    def draw(self):
        pass

    def bounds(self) -> Bounds:
        return ((self.x, self.x + self.width), (self.y, self.y + self.height))
    
    def move(self, x: float, y: float):
        self.x += x
        self.y += y

class PhysicsEngine:

    def __init__(self):
            self.objects: List[PhysicsObject] = []

    def register_obj(self, obj: PhysicsObject):
        self.objects.append(obj)

    def update(self):
        for obj in self.objects:
            obj.update()

        # Check for collision physics
        self._collision_update()

    def _collision_update(self):

        for dyn_obj in [obj for obj in self.objects if PhysicsObject.Tag.DYNAMIC in obj.tags]:

            for obj in self.objects:
                if obj.id == dyn_obj.id:
                    continue

                offset = AABBCollision.AABB_vector_compact(dyn_obj.bounds(), obj.bounds())
                dyn_obj.move(*offset)

    def draw(self, display: pygame.display):
        for obj in self.objects:
            obj.draw(display)


class Platform(PhysicsObject):

    def __init__(self, x: int, y: int, width: int, height: int):

        PhysicsObject.__init__(self, x, y, width, height, tags=[PhysicsObject.Tag.STATIC])

    def update(self):
        pass

    def draw(self, display: pygame.display):
        pygame.draw.rect(display, (255, 0, 0), (self.x, self.y, self.width, self.height))


class Player(PhysicsObject):

    def __init__(self, x: int, y: int, width: int, height: int):

        PhysicsObject.__init__(self, x, y, width, height, tags=[PhysicsObject.Tag.DYNAMIC, PhysicsObject.Tag.PLAYER])

        self.velocity = [0.0, 0.0]

    def update(self):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_SPACE] and self.velocity[1] < 0.1:
            if self.velocity[1] < 0: self.velocity[1] = 0
            self.velocity[1] += 30.0
        if keys[pygame.K_LEFT] and self.velocity[0] > -10:
            self.velocity[0] = self.velocity[0] - 3
        if keys[pygame.K_RIGHT] and self.velocity[0] < 10:
            self.velocity[0] = self.velocity[0] + 3

        # Dummy gravity
        t = 1
        if self.velocity[1] > -15:
            self.velocity[1] -= 3 * t
            t += 1
        else:
            t = 1

        self.x += self.velocity[0]
        self.y -= self.velocity[1]


    def draw(self, display: pygame.display):
        pygame.draw.rect(display, (255, 0, 0), (self.x, self.y, self.width, self.height))

if __name__ == "__main__":

    pygame.init()
    display: pygame.display = pygame.display.set_mode((500, 500))
    pygame.display.set_caption("Platform Master")

    physics = PhysicsEngine()
    physics.register_obj(Player(50, 380, 40, 60))

    # Edges
    physics.register_obj(Platform(5, 490, 490, 5))
    physics.register_obj(Platform(5, 5, 490, 5))
    physics.register_obj(Platform(5, 10, 5, 480))
    physics.register_obj(Platform(490, 10, 5, 480))

    # Middle Platform
    physics.register_obj(Platform(180, 225, 140, 50))

    run = True
    delta_time = 50
    while run:

        pygame.time.delay(40)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        physics.update()

        display.fill((0, 0, 0))
        physics.draw(display)
        pygame.display.update()


    pygame.quit()