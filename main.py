from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
screen_width = 128
screen_height = 64
alien_width = 8
alien_height = 5
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
        
    def speed_adj(self):
        return self.speed / len(enemies)

    def move(self):
        self.x += self.speed_adj()
        if self.x + self.width > screen_width:
            self.x = 0
            self.y += self.height
    
    def draw(self):
        screen.fill_rect(int(self.x), int(self.y), self.width, self.height, 1)

enemies = []
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
    for alien in enemies:
        alien.move()
        alien.draw()
    screen.show()
        
print(enemies[31].x, enemies[31].y)