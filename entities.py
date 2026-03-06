import pygame

class Entity(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, width: int, height: int, color: tuple):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.velocity = pygame.Vector2(0, 0)
        self.speed: float = 3.0
        self.max_hp = 6
        self.hp = 6

class Sword(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        # NES style sword - roughly 16x32 or 32x16
        if direction in ["up", "down"]:
            self.image = pygame.Surface((16, 32))
        else:
            self.image = pygame.Surface((32, 16))
        
        self.image.fill((200, 200, 255)) # Light blueish silver
        if "wooden" in str(self.__class__).lower(): # This might not work with how it's currently instantiated
              self.image.fill((139, 69, 19)) # Brown
        
        self.rect = self.image.get_rect()
        self.direction = direction
        self.timer = 10 # Frames the sword lasts
        self.set_position(x, y)

    def set_position(self, px, py):
        if self.direction == "up":
            self.rect.midbottom = (px + 16, py)
        elif self.direction == "down":
            self.rect.midtop = (px + 16, py + 32)
        elif self.direction == "left":
            self.rect.midright = (px, py + 16)
        elif self.direction == "right":
            self.rect.midleft = (px + 32, py + 16)

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.kill()

class Enemy(Entity):
    def __init__(self, x, y, color=(255, 50, 50)):
        super().__init__(x, y, 32, 32, color)
        self.speed = 1.5
        self.hp = 2

    def chase_player(self, player_rect, walls):
        # Very simple AI: Move towards player
        target = pygame.Vector2(player_rect.center)
        current = pygame.Vector2(self.rect.center)
        direction = target - current
        
        if direction.length() > 0:
            direction = direction.normalize()
            self.velocity = direction * self.speed
        else:
            self.velocity = pygame.Vector2(0, 0)

        # Apply movement with simple wall collision
        self.rect.x += self.velocity.x
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if self.velocity.x > 0: self.rect.right = wall.rect.left
                if self.velocity.x < 0: self.rect.left = wall.rect.right

        self.rect.y += self.velocity.y
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if self.velocity.y > 0: self.rect.bottom = wall.rect.top
                if self.velocity.y < 0: self.rect.top = wall.rect.bottom

    def update(self, player_rect, walls, projectile_group=None, all_group=None):
        self.chase_player(player_rect, walls)

class ShooterEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, color=(255, 128, 0)) # Orange
        self.shoot_timer = 0
        self.speed = 1.0 # 20% reduction from 1.2

    def update(self, player_rect, walls, projectile_group=None, all_group=None):
        target = pygame.Vector2(player_rect.center)
        current = pygame.Vector2(self.rect.center)
        direction = target - current
        dist = direction.length()
        
        if dist > 200:
            # Move towards player
            self.chase_player(player_rect, walls)
        elif dist < 180:
            # Retreat from player
            if dist > 0:
                dir_vec = direction.normalize()
                self.velocity = -dir_vec * self.speed
            else:
                self.velocity = pygame.Vector2(0, 0)
                
            # Apply movement with collision
            self.rect.x += self.velocity.x
            for wall in walls:
                if self.rect.colliderect(wall.rect):
                    if self.velocity.x > 0: self.rect.right = wall.rect.left
                    if self.velocity.x < 0: self.rect.left = wall.rect.right
            self.rect.y += self.velocity.y
            for wall in walls:
                if self.rect.colliderect(wall.rect):
                    if self.velocity.y > 0: self.rect.bottom = wall.rect.top
                    if self.velocity.y < 0: self.rect.top = wall.rect.bottom
        else:
            # Stop between 180 and 200 pixels
            self.velocity = pygame.Vector2(0, 0)

        if projectile_group is None or all_group is None: return
        self.shoot_timer += 1
        if self.shoot_timer > 90:
            self.shoot_timer = 0
            target = pygame.Vector2(player_rect.center)
            current = pygame.Vector2(self.rect.center)
            dir_vec = target - current
            if dir_vec.length() > 0:
                dir_vec = dir_vec.normalize()
                # Shooter enemy projectiles now do 0.5 damage
                p = Projectile(self.rect.centerx, self.rect.centery, dir_vec.x, dir_vec.y, (255, 150, 0), damage=0.5)
                projectile_group.add(p)
                all_group.add(p)

class WallWalkerEnemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((28, 28))
        self.image.fill((50, 200, 50)) # Green
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos = pygame.Vector2(x, y) # Smooth position
        self.speed = 4.0
        # 0: Right, 1: Down, 2: Left, 3: Up
        self.move_dir = 0

    def update(self, player_rect=None, walls=[]):
        # Wall Walker logic: Move in one direction until hitting a wall or losing "ground"
        # For simplicity in this dungeon, we'll make it hug the perimeter of the room
        prev_pos = pygame.Vector2(self.pos)
        
        if self.move_dir == 0: self.pos.x += self.speed
        elif self.move_dir == 1: self.pos.y += self.speed
        elif self.move_dir == 2: self.pos.x -= self.speed
        elif self.move_dir == 3: self.pos.y -= self.speed

        self.rect.topleft = (int(self.pos.x), int(self.pos.y))

        # Collision check
        hit_wall = False
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                hit_wall = True
                break
        
        # Out of bounds check
        margin = 40 # TILE_SIZE
        if self.rect.left < margin or self.rect.right > 640 - margin or \
           self.rect.top < margin or self.rect.bottom > 440 - margin or hit_wall:
            # Revert and change direction
            self.pos = prev_pos
            self.rect.topleft = (int(self.pos.x), int(self.pos.y))
            self.move_dir = (self.move_dir + 1) % 4

