import pygame
import random
from typing import Dict, Union, Tuple, List, Set

TILE_SIZE = 40
ROOM_WIDTH_TILES = 16
ROOM_HEIGHT_TILES = 11
SCREEN_WIDTH = TILE_SIZE * ROOM_WIDTH_TILES
SCREEN_HEIGHT = TILE_SIZE * ROOM_HEIGHT_TILES

class Room:
    def __init__(self, room_type: str = "common", grid_pos: Tuple[int, int] = (0, 0)):
        self.walls = pygame.sprite.Group()
        self.doors = {} # direction: door_rect
        self.type = room_type
        self.grid_pos = grid_pos
        self.connections: Dict[str, bool] = {"up": False, "down": False, "left": False, "right": False}
        # locked_doors can be False, "key", or "master"
        self.locked_doors: Dict[str, Union[bool, str]] = {"up": False, "down": False, "left": False, "right": False}
        self.visited = False
        self.enemies_cleared = False
        self.arena_activated = False
        self.hazards = [] # Store hazard definitions [(type, x, y, extra_data)]
        # Special rooms should ALWAYS be empty
        special_types = ["start", "boss", "treasure", "puzzle", "master_key_room", "victory"]
        if self.type in special_types:
            self.layout_type = "special"
        else:
            self.layout_type = random.choice(["empty", "pillars", "bars", "grid", "square", "L_shapes", "plus", "single_bar"])

    def setup_walls(self):
        self.walls.empty()
        
        # Ensure special rooms ALWAYS stay 'special' even if type changed after init
        special_types = ["start", "boss", "treasure", "puzzle", "master_key_room", "victory"]
        if self.type in special_types:
            self.layout_type = "special"

        # Create a border of walls with gaps for doors
        for x in range(ROOM_WIDTH_TILES):
            # Up wall
            if self.connections["up"] and x in [7, 8]:
                if self.locked_doors["up"]:
                    self.add_wall(x * TILE_SIZE, 0, is_door=True, lock=self.locked_doors["up"])
            else:
                self.add_wall(x * TILE_SIZE, 0)

            # Down wall
            if self.connections["down"] and x in [7, 8]:
                if self.locked_doors["down"]:
                    self.add_wall(x * TILE_SIZE, (ROOM_HEIGHT_TILES - 1) * TILE_SIZE, is_door=True, lock=self.locked_doors["down"])
            else:
                self.add_wall(x * TILE_SIZE, (ROOM_HEIGHT_TILES - 1) * TILE_SIZE)

        for y in range(1, ROOM_HEIGHT_TILES - 1):
            # Left wall
            if self.connections["left"] and y in [5]:
                if self.locked_doors["left"]:
                    self.add_wall(0, y * TILE_SIZE, is_door=True, lock=self.locked_doors["left"])
            else:
                self.add_wall(0, y * TILE_SIZE)

            # Right wall
            if self.connections["right"] and y in [5]:
                if self.locked_doors["right"]:
                    self.add_wall((ROOM_WIDTH_TILES - 1) * TILE_SIZE, y * TILE_SIZE, is_door=True, lock=self.locked_doors["right"])
            else:
                self.add_wall((ROOM_WIDTH_TILES - 1) * TILE_SIZE, y * TILE_SIZE)
        
        # Internal Layouts applied to all rooms according to their layout_type
        # (Special rooms are now set to 'pillars' instead of returning early)

        if self.layout_type == "pillars":
            # Image 3: 4 Pillars
            for px, py in [(4, 3), (11, 3), (4, 7), (11, 7)]:
                self.add_wall(px * TILE_SIZE, py * TILE_SIZE)
        elif self.layout_type == "bars":
            # Image 1: Two horizontal bars
            for x in range(9, 13): # Top-right bar
                self.add_wall(x * TILE_SIZE, 3 * TILE_SIZE)
            for x in range(3, 7): # Bottom-left bar
                self.add_wall(x * TILE_SIZE, 7 * TILE_SIZE)
        elif self.layout_type == "grid":
            # Image 7: 4x3 Grid (Two pairs of columns, adjusted)
            for px in [3, 6, 9, 12]:
                for py in [2, 5, 8]:
                    self.add_wall(px * TILE_SIZE, py * TILE_SIZE)
        elif self.layout_type == "square":
            # Image 4: Large center square
            for x in range(6, 10):
                for y in range(4, 7):
                    self.add_wall(x * TILE_SIZE, y * TILE_SIZE)
        elif self.layout_type == "L_shapes":
            # Image 5: L-shapes in corners
            # Top-left
            self.add_wall(2 * TILE_SIZE, 2 * TILE_SIZE)
            self.add_wall(3 * TILE_SIZE, 2 * TILE_SIZE)
            self.add_wall(2 * TILE_SIZE, 3 * TILE_SIZE)
            # Top-right
            self.add_wall(13 * TILE_SIZE, 2 * TILE_SIZE)
            self.add_wall(12 * TILE_SIZE, 2 * TILE_SIZE)
            self.add_wall(13 * TILE_SIZE, 3 * TILE_SIZE)
            # Bottom-left
            self.add_wall(2 * TILE_SIZE, 8 * TILE_SIZE)
            self.add_wall(3 * TILE_SIZE, 8 * TILE_SIZE)
            self.add_wall(2 * TILE_SIZE, 7 * TILE_SIZE)
            # Bottom-right
            self.add_wall(13 * TILE_SIZE, 8 * TILE_SIZE)
            self.add_wall(12 * TILE_SIZE, 8 * TILE_SIZE)
            self.add_wall(13 * TILE_SIZE, 7 * TILE_SIZE)
        elif self.layout_type == "plus":
            # Image 6: Plus sign in center
            for x in range(5, 11): # Horizontal bar
                self.add_wall(x * TILE_SIZE, 5 * TILE_SIZE)
            for y in [3, 4, 6, 7]: # Vertical bars (skipping center row)
                self.add_wall(7 * TILE_SIZE, y * TILE_SIZE)
                self.add_wall(8 * TILE_SIZE, y * TILE_SIZE)
        elif self.layout_type == "special":
            # Corner pillars with space to walk behind (1 tile gap from walls)
            # Puzzle rooms handle these as interactive objects in main.py
            if self.type != "puzzle":
                for px, py in [(2, 2), (13, 2), (2, 8), (13, 8)]:
                    self.add_wall(px * TILE_SIZE, py * TILE_SIZE)
        elif self.layout_type == "single_bar":
            # Image 8: Single horizontal bar in center
            for x in range(5, 11):
                self.add_wall(x * TILE_SIZE, 5 * TILE_SIZE)

    def add_wall(self, x, y, is_door=False, lock=False):
        wall = pygame.sprite.Sprite()
        wall.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        
        if is_door:
            if lock == "key":
                color = (255, 255, 0) # Yellow Door
            elif lock == "master":
                color = (255, 100, 255) # Purple Door
            elif lock == "enemy":
                color = (255, 0, 0) # Red Door (Enemies)
            else:
                color = (40, 40, 40) # Should not happen if lock is False
        else:
            color = (80, 80, 100) # Default
            if self.type == "boss": color = (100, 20, 20)
            elif self.type == "treasure": color = (200, 160, 40)
            elif self.type == "puzzle": color = (60, 120, 60)
            elif self.type == "start": color = (50, 50, 80)
            elif self.type == "victory": color = (0, 100, 100) # Deep cyan for throne room
            elif self.type == "master_key_room": color = (200, 0, 200) # Purple for Master Key room
        
        wall.image.fill(color)
        if is_door:
            # Draw a small "lock" icon or detail on the door
            inner_rect = pygame.Rect(10, 10, TILE_SIZE-20, TILE_SIZE-20)
            pygame.draw.rect(wall.image, (0, 0, 0), inner_rect)
            
        wall.rect = wall.image.get_rect(topleft=(x, y))
        self.walls.add(wall)

    def draw(self, screen):
        self.walls.draw(screen)

