import pygame
import math, time
import random
from pygame.locals import *
import asyncio

random.seed(time.time())
# === Configuration ===
SCREEN_W, SCREEN_H = 1024, 768
FPS = 60
MAP_SCALE = 0.25
CELL = 64


# Maze dimensions
MAP_W = MAP_H = 47


# Function to generate a solvable maze
def generate_maze(width, height):
   maze = [[1 for _ in range(width)] for _ in range(height)]
   directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]


   def carve(x, y):
       maze[y][x] = 0
       random.shuffle(directions)
       for dx, dy in directions:
           nx, ny = x + dx, y + dy
           if 0 < nx < width - 1 and 0 < ny < height - 1 and maze[ny][nx] == 1:
               maze[y + dy // 2][x + dx // 2] = 0
               carve(nx, ny)


   carve(1, 1)
   maze[0][1] = 0
   maze[height - 1][width - 2] = 0
   return maze


# Create maze and color
MAZE = generate_maze(MAP_W, MAP_H)
r, g, b = [random.randint(120, 255) for _ in range(3)]


# Raycasting settings
FOV = math.pi / 3
NUM_RAYS = 400
MAX_DEPTH = MAP_W * CELL
DELTA_ANGLE = FOV / NUM_RAYS
DIST = NUM_RAYS / (2 * math.tan(FOV / 2))
PROJ_COEFF = 3 * DIST * CELL
SCALE = SCREEN_W / NUM_RAYS


# Player settings
gx, gy = CELL * 1.5, CELL * 1.5
pa = 0.0
vertical_offset = 0.0
vertical_vel = 0.0
on_ground = True
show_minimap = False


def mapping(x, y):
   return int(x // CELL), int(y // CELL)


def ray_casting(sc, px, py, pa, mid_y):
   ox, oy = px, py
   cur_angle = pa - FOV / 2
   prev_cell = None
   for ray in range(NUM_RAYS):
       sin_a = math.sin(cur_angle)
       cos_a = math.cos(cur_angle)
       for depth in range(1, int(MAX_DEPTH), 2):
           x = ox + depth * cos_a
           y = oy + depth * sin_a
           i, j = mapping(x, y)
           if 0 <= i < MAP_W and 0 <= j < MAP_H and MAZE[j][i] == 1:
               depth_corr = depth * math.cos(pa - cur_angle)
               proj_h = PROJ_COEFF / (depth_corr + 0.0001)
               shade = 1 / (1 + depth_corr * depth_corr * 0.00002)
               base_color = (r, g, b)
               color = tuple(min(255, int(c * shade)) for c in base_color)
               x_pos = int(ray * SCALE)
               height = int(proj_h)
               top = int(mid_y - height / 2)


               pygame.draw.rect(sc, color, (x_pos, top, math.ceil(SCALE), height))


               if prev_cell and (i != prev_cell[0] or j != prev_cell[1]):
                   pygame.draw.line(sc, (0, 0, 0), (x_pos, top), (x_pos, top + height), 1)


               prev_cell = (i, j)
               break
       cur_angle += DELTA_ANGLE


def draw_minimap(sc, px, py, pa):
   mini_w = int(MAP_W * CELL * MAP_SCALE)
   mini_h = int(MAP_H * CELL * MAP_SCALE)
   map_surf = pygame.Surface((mini_w, mini_h))
   map_surf.set_alpha(200)
   map_surf.fill((40, 40, 40))
   for j, row in enumerate(MAZE):
       for i, cell in enumerate(row):
           color = (200, 200, 200) if cell else (30, 30, 30)
           pygame.draw.rect(map_surf, color,
                            (i * CELL * MAP_SCALE, j * CELL * MAP_SCALE,
                             CELL * MAP_SCALE - 2, CELL * MAP_SCALE - 2))
   px_m = int(px * MAP_SCALE)
   py_m = int(py * MAP_SCALE)
   pygame.draw.circle(map_surf, (255, 0, 0), (px_m, py_m), 5)
   dx = math.cos(pa) * 20
   dy = math.sin(pa) * 20
   pygame.draw.line(map_surf, (0, 255, 0), (px_m, py_m),
                    (int((px + dx) * MAP_SCALE), int((py + dy) * MAP_SCALE)), 2)
   sc.blit(map_surf, (5, 5))


def main():
   global gx, gy, pa, vertical_offset, vertical_vel, on_ground, show_minimap

   pygame.init()
   screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
   pygame.display.set_caption("3D Maze - Auto Generated")
   clock = pygame.time.Clock()


   while True:
       dt = clock.tick(FPS) / 1000.0
       for event in pygame.event.get():
           if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
               pygame.quit()
           if event.type == KEYDOWN and event.key == K_m:
               show_minimap = not show_minimap
           if event.type == KEYDOWN and event.key == K_SPACE and on_ground:
               vertical_vel = 250.0
               on_ground = False


       keys = pygame.key.get_pressed()
       speed = 180 * dt
       dx = dy = 0.0
       if keys[K_w]: dx += math.cos(pa) * speed; dy += math.sin(pa) * speed
       if keys[K_s]: dx -= math.cos(pa) * speed; dy -= math.sin(pa) * speed
       if keys[K_a]: pa -= 2.2 * dt
       if keys[K_d]: pa += 2.2 * dt


       # Collision
       nx, ny = gx + dx, gy + dy
       if MAZE[int(gy // CELL)][int(nx // CELL)] == 0: gx = nx
       if MAZE[int(ny // CELL)][int(gx // CELL)] == 0: gy = ny


       # Jumping
       if not on_ground:
           vertical_vel -= 500 * dt
           vertical_offset += vertical_vel * dt
           if vertical_offset <= 0:
               vertical_offset = 0
               vertical_vel = 0
               on_ground = True


       screen.fill((100, 100, 100))
       mid_y = SCREEN_H // 2 + int(vertical_offset)
       pygame.draw.rect(screen, (45, 45, 45), (0, 0, SCREEN_W, mid_y))       # sky
       pygame.draw.rect(screen, (25, 25, 25), (0, mid_y, SCREEN_W, SCREEN_H - mid_y))  # ground
       ray_casting(screen, gx, gy, pa, mid_y)
       if show_minimap:
           draw_minimap(screen, gx, gy, pa)
       pygame.display.flip()

       await asyncio.sleep(0)

asyncio.run(main())