class MovingSpikes(pygame.sprite.Sprite):
    def __init__(self, x, y, axis="horizontal", direction=1, distance=400):
        super().__init__()
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        # Silver/Grey spikes
        pts = [(16, 0), (32, 16), (16, 32), (0, 16)]
        pygame.draw.polygon(self.image, (180, 180, 180), pts)
        pygame.draw.polygon(self.image, (100, 100, 100), pts, 2)
        
        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_pos = pygame.Vector2(x, y)
        self.axis = axis
        self.direction = direction # 1 or -1
        self.distance = distance
        self.speed = 10.0 # Fast strike
        self.return_speed = 1.5 # Slow return
        self.state = "idle" # idle, active, returning
        self.moved = 0.0 # Initialize as float

    def update(self, player_rect):
        if self.state == "idle":
            # Activate only if player is in line
            if self.axis == "horizontal":
                if abs(player_rect.centery - self.rect.centery) < 20:
                    self.state = "active"
            else: # vertical
                if abs(player_rect.centerx - self.rect.centerx) < 20:
                    self.state = "active"
                    
        elif self.state == "active":
            move_step = self.speed * self.direction
            if self.axis == "horizontal":
                self.rect.x += move_step
            else:
                self.rect.y += move_step
            self.moved += self.speed
            if self.moved >= self.distance:
                self.state = "returning"
                
        elif self.state == "returning":
            move_step = self.return_speed * self.direction
            if self.axis == "horizontal":
                self.rect.x -= move_step
            else:
                self.rect.y -= move_step
            self.moved -= self.return_speed
            if self.moved <= 0:
                self.state = "idle"
                self.moved = 0.0
                self.rect.topleft = self.start_pos

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy, color=(255, 255, 255), damage=1.0):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.velocity = pygame.Vector2(dx, dy) * 4
        self.damage = damage

    def update(self):
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y
        # Off-screen check?
        if self.rect.x < 0 or self.rect.x > 800 or self.rect.y < 0 or self.rect.y > 600:
            self.kill()

class Boss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, color=(200, 0, 200)) # Purple Boss
        self.image = pygame.Surface((64, 64))
        self.image.fill((200, 0, 200))
        self.rect = self.image.get_rect(center=(x, y))
        self.hp = 20
        self.max_hp = 20
        self.shoot_timer = 0

    def update_boss(self, player_rect, walls, projectile_group, all_group):
        self.chase_player(player_rect, walls)
        
        self.shoot_timer += 1
        if self.shoot_timer > 60:
            self.shoot_timer = 0
            # Shoot at player
            target = pygame.Vector2(player_rect.center)
            current = pygame.Vector2(self.rect.center)
            dir_vec = target - current
            if dir_vec.length() > 0:
                dir_vec = dir_vec.normalize()
                # Boss projectiles keep 1.0 damage
                p = Projectile(self.rect.centerx, self.rect.centery, dir_vec.x, dir_vec.y, (255, 100, 0), damage=1.0)
                projectile_group.add(p)
                all_group.add(p)

class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, item_type, color):
        super().__init__()
        self.item_type = item_type
        self.image = pygame.Surface((20, 20))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))

class Key(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "key", (255, 255, 0)) # Gold/Yellow

class MasterKey(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "master_key", (255, 100, 255)) # Purple

class SilverSword(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "silver_sword", (150, 150, 255))

class DefenseRing(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "defense_ring", (50, 255, 50))

class VictoryItem(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "victory_item", (0, 255, 255)) # Cyan Triangle/Diamond
        # Change shape to something special
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, (0, 255, 255), [(15, 0), (30, 15), (15, 30), (0, 15)])
        self.rect = self.image.get_rect(center=(x, y))

class WoodenSword(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "wooden_sword", (139, 69, 19)) # Brown

class Player(Entity):
    def __init__(self, x, y):
        # Initial color: Blue (Player)
        super().__init__(x, y, 32, 32, (0, 100, 255))
        self.hp = 6  # 3 hearts * 2 HP each
        self.max_hp = 6
        self.keys = 0
        self.has_wooden_sword = False
        self.has_silver_sword = False
        self.has_sword = False
        self.has_defense_ring = False
        self.has_master_key = False
        self.direction = "down"
        self.attack_cooldown = 0
        self.damage = 2
        self.defense = 0
        self.iframes = 0
        self.original_image = self.image.copy()

    def handle_input(self, sword_group):
        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        self.velocity.y = 0

        # Attack (Space bar)
        if keys[pygame.K_SPACE] and self.has_sword and self.attack_cooldown <= 0:
            new_sword = Sword(self.rect.x, self.rect.y, self.direction)
            sword_group.add(new_sword)
            self.attack_cooldown = 20 # Cooldown frames
        
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity.x = -self.speed
            self.direction = "left"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity.x = self.speed
            self.direction = "right"
        
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.velocity.y = -self.speed
            self.direction = "up"
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.velocity.y = self.speed
            self.direction = "down"
        
        # Simple diagonal normalization (can be added if needed, but for NES style 4/8-way is fine)
        if self.velocity.length() > 0:
            self.velocity = self.velocity.normalize() * self.speed

    def update(self, walls):
        # Handle X movement and collisions
        self.rect.x += self.velocity.x
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if self.velocity.x > 0: self.rect.right = wall.rect.left
                if self.velocity.x < 0: self.rect.left = wall.rect.right

        # Handle Y movement and collisions
        self.rect.y += self.velocity.y
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if self.velocity.y > 0: self.rect.bottom = wall.rect.top
                if self.velocity.y < 0: self.rect.top = wall.rect.bottom

        # Handle invincibility frames
        if self.iframes > 0:
            self.iframes -= 1
            # Flicker effect: toggle transparency every 5 frames
            if (self.iframes // 5) % 2 == 0:
                self.image.set_alpha(100)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)
