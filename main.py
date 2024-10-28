from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from math import ceil
import framebuf
import random

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
screen_width = 128
screen_height = 64
alien_width = 10
alien_height = 7
font_size = 8
# CONTROLS
move_left = Pin(9,  mode=Pin.IN, pull=Pin.PULL_UP) # SW2
move_right = Pin(7,  mode=Pin.IN, pull=Pin.PULL_UP) # SW0
shoot = Pin(12,  mode=Pin.IN, pull=Pin.PULL_UP) # ROT_push
center = int((screen_height - 1) / 2) # Rough middle of the screen height
screen = SSD1306_I2C(screen_width, screen_height, i2c)
screen.fill(0)
player_model = bytearray([0x30, 0x38, 0x28, 0x28, 0x14, 0x1F, 0x14, 0x28, 0x28, 0x38, 0x30]) # player sprite as a bytemap
alien_model = bytearray([0x60, 0x12, 0x79, 0x56, 0x1C, 0x1C, 0x56, 0x79, 0x12, 0x60]) # alien sprite as a bytemap
alien_death_model = bytearray([0x24, 0x52, 0x09, 0x10, 0x45, 0x20, 0x15, 0x22, 0x44, 0x28]) # alien sprite when pew pew hit

alien_sprite = framebuf.FrameBuffer(alien_model, alien_width, alien_height, framebuf.MONO_VLSB) # create image of alien sprite
alien_death_sprite = framebuf.FrameBuffer(alien_death_model, alien_width, alien_height, framebuf.MONO_VLSB) # create image of ded alien sprite
class Alien:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.speed = 7
        self.width = width
        self.height = height
        self.index = 0
        self.bullet_speed = 1
        self.alive = True
        self.death_timer = 1
        
        
    def speed_adj(self): # Mimic difficulty of OG space invaders, the fewer enemies, the faster they move.
        return self.speed / len(GAME.enemies) # Use fewer when what you're talking about can be counted, and less if it can't be. (Stannis)

    def move(self):
        if not self.alive:
            self.death_timer -= 1 / 8
            if self.death_timer <= 0:
                GAME.enemies.pop(self.index)
            return  
        self.x += self.speed_adj() # Move by the difficulty adjusted speed
        if self.x + self.width > screen_width: # Once an alien reaches the edge of the screen, it goes down by 1 length.
            self.x = 0
            self.y += self.height
        
        if self.y >= screen_height - PLAYER.height * 2: # If the alien reaches the player, remove life from player and kill alien
            PLAYER.life -= 5
            self.destroy(p_kill = False)
            
        if random.randint(1, 500) == 500:
            self.shoot()
    
    def draw(self): # Draw alien at its current position
        if self.alive:
            screen.blit(alien_sprite, int(self.x), int(self.y))
        else:
            screen.blit(alien_death_sprite, int(self.x), int(self.y))
    
    def destroy(self, p_kill = True): # Remove the alien from the game and increase player's score if killed by bullet
        self.alive = False
        if p_kill:
            GAME.score += 25
            
    def shoot(self):
        own_center = ceil(self.width / 2) # Get center of alien model
        spawn_x = int(self.x + own_center) # Find where the bullet should spawn at on x axis
        spawn_y = int(self.y + self.height) # Find where the bullet should spawn at on y axis
        GAME.bullets.append(Bullet(spawn_x, spawn_y, self.bullet_speed, len(GAME.bullets), direction = 1)) # Create new Bullet instance


class Player:
    def __init__(self, x, width, height, life, shoot_speed, mov_speed, bullet_speed):
        self.x = x
        self.y = screen_height - height
        self.width = width
        self.height = height
        self.life = life
        self.shoot_cd = 0
        self.shoot_speed = shoot_speed
        self.mov_speed = mov_speed
        self.bullet_speed = bullet_speed
        self.sprite = framebuf.FrameBuffer(player_model, self.width, self.height, framebuf.MONO_VLSB) # create image of player sprite
        self.invulnerable = 0
    
    def draw(self):
        if self.invulnerable % 2 == 0:
            screen.blit(self.sprite, int(self.x), int(self.y)) # draw sprite on player location
    
    def move(self, amnt):
        # Check if the player touches either side of the screen
        # if so, prevent movement in that direction
        if self.x + amnt + self.width > screen_width or self.x + amnt < 0:
            return
        self.x += amnt # move by 1 px left or right
    
    def controls(self):
        if self.shoot_cd > 0: # Lower cooldown every frame, if it's above 0
            self.shoot_cd -= self.shoot_speed
        if move_left.value() == 0: # Move left button pressed, move 1px left
            self.move(-1)
        elif move_right.value() == 0: # Move right button pressed, move 1px right
            self.move(1)
        if shoot.value() == 0: # Shoot button pressed, SHOOT!
            self.shoot()
    
    def shoot(self):
        if self.shoot_cd > 0: # Shooting on cooldown, can't pewpew!
            return
        self.shoot_cd = 10 # Cooldown 10 means that you can shoot once every ~17 frames.
        own_center = ceil(self.width / 2) # Get center of player model
        spawn_x = self.x + own_center # Find where the bullet should spawn at on x axis
        spawn_y = screen_height - self.height # Find where the bullet should spawn at on y axis
        GAME.bullets.append(Bullet(spawn_x, spawn_y, self.bullet_speed, len(GAME.bullets), direction = -1)) # Create new Bullet instance
        
    def invulnerability(self):
        if self.invulnerable > 0:
            self.invulnerable -= 1
            
    def hurt(self):
        if self.invulnerable <= 0:
            self.life -= 1
            self.invulnerable = 100


