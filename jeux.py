import pygame
import sys
import math
import random

# ─────────────────────────────────────────────
#  INIT
# ─────────────────────────────────────────────
pygame.init()
pygame.mixer.init()

W, H = 900, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("⚡ Shadow Runner – Complete Platformer")
clock = pygame.time.Clock()
FPS = 60

# ─────────────────────────────────────────────
#  COLOURS
# ─────────────────────────────────────────────
SKY      = (20,  20,  45)
SKY2     = (35,  35,  75)
GROUND_C = (60,  80,  60)
PLAT_C   = (70, 110,  70)
PLAT_C2  = (100, 60,  40)   # wood platforms
PLAT_C3  = (50,  50, 120)   # ice platforms
SPIKES_C = (200,  50,  50)
COIN_C   = (255, 210,  50)
STAR_C   = (255, 255, 150)
PLAYER_C = (80, 160, 255)
PLAYER_S = (255, 100,  80)   # shadow form
ENEMY_C  = (220,  60,  60)
ENEMY2_C = (180,  60, 200)
HUD_BG   = (0,0,0,160)
WHITE    = (255,255,255)
BLACK    = (0,0,0)
RED      = (220,50,50)
GREEN    = (50,220,80)
YELLOW   = (255,220,50)
CYAN     = (80,220,255)
PURPLE   = (160,80,255)
ORANGE   = (255,140,40)

# ─────────────────────────────────────────────
#  FONTS
# ─────────────────────────────────────────────
font_big   = pygame.font.SysFont("consolas", 54, bold=True)
font_med   = pygame.font.SysFont("consolas", 32, bold=True)
font_small = pygame.font.SysFont("consolas", 22)
font_tiny  = pygame.font.SysFont("consolas", 16)

# ─────────────────────────────────────────────
#  HELPER
# ─────────────────────────────────────────────
def text(surf, msg, fnt, color, cx, cy, shadow=True):
    if shadow:
        s = fnt.render(msg, True, (0,0,0))
        surf.blit(s, s.get_rect(center=(cx+2, cy+2)))
    r = fnt.render(msg, True, color)
    surf.blit(r, r.get_rect(center=(cx, cy)))

def draw_rounded_rect(surf, color, rect, radius=10):
    pygame.draw.rect(surf, color, rect, border_radius=radius)

# ─────────────────────────────────────────────
#  PARTICLES
# ─────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, life=None, size=None):
        self.x = x; self.y = y
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-3, 3)
        self.vy = vy if vy is not None else random.uniform(-5, -1)
        self.life = life if life else random.randint(20, 45)
        self.max_life = self.life
        self.size = size if size else random.randint(3, 7)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 1

    def draw(self, surf, ox):
        alpha = max(0, int(255 * self.life / self.max_life))
        r = max(1, int(self.size * self.life / self.max_life))
        c = (*self.color[:3], alpha)
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, c, (r, r), r)
        surf.blit(s, (int(self.x - ox - r), int(self.y - r)))

particles = []

def spawn_particles(x, y, color, n=8, **kw):
    for _ in range(n):
        particles.append(Particle(x, y, color, **kw))

# ─────────────────────────────────────────────
#  CAMERA
# ─────────────────────────────────────────────
class Camera:
    def __init__(self):
        self.x = 0
        self.target_x = 0

    def update(self, px, level_w):
        self.target_x = px - W // 3
        self.target_x = max(0, min(self.target_x, level_w - W))
        self.x += (self.target_x - self.x) * 0.1

    @property
    def ox(self):
        return int(self.x)

