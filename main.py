from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from math import ceil

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
screen_width = 128
screen_height = 64
alien_width = 8
alien_height = 5
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
        self.speed = 4
        self.width = width
        self.height = height
        self.index = 0
        
    def speed_adj(self):
        return self.speed / len(enemies)

    def move(self):
        self.x += self.speed_adj()
        if self.x + self.width > screen_width:
            self.x = 0
            self.y += self.height
    
    def draw(self):
        screen.fill_rect(int(self.x), int(self.y), self.width, self.height, 1)
    
    def destroy(self):
        enemies.pop(self.index)


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
        bullets.append(Bullet(spawn_point, self.bullet_speed, len(bullets)))
        


class Bullet:
    def __init__(self, x, speed, index):
        self.x = x
        self.y = screen_height - PLAYER.height
        self.speed = speed
        self.index = index
    
    def move(self):
        self.y -= self.speed
        if self.y <= 0:
            bullets_to_destroy.append(self.index)
    
    def draw(self):
        screen.pixel(self.x, self.y, 1)
        
    def destroy(self):
        bullets.pop(self.index)
        
    def check_collision(self):
        for i in range(len(enemies)):
            if self.x >= enemies[i].x and self.x <= enemies[i].x + enemies[i].width and self.y <= enemies[i].y and self.y >= enemies[i].y - enemies[i].height:
                enemies_to_destroy.append(i)
                bullets_to_destroy.append(self.index)
                break
    
        
PLAYER = Player(0, 11, 6, 5, 1, 1, 1)
        
    

bullets = []
enemies = []
bullets_to_destroy = []
enemies_to_destroy = []
enemies_count = 32
alien_x = 0
alien_y = 0
for i in range(enemies_count):
    enemies.append(Alien(alien_x, alien_y, alien_width, alien_height))
    alien_x += alien_width + 2
    if alien_x > screen_width:
        alien_x = 0
        alien_y += alien_height + 2

while True:
    screen.fill(0)
    PLAYER.controls()
    PLAYER.draw()
    for i in range(len(bullets)):
        bullets[i].index = i
        bullets[i].move()
        bullets[i].draw()
        bullets[i].check_collision()
    for i in range(len(enemies)):
        enemies[i].index = i
        enemies[i].move()
        enemies[i].draw()
    for d in bullets_to_destroy:
        bullets.pop(d)
    for d in enemies_to_destroy:
        enemies.pop(d)
    bullets_to_destroy = []
    enemies_to_destroy = []
    screen.show()
        