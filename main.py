import pygame
import sys
import asyncio
import os
import random

# Ensure the current directory is in the Python search path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from entities import Player, Enemy, Sword, Key, MasterKey, SilverSword, DefenseRing, Boss, Projectile, VictoryItem, ShooterEnemy, WallWalkerEnemy, MovingSpikes, WoodenSword
from map_gen import Dungeon, SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE

async def main():
    # Pygame initialization
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dungeon Crawler (NP) - Web Optimized")
    clock = pygame.time.Clock()

    # Game Objects
    # Spawning player at the top center of the room
    player = Player(SCREEN_WIDTH // 2, TILE_SIZE * 2)
    dungeon = Dungeon(size=3) 
    
    # Sprite groups
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)
    
    swords = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    items = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    hazards = pygame.sprite.Group()
    
    # Game State
    STATE_PLAYING = 0
    STATE_GAMEOVER = 1
    STATE_WIN = 2
    STATE_TITLE = 3
    game_state = STATE_TITLE

    # Cache fonts for performance
    font_hud = pygame.font.SysFont("Arial", 20)
    font_boss = pygame.font.SysFont("Arial", 16)
    font_small = pygame.font.SysFont("Arial", 16, bold=True)
    font_overlay = pygame.font.SysFont("Arial", 40, bold=True)
    font_sub_overlay = pygame.font.SysFont("Arial", 20)

    def setup_room(room, groups, all_group):
        enemies, items, projectiles, hazards = groups
        enemies.empty()
        items.empty()
        projectiles.empty()
        hazards.empty()
        
        # Remove old entities (enemies, items, projectiles, etc.)
        for s in list(all_group):
            if s != player:
                s.kill()
        
        room.arena_activated = False
        
        # Ensure room state attributes exist
        if not hasattr(room, 'items_collected'): room.items_collected = False
        if not hasattr(room, 'enemies_cleared'): room.enemies_cleared = False

        def spawn_minions():
            for _ in range(random.randint(2, 4)):
                etype = random.random()
                ex = random.randint(TILE_SIZE * 2, SCREEN_WIDTH - TILE_SIZE * 3)
                ey = random.randint(TILE_SIZE * 2, SCREEN_HEIGHT - TILE_SIZE * 3)
                
                if etype < 0.7: e = Enemy(ex, ey)
                else: e = ShooterEnemy(ex, ey)
                
                enemies.add(e)
                all_group.add(e)

        def setup_hazards():
            # Use persisted hazards if they exist
            if room.hazards:
                for h_type, hx, hy, extra in room.hazards:
                    if h_type == "spikes":
                        s = MovingSpikes(hx, hy, axis=extra["axis"], direction=extra["direction"], distance=extra["distance"])
                        all_group.add(s)
                        hazards.add(s)
                    elif h_type == "wall_walker":
                        w = WallWalkerEnemy(hx, hy)
                        all_group.add(w)
                        hazards.add(w)
                return

            # Hazard Spawn (Only in hazard-eligible rooms, e.g., common or puzzle)
            if room.type in ["common", "puzzle", "treasure"] and random.random() < 0.5:
                hazard_choice = random.choice(["spikes", "wall_walker"])
                
                if hazard_choice == "spikes":
                    # Filter only walls that HAVE a door (connection)
                    dir_map = {"top": "up", "bottom": "down", "left": "left", "right": "right"}
                    valid_sides = [side for side in ["top", "bottom", "left", "right"] if room.connections.get(dir_map[side])]
                    
                    if not valid_sides: return # No doors, no ambush spikes
                    
                    wall_side = random.choice(valid_sides)
                    if wall_side == "top":
                        dist = (SCREEN_WIDTH // 2) - TILE_SIZE - 16
                        s1 = MovingSpikes(TILE_SIZE, TILE_SIZE, axis="horizontal", direction=1, distance=dist)
                        s2 = MovingSpikes(SCREEN_WIDTH - TILE_SIZE - 32, TILE_SIZE, axis="horizontal", direction=-1, distance=dist)
                    elif wall_side == "bottom":
                        dist = (SCREEN_WIDTH // 2) - TILE_SIZE - 16
                        s1 = MovingSpikes(TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE - 32, axis="horizontal", direction=1, distance=dist)
                        s2 = MovingSpikes(SCREEN_WIDTH - TILE_SIZE - 32, SCREEN_HEIGHT - TILE_SIZE - 32, axis="horizontal", direction=-1, distance=dist)
                    elif wall_side == "left":
                        dist = (SCREEN_HEIGHT // 2) - TILE_SIZE - 16
                        s1 = MovingSpikes(TILE_SIZE, TILE_SIZE, axis="vertical", direction=1, distance=dist)
                        s2 = MovingSpikes(TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE - 32, axis="vertical", direction=-1, distance=dist)
                    else: # right
                        dist = (SCREEN_HEIGHT // 2) - TILE_SIZE - 16
                        s1 = MovingSpikes(SCREEN_WIDTH - TILE_SIZE - 32, TILE_SIZE, axis="vertical", direction=1, distance=dist)
                        s2 = MovingSpikes(SCREEN_WIDTH - TILE_SIZE - 32, SCREEN_HEIGHT - TILE_SIZE - 32, axis="vertical", direction=-1, distance=dist)
                    
                    for s in [s1, s2]:
                        all_group.add(s)
                        hazards.add(s)
                        room.hazards.append(("spikes", s.rect.x, s.rect.y, {"axis": s.axis, "direction": s.direction, "distance": s.distance}))
                else:
                    # WallWalkerEnemy: Pick a random perimeter wall to spawn on
                    wall_side = random.choice(["top", "bottom", "left", "right"])
                    if wall_side == "top":
                        wx, wy = random.randint(TILE_SIZE, SCREEN_WIDTH-TILE_SIZE-28), TILE_SIZE
                    elif wall_side == "bottom":
                        wx, wy = random.randint(TILE_SIZE, SCREEN_WIDTH-TILE_SIZE-28), SCREEN_HEIGHT-TILE_SIZE-28
                    elif wall_side == "left":
                        wx, wy = TILE_SIZE, random.randint(TILE_SIZE, SCREEN_HEIGHT-TILE_SIZE-28)
                    else: # right
                        wx, wy = SCREEN_WIDTH-TILE_SIZE-28, random.randint(TILE_SIZE, SCREEN_HEIGHT-TILE_SIZE-28)
                        
                    w = WallWalkerEnemy(wx, wy)
                    all_group.add(w)
                    hazards.add(w)
                    room.hazards.append(("wall_walker", wx, wy, {}))

        # 1. Common Combat Rooms
        if room.type == "common":
            if not room.enemies_cleared:
                spawn_minions()
            setup_hazards()
        
        # 2. Boss Room
        elif room.type == "boss":
            if not room.enemies_cleared:
                b = Boss(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                enemies.add(b)
                all_group.add(b)

        # 3. Special Rooms with Items/Transitions
        else:
            if room.items_collected:
                # Already picked, nothing more to do here usually
                pass
            else:
                # Determine item spawn
                item_class = None
                spawn_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                should_spawn = False

                if room.type == "start":
                    if not player.has_sword:
                        item_class = WoodenSword
                        spawn_pos = (SCREEN_WIDTH // 2, TILE_SIZE * 5)
                        should_spawn = True
                elif room.type == "puzzle":
                    if player.keys == 0:
                        item_class = Key
                        should_spawn = True
                elif room.type == "treasure":
                    if not hasattr(room, 'item_choice'):
                        room.item_choice = random.choice(["sword", "ring"])
                    
                    if room.item_choice == "sword":
                        primary_class, secondary_class = SilverSword, DefenseRing
                        has_primary, has_secondary = player.has_silver_sword, player.has_defense_ring
                    else:
                        primary_class, secondary_class = DefenseRing, SilverSword
                        has_primary, has_secondary = player.has_defense_ring, player.has_silver_sword

                    if not has_primary:
                        item_class = primary_class
                        should_spawn = True
                    elif not has_secondary:
                        item_class = secondary_class
                        should_spawn = True
                elif room.type == "master_key_room":
                    if not player.has_master_key:
                        item_class = MasterKey
                        should_spawn = True
                elif room.type == "victory":
                    item_class = VictoryItem
                    should_spawn = True

                if should_spawn:
                    it = item_class(*spawn_pos)
                    items.add(it)
                    all_group.add(it)
                else:
                    # Item is already taken or duplicate -> Combat encounter
                    if not room.enemies_cleared and room.type != "victory" and room.type != "start":
                        spawn_minions()

        room.setup_walls()

    setup_room(dungeon.get_current_room(), (enemies, items, projectiles, hazards), all_sprites)

    running = True
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. Input Handling
        if game_state == STATE_PLAYING:
            player.handle_input(swords)
            for s in swords: all_sprites.add(s)
        elif game_state == STATE_TITLE:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                # Start game
                player.hp = player.max_hp
                player.keys = 0
                player.has_wooden_sword = False
                player.has_silver_sword = False
                player.has_sword = False
                player.has_defense_ring = False
                player.has_master_key = False
                player.damage = 2
                player.defense = 0
                player.rect.topleft = (SCREEN_WIDTH // 2, TILE_SIZE * 2)
                dungeon = Dungeon(size=3)
                setup_room(dungeon.get_current_room(), (enemies, items, projectiles, hazards), all_sprites)
                game_state = STATE_PLAYING
                continue
        elif game_state == STATE_GAMEOVER:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                # Reset whole game
                player.hp = player.max_hp
                player.keys = 0
                player.has_wooden_sword = False
                player.has_silver_sword = False
                player.has_sword = False
                player.has_defense_ring = False
                player.has_master_key = False
                player.damage = 2
                player.defense = 0
                player.rect.topleft = (SCREEN_WIDTH // 2, TILE_SIZE * 2)
                dungeon = Dungeon(size=3)
                setup_room(dungeon.get_current_room(), (enemies, items, projectiles, hazards), all_sprites)
                game_state = STATE_PLAYING
                continue
        elif game_state == STATE_WIN:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                # Restart (Play again)
                player.hp = player.max_hp
                player.keys = 0
                player.has_wooden_sword = False
                player.has_silver_sword = False
                player.has_sword = False
                player.has_defense_ring = False
                player.has_master_key = False
                player.damage = 2
                player.defense = 0
                player.rect.topleft = (SCREEN_WIDTH // 2, TILE_SIZE * 2)
                dungeon = Dungeon(size=3)
                setup_room(dungeon.get_current_room(), (enemies, items, projectiles, hazards), all_sprites)
                game_state = STATE_PLAYING
                continue
            elif keys[pygame.K_ESCAPE]:
                # Back to Title
                game_state = STATE_TITLE
                continue

        # 3. Game Logic (Update)
        if game_state == STATE_PLAYING:
            current_room = dungeon.get_current_room()
            
            # Room Transitions & Locking
            transitioned = False
            dir_to_move = None
            
            # Check for door collision/intent (now requires alignment with door gap)
            if player.rect.left <= TILE_SIZE + 5 and 200 < player.rect.centery < 240: 
                dir_to_move = "left"
            elif player.rect.right >= SCREEN_WIDTH - TILE_SIZE - 5 and 200 < player.rect.centery < 240: 
                dir_to_move = "right"
            elif player.rect.top <= TILE_SIZE + 5 and 280 < player.rect.centerx < 360: 
                dir_to_move = "up"
            elif player.rect.bottom >= SCREEN_HEIGHT - TILE_SIZE - 5 and 280 < player.rect.centerx < 360: 
                dir_to_move = "down"

            if dir_to_move and current_room.connections[dir_to_move]:
                lock = current_room.locked_doors[dir_to_move]
                
                # Door Unlocking Logic (Check if player is close enough to use key)
                if lock:
                    can_unlock = False
                    if lock == "key" and player.keys > 0:
                        player.keys -= 1
                        can_unlock = True
                    elif lock == "master" and player.has_master_key:
                        can_unlock = True
                    
                    if can_unlock:
                        current_room.locked_doors[dir_to_move] = False
                        nx, ny = current_room.grid_pos
                        if dir_to_move == "up": ny -= 1
                        elif dir_to_move == "down": ny += 1
                        elif dir_to_move == "left": nx -= 1
                        elif dir_to_move == "right": nx += 1
                        opp = {"up":"down", "down":"up", "left":"right", "right":"left"}[dir_to_move]
                        dungeon.rooms[(nx, ny)].locked_doors[opp] = False
                        current_room.setup_walls()
                        lock = False # Door is now open
                        # Break out of intent check to prevent jumpy movement
                        dir_to_move = None 

            # Arena Activation Logic: Only lock doors once player is inside the room
            if not current_room.arena_activated and len(enemies) > 0:
                # Check if player is clearly inside the room (not near any door)
                margin = TILE_SIZE * 2
                if margin < player.rect.centerx < SCREEN_WIDTH - margin and \
                   margin < player.rect.centery < SCREEN_HEIGHT - margin:
                    current_room.arena_activated = True
                    for d in current_room.connections:
                        if current_room.connections[d] and not current_room.locked_doors[d]:
                            current_room.locked_doors[d] = "enemy"
                    current_room.setup_walls()

                # Check if we can actually transition (at the edge and enemies cleared)
            # Check if we can actually transition (must be at the specific edge and aligned)
            at_edge = False
            if dir_to_move == "left" and player.rect.left <= TILE_SIZE: at_edge = True
            elif dir_to_move == "right" and player.rect.right >= SCREEN_WIDTH - TILE_SIZE: at_edge = True
            elif dir_to_move == "up" and player.rect.top <= TILE_SIZE: at_edge = True
            elif dir_to_move == "down" and player.rect.bottom >= SCREEN_HEIGHT - TILE_SIZE: at_edge = True
            
            if at_edge and not lock:
                can_pass = True
                # Enemy clear logic
                if len(enemies) > 0 and current_room.type != "start":
                    can_pass = False

                if can_pass:
                        if dungeon.move(dir_to_move):
                            if dir_to_move == "left": player.rect.right = SCREEN_WIDTH - TILE_SIZE - 20
                            elif dir_to_move == "right": player.rect.left = TILE_SIZE + 20
                            elif dir_to_move == "up": player.rect.bottom = SCREEN_HEIGHT - TILE_SIZE - 20
                            elif dir_to_move == "down": player.rect.top = TILE_SIZE + 20
                            transitioned = True

            if transitioned:
                setup_room(dungeon.get_current_room(), (enemies, items, projectiles, hazards), all_sprites)
                current_room = dungeon.get_current_room()

            # Update sprites
            swords.update()
            projectiles.update()
            for e in enemies:
                if isinstance(e, Boss):
                    e.update_boss(player.rect, current_room.walls, projectiles, all_sprites)
                elif isinstance(e, ShooterEnemy):
                    e.update(player.rect, current_room.walls, projectiles, all_sprites)
                else:
                    e.update(player.rect, current_room.walls)
            
            # Update hazards (MovingSpikes, WallWalkerEnemy)
            for s in hazards:
                if isinstance(s, MovingSpikes):
                    s.update(player.rect)
                elif isinstance(s, WallWalkerEnemy):
                    s.update(player.rect, current_room.walls)
            
            # Physical collision group (Walls + Hazards)
            solid_colliders = pygame.sprite.Group(list(current_room.walls) + list(hazards))
            player.update(solid_colliders)

            # Collision: Sword -> Enemy
            for sword in swords:
                hit_enemies = pygame.sprite.spritecollide(sword, enemies, False)
                for enemy in hit_enemies:
                    enemy.hp -= player.damage
                    if enemy.hp <= 0:
                        enemy.kill()
                        # If all enemies killed (including boss), unlock "enemy" doors and MARK AS CLEARED
                        if len(enemies) == 0:
                            current_room.enemies_cleared = True
                            for d in current_room.locked_doors:
                                if current_room.locked_doors[d] == "enemy":
                                    current_room.locked_doors[d] = False
                            current_room.setup_walls()
            
            # Collision: Projectile -> Player
            if player.iframes <= 0:
                hit_projectiles = pygame.sprite.spritecollide(player, projectiles, True)
                if hit_projectiles:
                    # Get damage from the first projectile that hit
                    dmg = hit_projectiles[0].damage * (1 - player.defense)
                    player.hp -= dmg
                    player.iframes = 60 # 1 second of invincibility
            else:
                # Still consume projectiles even if invincible to avoid stacking hits later
                pygame.sprite.spritecollide(player, projectiles, True)

            # Collision: Item Collection
            picked_items = pygame.sprite.spritecollide(player, items, True)
            if picked_items:
                current_room.items_collected = True
                for item in picked_items:
                    item.kill() # Ensure it's removed from ALL groups including all_sprites
                    if item.item_type == "key":
                        player.keys += 1
                    elif item.item_type == "master_key":
                        player.has_master_key = True
                    elif item.item_type == "wooden_sword":
                        player.has_wooden_sword = True
                        player.has_sword = True
                        player.damage = 2
                    elif item.item_type == "silver_sword":
                        player.has_silver_sword = True
                        player.has_sword = True
                        player.damage = 4
                    elif item.item_type == "defense_ring":
                        player.has_defense_ring = True
                        player.defense = 0.5 # 50% damage reduction
                    elif item.item_type == "victory_item":
                        game_state = STATE_WIN

            # Collision: Enemy -> Player
            if player.iframes <= 0:
                hit_by_enemies = pygame.sprite.spritecollide(player, enemies, False)
                if hit_by_enemies:
                    # Discrete damage with i-frames
                    dmg = 1.0 * (1 - player.defense)
                    player.hp -= dmg
                    player.iframes = 60
            
            # Collision: Hazards (Spikes/WallWalker) -> Player
            if player.iframes <= 0:
                for s in all_sprites:
                    if isinstance(s, (MovingSpikes, WallWalkerEnemy)):
                        if player.rect.colliderect(s.rect):
                            dmg_base = 2.0 if isinstance(s, WallWalkerEnemy) else 1.5
                            player.hp -= dmg_base * (1 - player.defense)
                            player.iframes = 60
                            break
            
            if player.hp <= 0:
                game_state = STATE_GAMEOVER

        # 4. Drawing
        if game_state == STATE_TITLE:
            draw_title_screen(screen, font_overlay, font_sub_overlay)
        else:
            screen.fill((20, 20, 30))
            dungeon.get_current_room().draw(screen)
            all_sprites.draw(screen)
            draw_hud(screen, player, enemies, font_hud, font_boss, font_small)

            if game_state == STATE_GAMEOVER:
                draw_overlay(screen, "GAME OVER", (255, 50, 50), font_overlay, font_sub_overlay)
            elif game_state == STATE_WIN:
                draw_victory_overlay(screen, "DUNGEON CLEARED!", (50, 255, 50), font_overlay, font_sub_overlay)

        pygame.display.flip()
        await asyncio.sleep(0) 
        clock.tick(60)

    # Main loop ends

def draw_title_screen(screen, font, sub_font):
    screen.fill((10, 10, 20))
    
    # Title Text
    title = font.render("DUNGEON CRAWLER", True, (0, 150, 255))
    rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
    screen.blit(title, rect)
    
    # Start Instruction
    start_msg = sub_font.render("Press SPACE to Start Exploration", True, (200, 200, 200))
    start_rect = start_msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    screen.blit(start_msg, start_rect)
    
    # Simple Legend
    legend = sub_font.render("Arrow Keys - Move | Space - Attack", True, (100, 100, 100))
    leg_rect = legend.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
    screen.blit(legend, leg_rect)

def draw_victory_overlay(screen, text, color, font, sub_font):
    # Darker background for overlay
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    s.set_alpha(180)
    s.fill((0, 0, 0))
    screen.blit(s, (0,0))
    
    msg = font.render(text, True, color)
    rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
    screen.blit(msg, rect)
    
    msg1 = sub_font.render("Press SPACE to Play Again", True, (255, 255, 255))
    rect1 = msg1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
    screen.blit(msg1, rect1)
    
    msg2 = sub_font.render("Press ESC for Title Screen", True, (255, 255, 255))
    rect2 = msg2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
    screen.blit(msg2, rect2)

def draw_overlay(screen, text, color, font, sub_font):
    # Darker background for overlay
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    s.set_alpha(128)
    s.fill((0, 0, 0))
    screen.blit(s, (0,0))
    
    msg = font.render(text, True, color)
    rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(msg, rect)
    
    sub_msg = sub_font.render("Press SPACE to Restart", True, (255, 255, 255))
    sub_rect = sub_msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    screen.blit(sub_msg, sub_rect)

def draw_hud(screen, player, enemies, font, font_boss, font_small):
    # Hearts
    heart_color = (255, 0, 0)
    for i in range(3):
        heart_rect = pygame.Rect(10 + i * 35, 10, 30, 30)
        current_heart_hp = max(0, min(2, player.hp - (i * 2)))
        pygame.draw.rect(screen, (50, 50, 50), heart_rect)
        if current_heart_hp > 0:
            fill_rect = pygame.Rect(10 + i * 35, 10, 30 * (current_heart_hp / 2), 30)
            pygame.draw.rect(screen, heart_color, fill_rect)

    # Boss HP if present
    for e in enemies:
        if isinstance(e, Boss):
            boss_bar_rect = pygame.Rect(200, 10, 400, 20)
            pygame.draw.rect(screen, (50, 50, 50), boss_bar_rect)
            fill_w = 400 * (e.hp / e.max_hp)
            pygame.draw.rect(screen, (200, 0, 200), (200, 10, fill_w, 20))
            text_boss = font_boss.render("THE GUARDIAN", True, (255, 255, 255))
            screen.blit(text_boss, (200, 35))
            
    # Key Alert
    if len(enemies) > 0 and len(enemies) < 10: # Only if clearable
        alert = font_small.render("ENEMIES REMAINING!", True, (255, 100, 100))
        screen.blit(alert, (SCREEN_WIDTH // 2 - 70, 50))
            
    # Keys & Info
    keys_text = font.render(f"Keys: {player.keys}", True, (255, 255, 255))
    screen.blit(keys_text, (10, 50))
    
    if player.has_master_key:
        mk_text = font.render("MASTER KEY FOUND", True, (255, 100, 255))
        screen.blit(mk_text, (10, 80))
    
    if player.has_silver_sword:
        ss_text = font.render("SILVER SWORD (2x DMG)", True, (150, 150, 255))
        screen.blit(ss_text, (10, 110))
    elif player.has_wooden_sword:
        ws_text = font.render("WOODEN SWORD (1x DMG)", True, (139, 69, 19))
        screen.blit(ws_text, (10, 110))

    if player.has_defense_ring:
        dr_text = font.render("DEFENSE RING (RESISTANT)", True, (100, 255, 100))
        screen.blit(dr_text, (10, 140))

def run_game():
    # Detect if we are in a web browser
    if sys.platform == "emscripten":
        asyncio.run(main())
    else:
        # Standard local launch
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error: {e}")
        finally:
            pygame.quit()

if __name__ == "__main__":
    run_game()