class Bullet:
    def __init__(self, x, y, speed, index, direction):
        self.x = x
        self.y = y
        self.speed = speed
        self.index = index
        self.direction = direction
    
    # Moves the bullet up (-y) by 1 pixel per frame.
    def move(self):
        self.y += self.speed * self.direction # direction is either +1 or -1
        if self.y <= 0 or self.y >= screen_height: # mark the bullet for destruction when it hits the edge of the screen
            self.destroy()
            
    # Draws the bullet as a single pixel in its current position
    def draw(self):
        screen.pixel(self.x, self.y, 1)
        
    def destroy(self):
        GAME.bullets.pop(self.index)
        
    def check_collision(self):
        if self.direction > 0:
            # This line of code checks if a bullet is colliding with the player's bounding box
            if self.x >= PLAYER.x and self.x <= PLAYER.x + PLAYER.width and self.y <= PLAYER.y and self.y >= PLAYER.y - PLAYER.height:
                PLAYER.hurt()
                self.destroy()
        else:
            for i in range(len(GAME.enemies)):
                # This gargantuan line of code checks if the bullet is inside the enemy's bounding box
                # The enemy can for example occupy a space of x = [5, 12] y = [23, 28]
                # if the bullet is then eg. x = 7 and y = 25, it is within the enemy's bounding box
                # and thus collides with the enemy
                if self.x >= GAME.enemies[i].x and self.x <= GAME.enemies[i].x + GAME.enemies[i].width and self.y <= GAME.enemies[i].y and self.y >= GAME.enemies[i].y - GAME.enemies[i].height:
                    GAME.enemies[i].destroy()
                    self.destroy()
                    break
        for i in range(len(GAME.bullets)):
            if self.x == GAME.bullets[i].x and (self.y + 1 == GAME.bullets[i].y or self.y - 1 == GAME.bullets[i].y):
                GAME.bullets[i].destroy()
                self.destroy()
                break
    
    
class Game:
    def __init__(self, enemies_count):
        self.bullets = []
        self.enemies = []
        self.enemies_count = enemies_count
        self.score = 0
        self.add_aliens()
        
    # Populates the enemies list with instances of the Alien class.
    # They start spawning at y = 8 to prevent the header from obstructing them.
    # Aliens are spawned with a 3 pixel margin.
    # TODO: One column of aliens always spawns without y margin, find cause and fix.
    def add_aliens(self):
        alien_x = 0 # what x position the alien spawns in
        alien_y = 8 # what y position the alien spawns in
        for i in range(self.enemies_count):
            self.enemies.append(Alien(alien_x, alien_y, alien_width, alien_height))
            alien_x += alien_width + 3 # increment spawning x by width + 3, by default 11px
            if alien_x > screen_width:
                alien_x = 0 # reset spawning x to left side
                alien_y += alien_height + 3 # increment spawning y by height + 3, by default 8px
                
    # Draws the header that displays score and lives at the top of the screen
    # Its dimensions are 128x8 by default
    def draw_ui(self):
        screen.fill_rect(0, 0, screen_width, font_size, 0)
        screen.text(f"SCORE {self.score}", 0, 0)
        screen.text(f"HP {PLAYER.life}", int(screen_width - font_size * 4), 0)
        
    # Draws lose screen with the text in the middle of the screen
    def lose_screen(self):
        screen.fill(0)
        text = "GAME OVER!"
        text2 = "EARTH IS NEXT.."
        text_len = len(text) * font_size
        text2_len = len(text2) * font_size
        screen.text(text, int(screen_width / 2 - text_len / 2), int(screen_height / 2 - font_size), 1)
        screen.text(text2, int(screen_width / 2 - text2_len / 2), int(screen_height / 2 + font_size), 1)
        screen.show()
        
    # Draws win screen with the text in the middle of the screen
    def win_screen(self):
        screen.fill(0)
        text = "YOU WIN!"
        text2 = f"SCORE {self.score}"
        text_len = len(text) * font_size
        text2_len = len(text2) * font_size
        screen.text(text, int(screen_width / 2 - text_len / 2), int(screen_height / 2  - font_size), 1)
        screen.text(text2, int(screen_width / 2 - text2_len / 2), int(screen_height / 2 + font_size), 1)
        screen.show()
    
    def game_loop(self):
        screen.fill(0)
        PLAYER.controls()
        PLAYER.invulnerability()
        PLAYER.draw()
        # Loop through each bullet and apply its per tick methods
        # The looping is done in reverse because the list is being modified during it.
        for i in range(len(self.bullets) - 1, -1, -1): # Start at list length - 1, stop when i decrements to -1.
            self.bullets[i].index = i # set index for destroy() function
            self.bullets[i].move()
            if i > len(self.bullets) - 1: # check if bullet was destroyed during move()
                continue
            self.bullets[i].draw()
            self.bullets[i].check_collision() # check if currently colliding with alien
            
        # Since enemies can be destroyed the same as bullets, reverse loop is needed here too.
        for i in range(len(self.enemies) - 1, -1, -1):
            self.enemies[i].index = i # set index for destroy() function
            self.enemies[i].move() 
            if i > len(self.enemies) - 1: # check if enemy was destroyed during move()
                continue
            self.enemies[i].draw()
        self.draw_ui()
        screen.show()
        
PLAYER = Player(x = 0, width = 11, height = 6, life = 5, shoot_speed = 0.6, mov_speed = 1, bullet_speed = 2)
GAME = Game(16)

while True:
    GAME.game_loop()
    if(len(GAME.enemies) == 0 or PLAYER.life == 0):
        break
    
if PLAYER.life <= 0:
    GAME.lose_screen()
else:
    GAME.win_screen()
        


        