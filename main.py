from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from math import ceil

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
screen_width = 128
screen_height = 64
alien_width = 8
alien_height = 5
font_size = 8
# CONTROLS
move_left = Pin(9,  mode=Pin.IN, pull=Pin.PULL_UP) # SW2
move_right = Pin(7,  mode=Pin.IN, pull=Pin.PULL_UP) # SW0
shoot = Pin(12,  mode=Pin.IN, pull=Pin.PULL_UP) # ROT_push
center = int((screen_height - 1) / 2) # Rough middle of the screen height
screen = SSD1306_I2C(screen_width, screen_height, i2c)
screen.fill(0)

class Alien:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.speed = 8
        self.width = width
        self.height = height
        self.index = 0
        
    def speed_adj(self):
        return self.speed / len(GAME.enemies)

    def move(self):
        self.x += self.speed_adj()
        if self.x + self.width > screen_width:
            self.x = 0
            self.y += self.height
        
        if self.y >= screen_height - PLAYER.height * 2:
            PLAYER.life -= 1
            GAME.enemies_to_destroy.append(self.index)
    
    def draw(self):
        screen.fill_rect(int(self.x), int(self.y), self.width, self.height, 1)
    
    def destroy(self):
        GAME.enemies.pop(self.index)
        GAME.score += 10


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
    
    def draw(self):
        screen.fill_rect(int(self.x), int(self.y), self.width, self.height, 1)
    
    def move(self, amnt):
        if self.x + amnt + self.width > screen_width or self.x + amnt < 0:
            return
        self.x += amnt
    
    def controls(self):
        if self.shoot_cd > 0:
            self.shoot_cd -= self.shoot_speed
        if move_left.value() == 0:
            self.move(-1)
        elif move_right.value() == 0:
            self.move(1)
        if shoot.value() == 0:
            self.shoot()
    
    def shoot(self):
        if self.shoot_cd > 0:
            return
        self.shoot_cd = 10
        own_center = ceil(self.width / 2)
        spawn_point = self.x + own_center
        GAME.bullets.append(Bullet(spawn_point, self.bullet_speed, len(GAME.bullets)))
        


class Bullet:
    def __init__(self, x, speed, index):
        self.x = x
        self.y = screen_height - PLAYER.height
        self.speed = speed
        self.index = index
    
    def move(self):
        self.y -= self.speed
        if self.y <= 0:
            GAME.bullets_to_destroy.append(self.index)
    
    def draw(self):
        screen.pixel(self.x, self.y, 1)
        
    def destroy(self):
        GAME.bullets.pop(self.index)
        
    def check_collision(self):
        for i in range(len(GAME.enemies)):
            # This gargantuan line of code checks if the bullet is inside the enemy's bounding box
            # The enemy can for example occupy a space of x = [5, 12] y = [23, 28]
            # if the bullet is then eg. x = 7 and y = 25, it is within the enemy's bounding box
            # and thus collides with the enemy
            if self.x >= GAME.enemies[i].x and self.x <= GAME.enemies[i].x + GAME.enemies[i].width and self.y <= GAME.enemies[i].y and self.y >= GAME.enemies[i].y - GAME.enemies[i].height:
                GAME.enemies_to_destroy.append(i)
                GAME.bullets_to_destroy.append(self.index)
                break
    
    
class Game:
    def __init__(self, enemies_count):
        self.bullets = []
        self.enemies = []
        self.bullets_to_destroy = []
        self.enemies_to_destroy = []
        self.enemies_count = enemies_count
        self.score = 0
        self.add_aliens()
        
    def add_aliens(self):
        alien_x = 0
        alien_y = 8
        for i in range(self.enemies_count):
            self.enemies.append(Alien(alien_x, alien_y, alien_width, alien_height))
            alien_x += alien_width + 2
            if alien_x > screen_width:
                alien_x = 0
                alien_y += alien_height + 2
                
    def draw_ui(self):
        screen.fill_rect(0, 0, screen_width, font_size, 0)
        screen.text(f"SCORE {self.score}", 0, 0)
        screen.text(f"LIFE {PLAYER.life}", int(screen_width / 2 + font_size * 2), 0)
        
    def lose_screen(self):
        screen.fill(0)
        text = "GAME OVER!"
        text_len = len(text) * font_size
        screen.text(text, int(screen_width / 2 - text_len / 2), int(screen_height / 2), 1)
        screen.show()
        
    def win_screen(self):
        screen.fill(0)
        text = "YOU WIN!"
        text2 = f"SCORE {self.score}"
        text_len = len(text) * font_size
        text2_len = len(text2) * font_size
        screen.text(text, int(screen_width / 2 - text_len / 2), int(screen_height / 2), 1)
        screen.text(text2, int(screen_width / 2 - text2_len / 2), int(screen_height / 2), 1)
        screen.show()
    
    def game_loop(self):
        screen.fill(0)
        PLAYER.controls()
        PLAYER.draw()
        for i in range(len(self.bullets)):
            self.bullets[i].index = i
            self.bullets[i].move()
            self.bullets[i].draw()
            self.bullets[i].check_collision()
        for i in range(len(self.enemies)):
            self.enemies[i].index = i
            self.enemies[i].move()
            self.enemies[i].draw()
        # Try exceptions are there to catch list index out of bounds errors
        # as they do not interrupt gameplay noticably.
        for d in self.bullets_to_destroy:
            try:
                self.bullets[d].destroy()
            except:
                pass
        for d in self.enemies_to_destroy:
            try:
                self.enemies[d].destroy()
            except:
                pass
        self.bullets_to_destroy = []
        self.enemies_to_destroy = []
        self.draw_ui()
        screen.show()
        
PLAYER = Player(0, 11, 6, 5, 1, 1, 1)
GAME = Game(32)

while True:
    GAME.game_loop()
    if(len(GAME.enemies) == 0 or PLAYER.life == 0):
        break
    
if PLAYER.life == 0:
    GAME.lose_screen()
else:
    GAME.win_screen()
        


        