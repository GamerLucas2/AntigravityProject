import pygame
import random

TILE_SIZE = 40
ROOM_WIDTH_TILES = 16
ROOM_HEIGHT_TILES = 11
SCREEN_WIDTH = TILE_SIZE * ROOM_WIDTH_TILES
SCREEN_HEIGHT = TILE_SIZE * ROOM_HEIGHT_TILES

class Room:
    def __init__(self, room_type="common", grid_pos=(0, 0)):
        self.walls = pygame.sprite.Group()
        self.doors = {} # direction: door_rect
        self.type = room_type
        self.grid_pos = grid_pos
        self.connections = {"up": False, "down": False, "left": False, "right": False}
        self.locked_doors = {"up": False, "down": False, "left": False, "right": False}
        self.visited = False

    def setup_walls(self):
        self.walls.empty()
        # Create a border of walls with gaps for doors
        for x in range(ROOM_WIDTH_TILES):
            # Up wall
            if not (self.connections["up"] and x in [7, 8]):
                self.add_wall(x * TILE_SIZE, 0)
            # Down wall
            if not (self.connections["down"] and x in [7, 8]):
                self.add_wall(x * TILE_SIZE, (ROOM_HEIGHT_TILES - 1) * TILE_SIZE)

        for y in range(1, ROOM_HEIGHT_TILES - 1):
            # Left wall
            if not (self.connections["left"] and y in [5]):
                self.add_wall(0, y * TILE_SIZE)
            # Right wall
            if not (self.connections["right"] and y in [5]):
                self.add_wall((ROOM_WIDTH_TILES - 1) * TILE_SIZE, y * TILE_SIZE)

    def add_wall(self, x, y):
        wall = pygame.sprite.Sprite()
        wall.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        color = (80, 80, 100) # Default
        if self.type == "boss": color = (100, 20, 20)
        elif self.type == "treasure": color = (200, 160, 40)
        elif self.type == "puzzle": color = (60, 120, 60)
        elif self.type == "start": color = (50, 50, 80) # Darker blue for start
        
        wall.image.fill(color)
        wall.rect = wall.image.get_rect(topleft=(x, y))
        self.walls.add(wall)

    def draw(self, screen):
        self.walls.draw(screen)

class Dungeon:
    def __init__(self, size=5):
        self.size = size
        self.rooms = {} # (x, y): Room
        self.current_pos = (0, 0)
        self.generate()

    def generate(self):
        # 1. Initialize rooms in a grid
        for x in range(self.size):
            for y in range(self.size):
                self.rooms[(x, y)] = Room(grid_pos=(x, y))

        # 2. Simple Random Walk/Spanning Tree for connections
        # Just connecting all adjacent for now (DEBUG) or a simple chain
        curr = (0, 0)
        visited = set([curr])
        stack = [curr]
        
        while stack:
            cx, cy = stack[-1]
            neighbors = []
            for dx, dy, dir_name, opp_name in [(0, -1, "up", "down"), (0, 1, "down", "up"), 
                                              (-1, 0, "left", "right"), (1, 0, "right", "left")]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.size and 0 <= ny < self.size and (nx, ny) not in visited:
                    neighbors.append((nx, ny, dir_name, opp_name))
            
            if neighbors:
                nx, ny, d, o = random.choice(neighbors)
                self.rooms[(cx, cy)].connections[d] = True
                self.rooms[(nx, ny)].connections[o] = True
                visited.add((nx, ny))
                stack.append((nx, ny))
            else:
                stack.pop()

        # Assign special rooms
        rooms_list = list(self.rooms.values())
        random.shuffle(rooms_list)
        
        # Ensure Start room (0,0) is 'start' type
        self.rooms[(0, 0)].type = "start"

        special_count = 0
        for r in rooms_list:
            if r.grid_pos == (0, 0): continue # Skip start room
            if r.grid_pos == (self.size-1, self.size-1):
                r.type = "boss"
                # Lock doors to boss
                for d in r.connections:
                    if r.connections[d]: r.locked_doors[d] = "master"
                continue
            
            if special_count == 0:
                r.type = "treasure"
                special_count += 1
            elif special_count == 1:
                r.type = "puzzle"
                special_count += 1
            elif special_count == 2:
                r.type = "master_key_room" # New type for master key
                r.setup_walls()
                special_count += 1

        # Re-setup walls for all (to apply colors)
        for room in self.rooms.values():
            room.setup_walls()

    def get_current_room(self):
        return self.rooms[self.current_pos]

    def move(self, direction):
        x, y = self.current_pos
        if direction == "up": y -= 1
        elif direction == "down": y += 1
        elif direction == "left": x -= 1
        elif direction == "right": x += 1
        
        if (x, y) in self.rooms:
            self.current_pos = (x, y)
            return True
        return False