class Dungeon:
    def __init__(self, size: int = 5):
        self.size = size
        self.rooms: Dict[Tuple[int, int], Room] = {} # (x, y): Room
        self.current_pos: Tuple[int, int] = (0, 0)
        self.generate()

    def generate(self):
        # 1. Initialize rooms
        for x in range(self.size):
            for y in range(self.size):
                self.rooms[(x, y)] = Room(grid_pos=(x, y))

        # 2. Create Spanning Tree (Randomized DFS)
        # This guarantees everyone is reachable and there are no cycles initially
        curr = (0, 0)
        visited = set([curr])
        stack = [curr]
        tree_edges = set() # ( (x1,y1), (x2,y2) )

        while stack:
            cx, cy = stack[-1]
            neighbors = []
            for dx, dy, d_name, o_name in [(0, -1, "up", "down"), (0, 1, "down", "up"), 
                                              (-1, 0, "left", "right"), (1, 0, "right", "left")]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.size and 0 <= ny < self.size and (nx, ny) not in visited:
                    neighbors.append((nx, ny, d_name, o_name))
            
            if neighbors:
                nx, ny, d, o = random.choice(neighbors)
                self.rooms[(cx, cy)].connections[d] = True
                self.rooms[(nx, ny)].connections[o] = True
                tree_edges.add(tuple(sorted([(cx, cy), (nx, ny)])))
                visited.add((nx, ny))
                stack.append((nx, ny))
            else:
                stack.pop()

        # 3. Calculate Depths and Parents (BFS)
        depths: Dict[Tuple[int, int], int] = {(0, 0): 0}
        parents: Dict[Tuple[int, int], Union[Tuple[int, int], None]] = {(0, 0): None}
        bfs_queue: List[Tuple[int, int]] = [(0, 0)]
        bfs_order: List[Tuple[int, int]] = [(0, 0)]
        visited_bfs = set([(0, 0)])

        while bfs_queue:
            cx, cy = bfs_queue.pop(0)
            room = self.rooms[(cx, cy)]
            for d, is_conn in room.connections.items():
                if is_conn:
                    nx, ny = cx, cy
                    if d == "up": ny -= 1
                    elif d == "down": ny += 1
                    elif d == "left": nx -= 1
                    elif d == "right": nx += 1
                    
                    if (nx, ny) not in visited_bfs:
                        visited_bfs.add((nx, ny))
                        depths[(nx, ny)] = depths[(cx, cy)] + 1
                        parents[(nx, ny)] = (cx, cy)
                        bfs_queue.append((nx, ny))
                        bfs_order.append((nx, ny))

        # 4. Strategy: Furthest Room is Victory, its parent is Boss
        # Find deepest room
        victory_pos = (0, 0)
        max_d = -1
        for pos, d in depths.items():
            if d > max_d:
                max_d = d
                victory_pos = pos
        
        boss_pos = parents[victory_pos]
        if boss_pos is None: # Should only happen if dungeon size is 1
            boss_pos = (0, 0) # Fallback

        # Apply basic types
        self.rooms[(0, 0)].type = "start"
        self.rooms[victory_pos].type = "victory"
        self.rooms[boss_pos].type = "boss"

        # ISOLATION: Boss and Victory should only have connections within the sequence
        # We must be careful not to isolate other rooms if Boss was a passage in the tree
        # To fix this, we'll re-route any "children" of Boss to Boss's parent or or neighbors
        # Easier/Safer: Since we want a perfect sequence, we just make Boss/Victory a DEAD END sequence
        # We'll find a TRUE leaf for Victory if we can
        
        # 5. Connect Sequence: Parent -> Boss -> Victory
        # Boss Exit to Victory
        exit_dir = ""
        vx, vy = victory_pos
        bx, by = boss_pos
        if vx > bx: exit_dir = "right"
        elif vx < bx: exit_dir = "left"
        elif vy > by: exit_dir = "down"
        elif vy < by: exit_dir = "up"
        
        opp_exit = {"up":"down", "down":"up", "left":"right", "right":"left"}[exit_dir]
        self.rooms[boss_pos].locked_doors[exit_dir] = "enemy"
        self.rooms[victory_pos].locked_doors[opp_exit] = "enemy"
        
        # Boss Entrance (Parent to Boss)
        ent_dir = ""
        boss_parent = parents[boss_pos]
        if boss_parent is not None:
            px, py = boss_parent
            if bx > px: ent_dir = "right"
            elif bx < px: ent_dir = "left"
            elif by > py: ent_dir = "down"
            elif by < py: ent_dir = "up"
            
            if ent_dir:
                opp_ent = {"up":"down", "down":"up", "left":"right", "right":"left"}[ent_dir]
                self.rooms[boss_parent].locked_doors[ent_dir] = "master"
                self.rooms[boss_pos].locked_doors[opp_ent] = "master"

        # 6. Place other special rooms on non-boss branches
        puzzle_pos = bfs_order[min(2, len(bfs_order)-1)]
        potential_puzzle = [p for p in bfs_order if depths[p] >= 1 and depths[p] <= 3 and self.rooms[p].type == "common"]
        if potential_puzzle:
            puzzle_pos = random.choice(potential_puzzle)
        
        self.rooms[puzzle_pos].type = "puzzle"
        
        # 8. Path Protection (Critical Path to Puzzle must not be locked)
        critical_path = set()
        ptr = puzzle_pos
        while ptr is not None:
            critical_path.add(ptr)
            ptr = parents.get(ptr)

        # 9. Ensure the Puzzle room itself and its entrance are NOT locked by a key
        puzzle_parent = parents.get(puzzle_pos)
        if puzzle_parent is not None:
            px, py = puzzle_parent
            pux, puy = puzzle_pos
            p_dir = ""
            if pux > px: p_dir = "right"
            elif pux < px: p_dir = "left"
            elif puy > py: p_dir = "down"
            elif puy < py: p_dir = "up"
            
            if p_dir:
                opp_p = {"up":"down", "down":"up", "left":"right", "right":"left"}[p_dir]
                self.rooms[puzzle_parent].locked_doors[p_dir] = False
                self.rooms[puzzle_pos].locked_doors[opp_p] = False

        # 10. Re-add Master Key and Treasure Rooms placement with LOCKS
        # Master Key at a deeper spot that is NOT Victory, Boss, or Start
        potential_mk = [p for p in bfs_order if self.rooms[p].type == "common" and p != (0,0)]
        if potential_mk:
            start_idx = len(potential_mk) // 2
            mk_pos = random.choice(potential_mk[start_idx:])
        else:
            mk_pos = bfs_order[-1]
        self.rooms[mk_pos].type = "master_key_room"
        
        # Lock Master Key room with COMMON KEY
        mk_parent = parents.get(mk_pos)
        if mk_parent is not None and mk_pos not in critical_path:
            px, py = mk_parent
            mx, my = mk_pos
            m_dir = ""
            if mx > px: m_dir = "right"
            elif mx < px: m_dir = "left"
            elif my > py: m_dir = "down"
            elif my < py: m_dir = "up"
            if m_dir:
                opp_m = {"up":"down", "down":"up", "left":"right", "right":"left"}[m_dir]
                self.rooms[mk_parent].locked_doors[m_dir] = "key"
                self.rooms[mk_pos].locked_doors[opp_m] = "key"

        # Treasure Rooms (Unlocked to preserve the 1:1 Key/Door ratio)
        treasures_placed = 0
        common_nodes = [p for p in bfs_order if self.rooms[p].type == "common" and p != mk_pos]
        random.shuffle(common_nodes)
        for p in common_nodes:
            if treasures_placed < 2:
                self.rooms[p].type = "treasure"
                treasures_placed += 1

        # 10. Final check: Ensure NO isolation was caused by Boss sequence
        # (Since we didn't break connections, just applied locks, we are good)
        for room in self.rooms.values():
            room.setup_walls()

    def get_current_room(self) -> Room:
        return self.rooms[self.current_pos]

    def move(self, direction):
        # Check if there is even a door/connection in that direction first!
        if not self.rooms[self.current_pos].connections.get(direction):
            return False
            
        lx, ly = self.current_pos
        if direction == "up": ly -= 1
        elif direction == "down": ly += 1
        elif direction == "left": lx -= 1
        elif direction == "right": lx += 1
        
        if (lx, ly) in self.rooms:
            self.current_pos = (lx, ly)
            return True
        return False
