import pygame
import sys
import asyncio
from entities import Player, Enemy, Sword, Key, MasterKey, SilverSword, DefenseRing, Boss, Projectile
from map_gen import Dungeon, SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE
import random

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
    
    # Game State
    STATE_PLAYING = 0
    STATE_GAMEOVER = 1
    STATE_WIN = 2
    game_state = STATE_PLAYING

    def setup_room(room, groups, all_group):
        enemies, items, projectiles = groups
        enemies.empty()
        items.empty()
        projectiles.empty()
        
        # Remove old entities
        for s in list(all_group):
            if isinstance(s, (Enemy, Key, MasterKey, SilverSword, DefenseRing, Projectile, Boss)): s.kill()
        
        # Spawn enemies
        if room.type == "common":
            for _ in range(random.randint(2, 4)):
                e = Enemy(random.randint(TILE_SIZE * 2, SCREEN_WIDTH - TILE_SIZE * 3), 
                          random.randint(TILE_SIZE * 2, SCREEN_HEIGHT - TILE_SIZE * 3))
                enemies.add(e)
                all_group.add(e)
        
        # Spawn Boss
        elif room.type == "boss":
            b = Boss(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            enemies.add(b)
            all_group.add(b)
        
        # Spawn initial weapon in Start Room
        elif room.type == "start":
            # Spawn sword slightly ahead of the player (who is at top)
            w = SilverSword(SCREEN_WIDTH // 2, TILE_SIZE * 5)
            items.add(w)
            all_group.add(w)

        # Spawn items in special rooms
        if room.type == "puzzle":
            k = Key(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            items.add(k)
            all_group.add(k)
        elif room.type == "treasure":
            upg = random.choice([SilverSword, DefenseRing])(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            items.add(upg)
            all_group.add(upg)
        elif room.type == "master_key_room":
            mk = MasterKey(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            items.add(mk)
            all_group.add(mk)

    setup_room(dungeon.get_current_room(), (enemies, items, projectiles), all_sprites)

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
        else:
            # Simple restart on Space if dead or won
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                # Reset whole game
                player.hp = player.max_hp
                player.keys = 0
                player.has_master_key = False
                player.has_silver_sword = False
                player.damage = 2
                player.defense = 0
                player.rect.topleft = (SCREEN_WIDTH // 2, TILE_SIZE * 2)
                dungeon = Dungeon(size=3)
                setup_room(dungeon.get_current_room(), (enemies, items, projectiles), all_sprites)
                game_state = STATE_PLAYING
                continue

        # 3. Game Logic (Update)
        if game_state == STATE_PLAYING:
            current_room = dungeon.get_current_room()
            
            # Room Transitions
            transitioned = False
            dir_to_move = None
            if player.rect.left < 5: dir_to_move = "left"
            elif player.rect.right > SCREEN_WIDTH - 5: dir_to_move = "right"
            elif player.rect.top < 5: dir_to_move = "up"
            elif player.rect.bottom > SCREEN_HEIGHT - 5: dir_to_move = "down"

            if dir_to_move and current_room.connections[dir_to_move]:
                lock = current_room.locked_doors[dir_to_move]
                can_pass = True
                if lock == "master" and not player.has_master_key:
                    can_pass = False
                
                if can_pass:
                    if dungeon.move(dir_to_move):
                        if dir_to_move == "left": player.rect.right = SCREEN_WIDTH - 15
                        elif dir_to_move == "right": player.rect.left = 15
                        elif dir_to_move == "up": player.rect.bottom = SCREEN_HEIGHT - 15
                        elif dir_to_move == "down": player.rect.top = 15
                        transitioned = True

            if transitioned:
                setup_room(dungeon.get_current_room(), (enemies, items, projectiles), all_sprites)
                current_room = dungeon.get_current_room()

            # Update sprites
            swords.update()
            projectiles.update()
            for e in enemies:
                if isinstance(e, Boss):
                    e.update_boss(player.rect, current_room.walls, projectiles, all_sprites)
                    if e.hp <= 0:
                        game_state = STATE_WIN
                else:
                    e.chase_player(player.rect, current_room.walls)
            
            # Check collision with walls
            player.update(current_room.walls)

            # Collision: Sword -> Enemy
            for sword in swords:
                hit_enemies = pygame.sprite.spritecollide(sword, enemies, False)
                for enemy in hit_enemies:
                    enemy.hp -= player.damage
                    if enemy.hp <= 0 and not isinstance(enemy, Boss):
                        enemy.kill()
            
            # Collision: Projectile -> Player
            hit_projectiles = pygame.sprite.spritecollide(player, projectiles, True)
            if hit_projectiles:
                player.hp -= 1 * (1 - player.defense)

            # Collision: Item Collection
            picked_items = pygame.sprite.spritecollide(player, items, True)
            for item in picked_items:
                if item.item_type == "key":
                    player.keys += 1
                elif item.item_type == "master_key":
                    player.has_master_key = True
                elif item.item_type == "silver_sword":
                    player.has_silver_sword = True
                    player.damage = 4
                elif item.item_type == "defense_ring":
                    player.has_defense_ring = True
                    player.defense = 0.5 

            # Collision: Enemy -> Player
            hit_by_enemies = pygame.sprite.spritecollide(player, enemies, False)
            if hit_by_enemies:
                dmg = 0.05 * (1 - player.defense)
                player.hp -= dmg
            
            if player.hp <= 0:
                game_state = STATE_GAMEOVER

        # 4. Drawing
        screen.fill((20, 20, 30))
        dungeon.get_current_room().draw(screen)
        all_sprites.draw(screen)
        draw_hud(screen, player, enemies)

        if game_state == STATE_GAMEOVER:
            draw_overlay(screen, "GAME OVER", (255, 50, 50))
        elif game_state == STATE_WIN:
            draw_overlay(screen, "YOU WIN! DUNGEON CLEARED", (50, 255, 50))

        pygame.display.flip()
        await asyncio.sleep(0) # Let the browser breathe (required for Pyodide)
        clock.tick(60)

    pygame.quit()
    sys.exit()

def draw_overlay(screen, text, color):
    # Darker background for overlay
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    s.set_alpha(128)
    s.fill((0, 0, 0))
    screen.blit(s, (0,0))
    
    font = pygame.font.SysFont("Arial", 40, bold=True)
    msg = font.render(text, True, color)
    rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(msg, rect)
    
    sub_font = pygame.font.SysFont("Arial", 20)
    sub_msg = sub_font.render("Press SPACE to Restart", True, (255, 255, 255))
    sub_rect = sub_msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    screen.blit(sub_msg, sub_rect)

def draw_hud(screen, player, enemies):
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
            font = pygame.font.SysFont("Arial", 16)
            text = font.render("THE GUARDIAN", True, (255, 255, 255))
            screen.blit(text, (200, 35))
            
    # Keys & Info
    font = pygame.font.SysFont("Arial", 20)
    keys_text = font.render(f"Keys: {player.keys}", True, (255, 255, 255))
    screen.blit(keys_text, (10, 50))
    
    if player.has_master_key:
        mk_text = font.render("MASTER KEY FOUND", True, (255, 100, 255))
        screen.blit(mk_text, (10, 80))
    
    if player.has_silver_sword:
        ss_text = font.render("SILVER SWORD (2x DMG)", True, (150, 150, 255))
        screen.blit(ss_text, (10, 110))

    if player.has_defense_ring:
        dr_text = font.render("DEFENSE RING (RESISTANT)", True, (100, 255, 100))
        screen.blit(dr_text, (10, 140))

if __name__ == "__main__":
    asyncio.run(main())