# ─────────────────────────────────────────────
#  PLATFORM
# ─────────────────────────────────────────────
class Platform:
    """
    kind: 'normal' | 'wood' | 'ice' | 'moving' | 'crumble' | 'spike'
    """
    def __init__(self, x, y, w, h=18, kind='normal',
                 move_range=0, move_speed=1.5, move_dir=1):
        self.rect   = pygame.Rect(x, y, w, h)
        self.kind   = kind
        self.ox     = x
        self.move_range  = move_range
        self.move_speed  = move_speed
        self.move_dir    = move_dir
        self.crumble_timer = 0
        self.crumbling = False
        self.dead   = False
        self.respawn_timer = 0
        self.orig_rect = self.rect.copy()

    def update(self):
        if self.kind == 'moving':
            self.rect.x += self.move_speed * self.move_dir
            if abs(self.rect.x - self.ox) >= self.move_range:
                self.move_dir *= -1

        if self.kind == 'crumble' and self.crumbling:
            self.crumble_timer += 1
            if self.crumble_timer > 40:
                self.dead = True
                self.respawn_timer = 180

        if self.dead:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.dead = False
                self.crumbling = False
                self.crumble_timer = 0
                self.rect = self.orig_rect.copy()

    def draw(self, surf, ox):
        if self.dead:
            return
        rx = self.rect.x - ox
        col = {
            'normal' : PLAT_C,
            'wood'   : PLAT_C2,
            'ice'    : PLAT_C3,
            'moving' : (80, 140, 200),
            'crumble': (170, 100, 50),
            'spike'  : SPIKES_C,
        }.get(self.kind, PLAT_C)

        if self.crumbling:
            col = (col[0]//2, col[1]//2, col[2]//2)

        draw_rounded_rect(surf, col,
            pygame.Rect(rx, self.rect.y, self.rect.w, self.rect.h), 5)

        # top highlight
        pygame.draw.rect(surf,
            tuple(min(255, c+60) for c in col),
            pygame.Rect(rx+4, self.rect.y+2, self.rect.w-8, 4), border_radius=2)

        if self.kind == 'spike':
            n = self.rect.w // 14
            for i in range(n):
                tx = rx + 7 + i*14
                pygame.draw.polygon(surf, (255,80,80),
                    [(tx, self.rect.y), (tx-6, self.rect.y-14), (tx+6, self.rect.y-14)])

        if self.kind == 'ice':
            pygame.draw.rect(surf, (180,220,255,80),
                pygame.Rect(rx+2, self.rect.y+3, self.rect.w-4, 5), border_radius=2)

# ─────────────────────────────────────────────
#  COIN
# ─────────────────────────────────────────────
class Coin:
    def __init__(self, x, y, kind='gold'):
        self.x = x; self.y = y
        self.kind = kind   # 'gold' | 'gem'
        self.collected = False
        self.angle = random.uniform(0, 360)
        self.bob = random.uniform(0, math.pi*2)

    def update(self):
        self.angle += 4
        self.bob   += 0.08

    def draw(self, surf, ox):
        if self.collected: return
        rx = self.x - ox
        by = self.y + math.sin(self.bob) * 4

        if self.kind == 'gem':
            col = CYAN
            points = [
                (rx,    by-12),
                (rx+8,  by),
                (rx,    by+8),
                (rx-8,  by),
            ]
            pygame.draw.polygon(surf, col, points)
            pygame.draw.polygon(surf, WHITE, points, 1)
        else:
            pygame.draw.circle(surf, COIN_C,  (int(rx), int(by)), 9)
            pygame.draw.circle(surf, (255,240,120), (int(rx)-2, int(by)-2), 4)

# ─────────────────────────────────────────────
#  ENEMY
# ─────────────────────────────────────────────
class Enemy:
    def __init__(self, x, y, kind='walker', patrol=100):
        self.x = float(x); self.y = float(y)
        self.kind = kind
        self.vx = 1.5 if kind != 'flyer' else 1.2
        self.vy = 0.0
        self.dir = 1
        self.patrol = patrol
        self.ox = x
        self.alive = True
        self.stomp_immune = (kind == 'spiky')
        self.angle = 0
        self.w = 30; self.h = 30
        self.flash = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w//2), int(self.y - self.h), self.w, self.h)

    def update(self, platforms):
        if not self.alive: return
        self.angle += 3

        if self.kind == 'flyer':
            self.y += math.sin(pygame.time.get_ticks() * 0.03) * 0.8
            self.x += self.vx * self.dir
            if abs(self.x - self.ox) > self.patrol:
                self.dir *= -1
        else:
            self.vy += 0.5
            self.x += self.vx * self.dir
            self.y += self.vy

            # platform collision
            for p in platforms:
                if p.dead or p.kind == 'spike': continue
                pr = p.rect
                er = self.rect
                if er.colliderect(pr) and self.vy >= 0 and er.bottom - self.vy*1.5 <= pr.top + 4:
                    self.y = pr.top
                    self.vy = 0

            # patrol reversal
            if abs(self.x - self.ox) > self.patrol:
                self.dir *= -1

        if self.flash > 0: self.flash -= 1

    def draw(self, surf, ox):
        if not self.alive: return
        rx = int(self.x - ox)
        ry = int(self.y)

        col = ENEMY2_C if self.kind == 'flyer' else ENEMY_C
        if self.stomp_immune: col = (180, 80, 80)
        if self.flash > 0: col = WHITE

        # body
        pygame.draw.ellipse(surf, col,
            (rx - self.w//2, ry - self.h, self.w, self.h))

        # eyes
        ex = rx + (6 if self.dir > 0 else -6)
        pygame.draw.circle(surf, WHITE, (ex, ry - self.h + 8), 5)
        pygame.draw.circle(surf, BLACK, (ex + self.dir*2, ry - self.h + 8), 3)

        # spiky crown
        if self.stomp_immune:
            for i in range(5):
                ang = math.radians(i * 72 + self.angle)
                sx = rx + math.cos(ang) * 14
                sy = ry - self.h//2 + math.sin(ang) * 14
                pygame.draw.circle(surf, ORANGE, (int(sx), int(sy)), 4)

        # wings for flyer
        if self.kind == 'flyer':
            wa = math.sin(pygame.time.get_ticks() * 0.1) * 20
            for side in [-1, 1]:
                pts = [
                    (rx, ry - self.h + 10),
                    (rx + side*28, ry - self.h - 10 + wa//3),
                    (rx + side*20, ry - self.h + 18),
                ]
                pygame.draw.polygon(surf, (200, 100, 240), pts)

# ─────────────────────────────────────────────
#  MOVING PLATFORM (checkpoint / door)
# ─────────────────────────────────────────────
class Flag:
    def __init__(self, x, y):
        self.x = x; self.y = y
        self.reached = False
        self.angle = 0

    def draw(self, surf, ox):
        rx = self.x - ox
        pygame.draw.line(surf, WHITE, (rx, self.y), (rx, self.y - 60), 3)
        col = YELLOW if not self.reached else GREEN
        pts = [(rx, self.y-60), (rx+28, self.y-50), (rx, self.y-40)]
        pygame.draw.polygon(surf, col, pts)
        if self.reached:
            text(surf, "✓", font_small, GREEN, rx, self.y - 75, shadow=True)

# ─────────────────────────────────────────────
#  PLAYER
# ─────────────────────────────────────────────
class Player:
    W, H = 28, 38

    def __init__(self, x, y):
        self.x = float(x); self.y = float(y)
        self.vx = 0.0; self.vy = 0.0
        self.on_ground = False
        self.jumps_left = 2          # double jump
        self.alive = True
        self.hp = 3
        self.invincible = 0
        self.coins = 0
        self.score = 0
        self.shadow_mode = False     # power-up: dash through enemies
        self.shadow_timer = 0
        self.dash_cd = 0
        self.dash_active = False
        self.dash_timer = 0
        self.facing = 1
        self.anim_frame = 0
        self.anim_t = 0
        self.wall_slide = False
        self.coyote = 0              # coyote time frames
        self.jump_buffer = 0         # jump buffer frames
        self.ice_friction = False

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def handle_input(self, keys):
        speed = 5.5 if not self.ice_friction else 3.0
        accel = 1.2 if not self.ice_friction else 0.4

        # horizontal movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx -= accel
            self.facing = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx += accel
            self.facing = 1
        else:
            # friction
            self.vx *= (0.75 if not self.ice_friction else 0.97)

        self.vx = max(-speed, min(speed, self.vx))

        # dash
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_x]) and self.dash_cd <= 0:
            self.dash_active = True
            self.dash_timer = 10
            self.dash_cd = 40
            self.shadow_mode = True
            self.shadow_timer = 12
            spawn_particles(self.x + self.W//2, self.y + self.H//2,
                            PLAYER_S, n=10, vy=-1)

    def jump(self):
        if self.coyote > 0 or self.jumps_left > 0:
            self.vy = -14 if self.jumps_left == 2 else -11
            if self.coyote <= 0:
                self.jumps_left -= 1
            else:
                self.jumps_left = max(0, self.jumps_left - 1)
            self.coyote = 0
            self.on_ground = False
            spawn_particles(self.x + self.W//2, self.y + self.H,
                            PLAYER_C, n=12, vy=1)
            return True
        return False

    def update(self, platforms, enemies, coins, flags):
        if not self.alive: return

        # timers
        if self.invincible > 0: self.invincible -= 1
        if self.dash_cd    > 0: self.dash_cd    -= 1
        if self.shadow_timer > 0:
            self.shadow_timer -= 1
        else:
            self.shadow_mode = False

        if self.coyote > 0: self.coyote -= 1
        if self.jump_buffer > 0: self.jump_buffer -= 1

        # dash override
        if self.dash_active:
            self.vx = self.facing * 18
            self.vy = 0
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dash_active = False
                self.vx = self.facing * 6

        # gravity
        if not self.dash_active:
            self.vy += 0.65
            self.vy = min(self.vy, 18)

        self.ice_friction = False

        # horizontal move + collision
        self.x += self.vx
        self._collide_h(platforms)

        # vertical move + collision
        was_on_ground = self.on_ground
        self.on_ground = False
        self.y += self.vy
        self._collide_v(platforms)

        if self.on_ground and not was_on_ground:
            # land dust
            spawn_particles(self.x + self.W//2, self.y + self.H,
                            (200,200,200), n=6, vy=1)

        if was_on_ground and not self.on_ground:
            self.coyote = 8          # coyote time

        if self.on_ground:
            self.jumps_left = 2
            self.coyote = 0

        # jump buffer
        if self.jump_buffer > 0 and self.on_ground:
            self.jump()

        # coins
        for c in coins:
            if not c.collected and self.rect.colliderect(
                    pygame.Rect(c.x-10, c.y-10, 20, 20)):
                c.collected = True
                val = 5 if c.kind == 'gem' else 1
                self.coins += val
                self.score += val * 10
                spawn_particles(c.x, c.y,
                    CYAN if c.kind=='gem' else COIN_C, n=12)

        # flags
        for f in flags:
            if not f.reached and self.rect.colliderect(
                    pygame.Rect(f.x-10, f.y-60, 40, 60)):
                f.reached = True
                self.score += 100
                spawn_particles(f.x, f.y - 30, YELLOW, n=20)

        # enemies
        for e in enemies:
            if not e.alive: continue
            if self.rect.colliderect(e.rect):
                if self.shadow_mode:
                    e.alive = False
                    self.score += 50
                    spawn_particles(e.x, e.y - 15, ENEMY_C, n=16)
                elif (self.vy > 2 and self.rect.bottom < e.rect.centery + 10
                      and not e.stomp_immune):
                    # stomp
                    e.alive = False
                    self.score += 50
                    self.vy = -10
                    spawn_particles(e.x, e.y - 15, ENEMY_C, n=16)
                    spawn_particles(e.x, e.y - 15, ORANGE, n=8)
                else:
                    self._take_damage()

        # death pit
        if self.y > 800:
            self.alive = False

        # animation
        self.anim_t += 1
        if abs(self.vx) > 0.5 and self.on_ground:
            self.anim_frame = (self.anim_t // 6) % 4
        else:
            self.anim_frame = 0

    def _take_damage(self):
        if self.invincible > 0: return
        self.hp -= 1
        self.invincible = 90
        self.vy = -8
        self.vx = -self.facing * 5
        spawn_particles(self.x + self.W//2, self.y + self.H//2,
                        RED, n=14, vy=-3)
        if self.hp <= 0:
            self.alive = False

    def _collide_h(self, platforms):
        pr = self.rect
        for p in platforms:
            if p.dead: continue
            if pr.colliderect(p.rect):
                if self.vx > 0:
                    self.x = p.rect.left - self.W
                elif self.vx < 0:
                    self.x = p.rect.right
                self.vx = 0

    def _collide_v(self, platforms):
        pr = self.rect
        for p in platforms:
            if p.dead: continue
            if pr.colliderect(p.rect):
                if p.kind == 'spike':
                    self._take_damage()
                    continue
                if self.vy > 0 and pr.bottom - self.vy <= p.rect.top + 6:
                    self.y = p.rect.top - self.H
                    self.vy = 0
                    self.on_ground = True
                    if p.kind == 'crumble' and not p.crumbling:
                        p.crumbling = True
                    if p.kind == 'ice':
                        self.ice_friction = True
                    # ride moving platform
                    if p.kind == 'moving':
                        self.x += p.move_speed * p.move_dir
                elif self.vy < 0:
                    self.y = p.rect.bottom
                    self.vy = 0

    def draw(self, surf, ox):
        if not self.alive: return
        if self.invincible > 0 and (self.invincible // 5) % 2:
            return

        rx = int(self.x - ox)
        ry = int(self.y)
        col = PLAYER_S if self.shadow_mode else PLAYER_C

        # legs animation
        leg_off = [0,4,0,-4][self.anim_frame]
        # back leg
        pygame.draw.rect(surf, tuple(max(0,c-40) for c in col),
            (rx + 6 - leg_off, ry + 24, 8, 14), border_radius=3)
        # front leg
        pygame.draw.rect(surf, tuple(max(0,c-20) for c in col),
            (rx + 14 + leg_off, ry + 24, 8, 14), border_radius=3)

        # body
        draw_rounded_rect(surf, col, (rx, ry, self.W, 26), 6)

        # head
        draw_rounded_rect(surf, col, (rx + 2, ry - 14, 24, 20), 6)

        # visor / eyes
        eye_x = rx + (16 if self.facing > 0 else 4)
        pygame.draw.ellipse(surf, (20,200,255), (eye_x, ry - 12, 10, 8))
        pygame.draw.circle(surf, WHITE, (eye_x+4, ry-9), 3)

        # scarf
        pygame.draw.rect(surf, ORANGE, (rx, ry + 6, self.W, 6), border_radius=3)

        # shadow trail
        if self.shadow_mode or self.dash_active:
            for i in range(1, 4):
                tx = rx - self.facing * i * 10
                s = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
                s.fill((*PLAYER_S[:3], 60 - i*15))
                surf.blit(s, (tx, ry))

# ─────────────────────────────────────────────
#  LEVEL DATA
# ─────────────────────────────────────────────
def make_level(n):
    """Return (platforms, enemies, coins, flags, spawn, level_w, bg_color)"""
    if n == 1:
        return _level1()
    elif n == 2:
        return _level2()
    elif n == 3:
        return _level3()
    else:
        return _level1()

def _level1():
    level_w = 3600
    platforms = [
        # ground sections
        Platform(0,   540, 500),
        Platform(550, 540, 300),
        Platform(900, 540, 250),
        # floating platforms
        Platform(400, 440, 120),
        Platform(600, 380, 100),
        Platform(760, 440, 120),
        Platform(980, 350, 130),
        Platform(1150,460, 100),
        Platform(1300,540, 400),
        Platform(1750,540, 200),
        Platform(1700,420, 150, kind='wood'),
        Platform(1500,340, 100, kind='wood'),
        Platform(1900,540, 300),
        Platform(2000,420, 100, kind='moving', move_range=120, move_speed=2),
        Platform(2250,340, 110),
        Platform(2400,540, 400),
        Platform(2450,430, 100, kind='crumble'),
        Platform(2600,360, 90,  kind='crumble'),
        Platform(2800,540, 800),
        # spikes
        Platform(870,  530, 20,  8, kind='spike'),
        Platform(1260, 530, 20,  8, kind='spike'),
    ]
    enemies = [
        Enemy(700,  540, 'walker', 80),
        Enemy(1050, 350, 'walker', 60),
        Enemy(1600, 540, 'walker', 100),
        Enemy(2100, 540, 'walker', 60),
        Enemy(1800, 300, 'flyer',  80),
        Enemy(2600, 540, 'spiky',  120),
    ]
    coins = (
        [Coin(c, 510) for c in range(100, 450, 80)] +
        [Coin(650, 340), Coin(820, 400), Coin(1010, 310)] +
        [Coin(c, 370)  for c in range(1350, 1650, 80)] +
        [Coin(2050, 380), Coin(2280, 300)] +
        [Coin(c, 510)  for c in range(2450, 2780, 80)] +
        [Coin(2900, 400, 'gem'), Coin(3200, 400, 'gem')]
    )
    flags = [Flag(3450, 540)]
    return platforms, enemies, coins, flags, (80, 490), level_w, SKY

def _level2():
    level_w = 4000
    platforms = [
        Platform(0,   560, 400),
        Platform(450, 480, 80,  kind='ice'),
        Platform(580, 420, 80,  kind='ice'),
        Platform(710, 360, 80,  kind='ice'),
        Platform(840, 300, 80,  kind='ice'),
        Platform(970, 420, 100),
        Platform(1100,360, 100, kind='moving', move_range=100, move_speed=2.5),
        Platform(1300,280, 100, kind='crumble'),
        Platform(1450,380, 80,  kind='crumble'),
        Platform(1600,460, 80,  kind='crumble'),
        Platform(1750,560, 300),
        Platform(2100,560, 200),
        Platform(2000,420, 80,  kind='wood'),
        Platform(2200,340, 80,  kind='wood'),
        Platform(2350,260, 80,  kind='wood'),
        Platform(2500,340, 80,  kind='moving', move_range=140, move_speed=3),
        Platform(2700,560, 400),
        Platform(2750,440, 100, kind='spike'),
        Platform(3000,560, 200),
        Platform(3100,420, 100),
        Platform(3250,340, 100, kind='moving', move_range=100, move_speed=2),
        Platform(3400,260, 100),
        Platform(3600,560, 400),
        # spikes ground
        Platform(430,  550, 15, 8, kind='spike'),
        Platform(1720, 550, 15, 8, kind='spike'),
        Platform(2680, 550, 15, 8, kind='spike'),
    ]
    enemies = [
        Enemy(200,  560, 'walker', 80),
        Enemy(1000, 420, 'walker', 80),
        Enemy(1800, 560, 'spiky',  100),
        Enemy(2150, 560, 'walker', 80),
        Enemy(1700, 250, 'flyer',  120),
        Enemy(2900, 560, 'spiky',  80),
        Enemy(3200, 340, 'walker', 60),
        Enemy(3500, 200, 'flyer',  100),
    ]
    coins = (
        [Coin(c, 530) for c in range(50, 380, 70)] +
        [Coin(x, y) for x,y in [(480,450),(610,390),(740,330),(870,270)]] +
        [Coin(c, 250) for c in range(1100, 1600, 90)] +
        [Coin(c, 530) for c in range(1800, 2080, 70)] +
        [Coin(x, y) for x,y in [(2050,390),(2250,310),(2400,230)]] +
        [Coin(c, 530) for c in range(2750, 2970, 70)] +
        [Coin(c, 390) for c in range(3100, 3580, 80)] +
        [Coin(3700, 400, 'gem'), Coin(3800, 400, 'gem'), Coin(3900, 400, 'gem')]
    )
    flags = [Flag(3900, 560)]
    return platforms, enemies, coins, flags, (60, 510), level_w, (15, 15, 50)

def _level3():
    """Boss level – tighter, more dangerous"""
    level_w = 4400
    platforms = [
        Platform(0,   560, 300),
        Platform(350, 480, 60,  kind='crumble'),
        Platform(450, 400, 60,  kind='crumble'),
        Platform(550, 320, 60,  kind='crumble'),
        Platform(650, 400, 60,  kind='moving', move_range=80, move_speed=3),
        Platform(800, 480, 60,  kind='moving', move_range=80, move_speed=2.5),
        Platform(950, 400, 80),
        Platform(1100,320, 80,  kind='ice'),
        Platform(1250,240, 80,  kind='ice'),
        Platform(1400,320, 80,  kind='ice'),
        Platform(1550,400, 80,  kind='moving', move_range=120, move_speed=3.5),
        Platform(1750,480, 60,  kind='crumble'),
        Platform(1850,400, 60,  kind='crumble'),
        Platform(1950,320, 60,  kind='crumble'),
        Platform(2100,560, 250),
        Platform(2120,440, 60,  kind='spike'),
        Platform(2300,380, 80,  kind='moving', move_range=100, move_speed=4),
        Platform(2500,300, 80),
        Platform(2650,220, 80,  kind='wood'),
        Platform(2800,300, 80,  kind='moving', move_range=120, move_speed=3),
        Platform(2980,380, 80),
        Platform(3100,460, 80,  kind='crumble'),
        Platform(3200,380, 80,  kind='crumble'),
        Platform(3350,560, 250),
        Platform(3400,440, 60,  kind='spike'),
        Platform(3650,480, 80,  kind='moving', move_range=100, move_speed=4),
        Platform(3800,400, 80),
        Platform(3950,480, 80,  kind='moving', move_range=80, move_speed=3.5),
        Platform(4100,560, 300),
    ]
    enemies = [
        Enemy(150,  560, 'walker', 60),
        Enemy(970,  400, 'spiky',  60),
        Enemy(1280, 240, 'walker', 50),
        Enemy(1600, 300, 'flyer',  80),
        Enemy(2160, 560, 'spiky',  60),
        Enemy(2520, 300, 'walker', 50),
        Enemy(2700, 150, 'flyer',  80),
        Enemy(3010, 380, 'spiky',  60),
        Enemy(3380, 560, 'spiky',  60),
        Enemy(3820, 400, 'flyer',  80),
        Enemy(4150, 560, 'walker', 60),
        Enemy(4200, 560, 'spiky',  60),
    ]
    coins = (
        [Coin(c, 530) for c in range(50, 290, 70)] +
        [Coin(x, y) for x,y in [(370,450),(470,370),(570,290)]] +
        [Coin(c, 290) for c in range(960, 1550, 100)] +
        [Coin(c, 530) for c in range(2150, 2350, 70)] +
        [Coin(x, y) for x,y in [(2520,270),(2670,190),(2820,270)]] +
        [Coin(c, 430) for c in range(3110, 3330, 80)] +
        [Coin(c, 530) for c in range(3400, 4080, 100)] +
        [Coin(4150, 300, 'gem'), Coin(4200, 300, 'gem'),
         Coin(4250, 300, 'gem'), Coin(4300, 300, 'gem')]
    )
    flags = [Flag(4350, 560)]
    return platforms, enemies, coins, flags, (60, 510), level_w, (10, 10, 30)

# ─────────────────────────────────────────────
#  BACKGROUND STARS
# ─────────────────────────────────────────────
stars = [(random.randint(0,W), random.randint(0,H//2),
          random.uniform(0.5, 2.0)) for _ in range(120)]

def draw_bg(surf, t, bg_col):
    surf.fill(bg_col)
    # gradient sky
    for i in range(H//2):
        ratio = i / (H//2)
        c = tuple(int(bg_col[j] + (SKY2[j] - bg_col[j]) * ratio) for j in range(3))
        pygame.draw.line(surf, c, (0,i), (W,i))
    # stars
    for sx, sy, sz in stars:
        b = int(100 + 80 * math.sin(t * 0.03 + sx))
        pygame.draw.circle(surf, (b,b,b), (sx, sy), int(sz))

def draw_hills(surf, cam_ox, bg_col):
    """Parallax hills"""
    for layer, (amp, freq, speed, alpha) in enumerate([
        (60,  0.003, 0.3,  60),
        (100, 0.002, 0.15, 40),
        (130, 0.0015,0.08, 25),
    ]):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        ox2 = cam_ox * speed
        pts = [(0, H)]
        for xi in range(W+1):
            hx = xi + ox2
            hy = H - 200 + layer*30 - amp * math.sin(hx * freq + layer)
            pts.append((xi, int(hy)))
        pts.append((W, H))
        col = tuple(min(255, bg_col[j] + 20 + layer*15) for j in range(3))
        pygame.draw.polygon(s, (*col, alpha), pts)
        surf.blit(s, (0,0))

# ─────────────────────────────────────────────
#  HUD
# ─────────────────────────────────────────────
def draw_hud(surf, player, level_num, total_coins, t):
    # semi-transparent bar
    hud = pygame.Surface((W, 52), pygame.SRCALPHA)
    hud.fill((0,0,0,140))
    surf.blit(hud, (0,0))

    # HP hearts
    for i in range(3):
        col = RED if i < player.hp else (60,60,60)
        pygame.draw.polygon(surf, col, [
            (20 + i*35 + 13, 16),
            (20 + i*35,       8),
            (20 + i*35 - 8,  16),
            (20 + i*35,      28),
        ])
        if i < player.hp:
            pygame.draw.polygon(surf, (255,150,150), [
                (20 + i*35 + 4,  14),
                (20 + i*35,       9),
                (20 + i*35 - 4,  14),
            ])

    # coins
    pygame.draw.circle(surf, COIN_C, (140, 22), 9)
    text(surf, f"× {player.coins}", font_small, YELLOW, 175, 22, shadow=True)

    # score
    text(surf, f"SCORE  {player.score:06d}", font_small, WHITE, W//2, 22)

    # level
    text(surf, f"LEVEL {level_num}/3", font_small, CYAN, W - 100, 22)

    # dash indicator
    if player.dash_cd > 0:
        pct = 1 - player.dash_cd / 40
        pygame.draw.rect(surf, (60,60,60),   (20, 42, 100, 6), border_radius=3)
        pygame.draw.rect(surf, PURPLE, (20, 42, int(100*pct), 6), border_radius=3)
    else:
        text(surf, "DASH READY", font_tiny, PURPLE, 70, 45)

    # shadow mode banner
    if player.shadow_mode:
        banner = pygame.Surface((220, 28), pygame.SRCALPHA)
        banner.fill((80,20,180,160))
        surf.blit(banner, (W//2 - 110, 54))
        text(surf, "⚡ SHADOW MODE ⚡", font_tiny, (200,150,255), W//2, 68)

# ─────────────────────────────────────────────
#  SCREENS
# ─────────────────────────────────────────────
def screen_title():
    t = 0
    while True:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        draw_bg(screen, t, SKY)
        draw_hills(screen, 0, SKY)

        # title box
        box = pygame.Surface((560, 200), pygame.SRCALPHA)
        box.fill((0,0,0,160))
        screen.blit(box, (W//2-280, H//2-120))

        pulse = abs(math.sin(t * 0.04))
        col = (int(80+175*pulse), int(100+155*pulse), 255)
        text(screen, "⚡ SHADOW RUNNER", font_big, col, W//2, H//2 - 60)
        text(screen, "A 2D PLATFORMER", font_med,  CYAN,  W//2, H//2)

        blink = (255,255,255) if (t//20)%2 else (120,120,120)
        text(screen, "PRESS ENTER TO START", font_small, blink, W//2, H//2 + 60)

        # controls
        ctrl_lines = [
            ("← → / A D", "Move"),
            ("↑ / W / SPACE", "Jump  (double jump!)"),
            ("SHIFT / X", "Dash through enemies"),
            ("↓ STOMP", "Jump on enemies to kill"),
        ]
        for i,(k,v) in enumerate(ctrl_lines):
            text(screen, f"{k}  →  {v}", font_tiny, (180,200,180),
                 W//2, H//2 + 100 + i*22)

        # animated coins
        for i in range(6):
            ang = t * 0.04 + i * math.pi/3
            cx = int(W//2 + math.cos(ang)*220)
            cy = int(H//2 - 80 + math.sin(ang*2)*30)
            pygame.draw.circle(screen, COIN_C, (cx,cy), 7)

        pygame.display.flip()
        t += 1

def screen_game_over(score):
    t = 0
    while True:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_r):
                    return 'retry'
                if ev.key == pygame.K_ESCAPE:
                    return 'menu'

        draw_bg(screen, t, (30, 5, 5))
        box = pygame.Surface((440, 220), pygame.SRCALPHA)
        box.fill((0,0,0,180))
        screen.blit(box, (W//2-220, H//2-120))

        pulse = abs(math.sin(t*0.05))
        text(screen, "GAME OVER", font_big,
             (255, int(50+100*pulse), int(50+100*pulse)), W//2, H//2-70)
        text(screen, f"SCORE  {score:06d}", font_med, YELLOW, W//2, H//2-10)
        text(screen, "R / ENTER  →  Retry", font_small, WHITE,   W//2, H//2+50)
        text(screen, "ESC        →  Menu",  font_small, (160,160,160), W//2, H//2+80)

        pygame.display.flip()
        t += 1

def screen_level_clear(level_num, score, coins):
    t = 0
    while True:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return

        draw_bg(screen, t, (5, 30, 5))
        # fireworks
        if t % 8 == 0:
            fx = random.randint(100, W-100)
            fy = random.randint(50, 300)
            col = random.choice([RED,GREEN,YELLOW,CYAN,PURPLE,ORANGE])
            for _ in range(20):
                a = random.uniform(0, math.pi*2)
                sp = random.uniform(2,7)
                particles.append(Particle(fx, fy, col,
                    vx=math.cos(a)*sp, vy=math.sin(a)*sp, life=40))

        for p in particles[:]:
            p.update()
            p.draw(screen, 0)
            if p.life <= 0:
                particles.remove(p)

        box = pygame.Surface((480, 230), pygame.SRCALPHA)
        box.fill((0,0,0,180))
        screen.blit(box, (W//2-240, H//2-120))

        text(screen, f"LEVEL {level_num} CLEAR!", font_big, GREEN, W//2, H//2-70)
        text(screen, f"SCORE  {score:06d}", font_med, YELLOW, W//2, H//2-10)
        text(screen, f"COINS  {coins}", font_med, COIN_C, W//2, H//2+40)
        blink = WHITE if (t//20)%2 else (120,120,120)
        text(screen, "PRESS ENTER / SPACE", font_small, blink, W//2, H//2+90)

        pygame.display.flip()
        t += 1

def screen_win(score, coins):
    t = 0
    while True:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return 'menu'
                if ev.key == pygame.K_ESCAPE:
                    return 'menu'

        screen.fill(BLACK)
        if t % 5 == 0:
            for _ in range(3):
                fx = random.randint(0, W)
                fy = random.randint(0, H//2)
                col = random.choice([RED,GREEN,YELLOW,CYAN,PURPLE,ORANGE,WHITE])
                for _ in range(30):
                    a = random.uniform(0, math.pi*2)
                    sp = random.uniform(3,9)
                    particles.append(Particle(fx, fy, col,
                        vx=math.cos(a)*sp, vy=math.sin(a)*sp, life=50, size=5))

        for p in particles[:]:
            p.update()
            p.draw(screen, 0)
            if p.life <= 0:
                particles.remove(p)

        pulse = abs(math.sin(t*0.05))
        col = (int(255*pulse), int(200*pulse), int(50 + 200*pulse))
        text(screen, "🏆  YOU WIN!  🏆",    font_big, col, W//2, H//2 - 100)
        text(screen, "All 3 levels cleared!", font_med, WHITE, W//2, H//2 - 40)
        text(screen, f"FINAL SCORE  {score:06d}", font_med, YELLOW, W//2, H//2 + 20)
        text(screen, f"TOTAL COINS  {coins}", font_med, COIN_C, W//2, H//2 + 70)
        blink = WHITE if (t//25)%2 else (80,80,80)
        text(screen, "PRESS ENTER TO RETURN TO MENU", font_small, blink, W//2, H//2+120)

        pygame.display.flip()
        t += 1

# ─────────────────────────────────────────────
#  MAIN GAME LOOP (one level)
# ─────────────────────────────────────────────
def run_level(level_num, carry_score=0, carry_coins=0):
    platforms, enemies, coins, flags, spawn, level_w, bg_col = make_level(level_num)
    player = Player(*spawn)
    player.score = carry_score
    player.coins = carry_coins
    camera = Camera()
    t = 0
    particles.clear()

    while True:
        dt = clock.tick(FPS)
        t += 1

        # ── EVENTS ──────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return 'menu', player.score, player.coins
                if ev.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
                    if not player.jump():
                        player.jump_buffer = 10
                if ev.key == pygame.K_p:
                    paused = True
                    while paused:
                        for e2 in pygame.event.get():
                            if e2.type == pygame.QUIT:
                                pygame.quit(); sys.exit()
                            if e2.type == pygame.KEYDOWN and e2.key == pygame.K_p:
                                paused = False
                        text(screen, "PAUSED", font_big, WHITE, W//2, H//2)
                        pygame.display.flip()
                        clock.tick(30)

        keys = pygame.key.get_pressed()
        if player.alive:
            player.handle_input(keys)

        # ── UPDATE ──────────────────────────────
        for p in platforms:
            p.update()
        for e in enemies:
            e.update(platforms)
        for c in coins:
            c.update()

        if player.alive:
            player.update(platforms, enemies, coins, flags)

        camera.update(player.x + player.W//2, level_w)

        # particles
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

        # ── CHECK WIN / LOSE ────────────────────
        if not player.alive:
            pygame.time.delay(400)
            result = screen_game_over(player.score)
            if result == 'retry':
                return 'retry', 0, 0
            else:
                return 'menu', 0, 0

        if flags and flags[-1].reached:
            player.score += player.coins * 5
            screen_level_clear(level_num, player.score, player.coins)
            return 'next', player.score, player.coins

        # ── DRAW ────────────────────────────────
        draw_bg(screen, t, bg_col)
        draw_hills(screen, camera.ox, bg_col)

        ox = camera.ox

        # platforms
        for p in platforms:
            if -200 < p.rect.x - ox < W + 200:
                p.draw(screen, ox)

        # coins
        for c in coins:
            if -50 < c.x - ox < W + 50:
                c.draw(screen, ox)

        # flags
        for f in flags:
            f.draw(screen, ox)

        # enemies
        for e in enemies:
            if -100 < e.x - ox < W + 100:
                e.draw(screen, ox)

        # particles
        for p in particles:
            p.draw(screen, ox)

        # player
        player.draw(screen, ox)

        # HUD
        draw_hud(screen, player, level_num, len([c for c in coins if not c.collected]), t)

        # mini-map
        map_w, map_h = 160, 8
        mx, my = W//2 - map_w//2, H - 16
        pygame.draw.rect(screen, (60,60,60), (mx-1, my-1, map_w+2, map_h+2))
        pygame.draw.rect(screen, (40,40,80), (mx, my, map_w, map_h))
        # player dot
        px_map = int((player.x / level_w) * map_w)
        pygame.draw.rect(screen, PLAYER_C, (mx+px_map-1, my, 4, map_h))
        # enemy dots
        for e in enemies:
            if e.alive:
                ex_map = int((e.x / level_w) * map_w)
                pygame.draw.rect(screen, RED, (mx+ex_map, my+2, 3, map_h-4))
        # flag dot
        for f in flags:
            fx_map = int((f.x / level_w) * map_w)
            pygame.draw.rect(screen, YELLOW, (mx+fx_map, my, 3, map_h))

        pygame.display.flip()

# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def main():
    while True:
        screen_title()

        score, coins = 0, 0
        level = 1
        while level <= 3:
            result, score, coins = run_level(level, score, coins)
            if result == 'next':
                level += 1
            elif result == 'retry':
                score, coins = 0, 0
                # restart from level 1
                level = 1
            else:   # 'menu'
                break
        else:
            # Won all 3 levels
            r = screen_win(score, coins)

if __name__ == '__main__':
    main()