# -*- coding: utf-8 -*-
import sys, os, random, pygame, math
from pygame.locals import *
from MyLibrary import *

IMG_PATH = os.path.join("src", "images")
SND_PATH = os.path.join("src", "sounds")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "data.txt")

LEVEL_CONFIG = {
    1: {"ground_speed": 5, "arrow_speed": 8, "fruit_min": 6000, "fruit_max": 9000, "target_score": 20},
    2: {"ground_speed": 6, "arrow_speed": 9, "fruit_min": 5000, "fruit_max": 8000, "target_score": 30},
    3: {"ground_speed": 7, "arrow_speed": 10, "fruit_min": 4000, "fruit_max": 7000, "target_score": 40},
    4: {"ground_speed": 8, "arrow_speed": 11, "fruit_min": 3500, "fruit_max": 6000, "target_score": 50},
    5: {"ground_speed": 9, "arrow_speed": 12, "fruit_min": 3000, "fruit_max": 5500, "target_score": 60},
}

def safe_load_image(filename):
    path = os.path.join(IMG_PATH, filename)
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception as e:
        print(f"图片加载失败：{path}")
        sys.exit()

def safe_load_sound(filename):
    path = os.path.join(SND_PATH, filename)
    try:
        return pygame.mixer.Sound(path)
    except Exception:
        return None

class Music:
    def __init__(self, sound):
        self.sound = sound
        self._channel = None

    def play(self, vol=0.5, loop=False):
        if not self.sound:
            return

        if loop:
            if self._channel is not None and self._channel.get_busy():
                try:
                    self._channel.set_volume(vol)
                except Exception:
                    pass
                return
            ch = pygame.mixer.find_channel(True)
            if ch:
                self._channel = ch
                self._channel.set_volume(vol)
                self._channel.play(self.sound, loops=-1)
        else:
            ch = pygame.mixer.find_channel(True)
            if ch:
                ch.set_volume(vol)
                ch.play(self.sound)

def load_progress():
    if not os.path.exists(DATA_FILE):
        return {"max_level": 1, "best_score": 0}
    try:
        with open(DATA_FILE, "r") as f:
            lines = f.readlines()
            max_level = int(lines[0].strip()) if len(lines) > 0 else 1
            best_score = int(lines[1].strip()) if len(lines) > 1 else 0
            return {"max_level": max(1, min(5, max_level)), "best_score": max(0, best_score)}
    except Exception:
        return {"max_level": 1, "best_score": 0}

def save_progress(max_level, best_score):
    try:
        with open(DATA_FILE, "w") as f:
            f.write(f"{int(max_level)}\n{int(best_score)}")
            f.flush()
    except Exception:
        pass

class MyMap:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.bg = safe_load_image("background.png")
        self.width = self.bg.get_width()

    def move(self, speed):
        self.x -= speed
        if self.x <= -self.width:
            self.x += self.width * 2

    def draw(self, surface):
        surface.blit(self.bg, (self.x, self.y))
        surface.blit(self.bg, (self.x + self.width, self.y))

class Button:
    def __init__(self, up, down, pos):
        self.image_up = safe_load_image(up)
        self.image_down = safe_load_image(down)
        self.pos = pos
        self.clicked = False
        
    def is_over(self):
        mx, my = pygame.mouse.get_pos()
        x, y = self.pos
        w, h = self.image_up.get_size()
        return x - w/2 < mx < x + w/2 and y - h/2 < my < y + h/2
        
    def draw(self, surface):
        img = self.image_down if self.is_over() else self.image_up
        w, h = img.get_size()
        surface.blit(img, (self.pos[0]-w/2, self.pos[1]-h/2))
        
    def handle_event(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.is_over():
                self.clicked = True
                return True
        return False

class LevelButton:
    def __init__(self, level, pos, get_max_level_func):
        self.level = int(level)
        self.pos = pos
        self.get_max_level_func = get_max_level_func
        self.img_unlocked = safe_load_image("level_unlocked.png")
        self.img_locked = safe_load_image("level_locked.png")

    def is_unlocked(self):
        try:
            maxlvl = int(self.get_max_level_func())
        except Exception:
            maxlvl = 1
        return self.level <= maxlvl

    def draw(self, surface, font):
        unlocked = self.is_unlocked()
        img = self.img_unlocked if unlocked else self.img_locked
        w, h = img.get_size()
        surface.blit(img, (self.pos[0]-w/2, self.pos[1]-h/2))

        color = (0, 204, 0) if unlocked else (255, 0, 0)
        txt = font.render(str(self.level), True, color)
        txt_rect = txt.get_rect(center=(self.pos[0], self.pos[1] - h/2 - 15))
        surface.blit(txt, txt_rect)

    def handle_event(self, events):
        if not self.is_unlocked():
            return False
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = pygame.mouse.get_pos()
                x, y = self.pos
                w, h = self.img_unlocked.get_size()
                if x - w/2 < mx < x + w/2 and y - h/2 < my < y + h/2:
                    return True
        return False

class Fruit(MySprite):
    def __init__(self):
        super().__init__()
        self.load(os.path.join(IMG_PATH, "fruit.png"), 40, 40, 3)
        self.reset()
        
    def reset(self):
        self.frame = random.randint(0, self.columns - 1)
        self.old_frame = self.frame
        start_x = 820
        start_y = random.randint(240, 300)
        self.spawn_time = pygame.time.get_ticks()
        frame_x = (self.frame % self.columns) * self.frame_width
        frame_y = (self.frame // self.columns) * self.frame_height
        rect = Rect(frame_x, frame_y, self.frame_width, self.frame_height)
        self.image = self.master_image.subsurface(rect).copy()
        self.rect = self.image.get_rect()
        self.rect.topleft = (start_x, start_y)
        
    def move(self, speed):
        self.rect.x -= speed
        self.rect.y += math.sin(pygame.time.get_ticks() / 250 + self.rect.x * 0.05) * 0.3
        if self.rect.x < -50 or pygame.time.get_ticks() - self.spawn_time > 12000:
            self.kill()
            
    def update(self, ticks): 
        pass

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((800,600))
        pygame.display.set_caption("勇者快跑")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 48)

        self.snd_hit = safe_load_sound("exlposion.wav")
        self.snd_btn = safe_load_sound("button.wav")
        self.snd_bg = safe_load_sound("background.ogg")
        self.snd_bullet = safe_load_sound("bullet.wav")
        self.snd_fruit = safe_load_sound("fruit.ogg")

        self.bg_music = Music(self.snd_bg)
        self.hit_music = Music(self.snd_hit)
        self.btn_music = Music(self.snd_btn)
        self.bullet_music = Music(self.snd_bullet)
        self.fruit_music = Music(self.snd_fruit)

        self.bg1 = MyMap(0, 0)
        self.bg2 = MyMap(self.bg1.width, 0)

        self.interface = safe_load_image("interface.png")
        self.level_bg = safe_load_image("level_bg.png")
        
        self.button_start = Button("game_start_up.png", "game_start_down.png", (400, 450))
        self.button_select = Button("game_select_up.png", "game_select_down.png", (400, 520))

        self.state = "menu"
        self.current_level = 1
        self.score = 0
        
        progress = load_progress()
        self.max_unlocked_level = progress["max_level"]
        self.best = progress["best_score"]
        
        self.lives = 3
        self.invincible = 0

        self.level_buttons = []
        positions = [(250, 250), (400, 250), (550, 250), (325, 400), (475, 400)]
        for i in range(5):
            level = i + 1
            self.level_buttons.append(LevelButton(level, positions[i], lambda: self.max_unlocked_level))

        self.group = pygame.sprite.Group()
        self.group_exp = pygame.sprite.Group()
        self.fruit_group = pygame.sprite.Group()
        self.last_fruit_time = 0
        self.next_fruit_interval = 0

        self.dragon = MySprite()
        self.dragon.load(os.path.join(IMG_PATH, "dragon.png"), 260, 150, 3)
        self.dragon.position = (100, 270)

        self.player = MySprite()
        self.player.load(os.path.join(IMG_PATH, "sprite.png"), 100, 100, 4)
        self.player.position = (400, 310)

        self.arrow = MySprite()
        self.arrow.load(os.path.join(IMG_PATH, "flame.png"), 40, 16, 1)
        self.arrow.position = (800, 360)

        self.group.add(self.dragon)
        self.group.add(self.player)
        self.group.add(self.arrow)

        self.jump_vel = 0
        self.is_jumping = False

        self.reset_message_time = None
        self.last_reset_time = 0

    def get_current_config(self):
        return LEVEL_CONFIG[self.current_level]

    def reset_arrow(self):
        config = self.get_current_config()
        y = random.randint(310,390)
        self.arrow.position = (800, y)
        self.score += 1
        if self.score > self.best:
            self.best = self.score
        self.bullet_music.play()

    def start_level(self, level):
        self.current_level = level
        self.state = "playing"
        self.lives = 3
        self.score = 0
        self.invincible = 0
        self.is_jumping = False
        self.jump_vel = 0
        self.player.Y = 310
        self.arrow.X = 800
        self.group_exp.empty()
        self.fruit_group.empty()
        config = self.get_current_config()
        self.last_fruit_time = pygame.time.get_ticks()
        self.next_fruit_interval = random.randint(config["fruit_min"], config["fruit_max"])
        self.bg_music.play(loop=True)

    def run(self):
        self.bg_music.play(loop=True)
        while True:
            dt = self.clock.tick(60)
            events = pygame.event.get()

            for e in events:
                if e.type == QUIT:
                    pygame.quit(); sys.exit()
                if e.type == KEYDOWN and e.key == K_ESCAPE:
                    if self.state in ["level_select", "level_complete", "gameover"]:
                        self.state = "menu"
                    else:
                        pygame.quit(); sys.exit()

            if self.state == "menu":
                self.update_menu(events)
            elif self.state == "level_select":
                self.update_level_select(events)
            elif self.state == "playing":
                self.update_playing(events)
            elif self.state == "gameover":
                self.update_gameover(events)
            elif self.state == "level_complete":
                self.update_level_complete(events)

            pygame.display.update()

    def update_menu(self, events): 
        self.screen.blit(self.interface, (0, 0))
        self.button_start.draw(self.screen)
        self.button_select.draw(self.screen)

        if self.button_start.handle_event(events):
            self.btn_music.play()
            self.start_level(1)
        if self.button_select.handle_event(events):
            self.btn_music.play()
            self.state = "level_select"

        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
                now = pygame.time.get_ticks()
                if now - self.last_reset_time > 1000:
                    self.last_reset_time = now
                    self.btn_music.play()
                    save_progress(1, 0)
                    self.max_unlocked_level = 1
                    self.best = 0
                    self.reset_message_time = now

        hint_text = self.font.render("Press TAB to reset progress", True, (200, 200, 200))
        hint_rect = hint_text.get_rect(center=(400, 580))
        self.screen.blit(hint_text, hint_rect)

        if self.reset_message_time is not None:
            if pygame.time.get_ticks() - self.reset_message_time < 2000:
                msg = self.font.render("Progress reset successfully!", True, (255,100,100))
                msg_rect = msg.get_rect(center=(630, 580))
                self.screen.blit(msg, msg_rect)

    def update_level_select(self, events):
        self.screen.blit(self.level_bg, (0, 0))
        title = self.font_large.render("SELECT LEVEL", True, (255, 255, 255))
        title_rect = title.get_rect(center=(400, 80))
        self.screen.blit(title, title_rect)

        for btn in self.level_buttons:
            btn.draw(self.screen, self.font_large)
            if btn.handle_event(events):
                if btn.level <= int(self.max_unlocked_level):
                    self.btn_music.play()
                    self.start_level(btn.level)

        hint = self.font.render("Press ESC to return", True, (200, 200, 200))
        hint_rect = hint.get_rect(center=(400, 500))
        self.screen.blit(hint, hint_rect)

    def update_playing(self, events):
        config = self.get_current_config()
        keys = pygame.key.get_pressed()
        if keys[K_SPACE] and not self.is_jumping:
            self.is_jumping = True
            self.jump_vel = -12.0
            
        self.bg1.move(config["ground_speed"])
        self.bg2.move(config["ground_speed"])
        self.bg1.draw(self.screen)
        self.bg2.draw(self.screen)
        
        if self.is_jumping:
            if self.jump_vel < 0: self.jump_vel += 0.6
            else: self.jump_vel += 0.8
            self.player.Y += self.jump_vel
            if self.player.Y >= 310:
                self.player.Y = 310
                self.is_jumping = False
                
        self.arrow.X -= config["arrow_speed"]
        if self.arrow.X < -40:
            self.reset_arrow()
            
        current_time = pygame.time.get_ticks()
        self.group.update(current_time)
        self.group.draw(self.screen)
        self.group_exp.update(current_time)
        self.group_exp.draw(self.screen)

        if current_time - self.last_fruit_time > self.next_fruit_interval:
            fruit = Fruit()
            self.fruit_group.add(fruit)
            self.last_fruit_time = current_time
            self.next_fruit_interval = random.randint(config["fruit_min"], config["fruit_max"])
            
        for fruit in list(self.fruit_group):
            fruit.move(config["ground_speed"])
            fruit.update(current_time)
            self.screen.blit(fruit.image, fruit.rect.topleft)

        hit_fruit = pygame.sprite.spritecollideany(self.player, self.fruit_group)
        if hit_fruit:
            self.fruit_group.remove(hit_fruit)
            self.lives = min(self.lives + 1, 5)
            self.score += 3
            self.fruit_music.play()

        if self.invincible > 0:
            self.invincible -= self.clock.get_time()
            if int(current_time / 100) % 2 == 0:
                self.player.image.set_alpha(100)
            else:
                self.player.image.set_alpha(255)
        else:
            self.player.image.set_alpha(255)

        for exp in list(self.group_exp):
            if exp.frame >= exp.last_frame:
                self.group_exp.remove(exp)

        if pygame.sprite.collide_rect(self.arrow, self.player) and self.invincible <= 0:
            self.lives -= 1
            self.invincible = 1500
            exp = MySprite()
            exp.load(os.path.join(IMG_PATH, "explosion.png"), 128, 128, 6)
            exp.X = self.arrow.X - (exp.frame_width - self.arrow.frame_width) / 2
            exp.Y = self.arrow.Y - (exp.frame_height - self.arrow.frame_height) / 2
            self.group_exp.add(exp)
            self.hit_music.play()
            if self.lives <= 0:
                self.state = "gameover"
                save_progress(self.max_unlocked_level, self.best)

        if self.score >= config["target_score"]:
            self.state = "level_complete"
            if self.current_level >= self.max_unlocked_level and self.current_level < 5:
                self.max_unlocked_level = self.current_level + 1
            save_progress(self.max_unlocked_level, self.best)

        score_text = self.font.render(f"Score: {self.score}", True, (255,255,255))
        best_text = self.font.render(f"Best: {self.best}", True, (255,255,0))
        level_text = self.font.render(f"Level: {self.current_level}", True, (255,255,255))        
        lives_text = self.font.render(f"Lives: {self.lives}", True, (255,0,0))

        self.screen.blit(score_text, (10, 10))
        self.screen.blit(best_text,  (10, 34))        
        self.screen.blit(level_text, (680, 10))
        self.screen.blit(lives_text, (680, 34))

    def update_level_complete(self, events):
        self.screen.fill((30, 30, 30))
        title = self.font_large.render("LEVEL COMPLETE!", True, (0, 200, 0))
        title_rect = title.get_rect(center=(400, 180))
        self.screen.blit(title, title_rect)

        stats = self.font.render(f"Level {self.current_level} cleared. Score: {self.score}", True, (255,255,255))
        stats_rect = stats.get_rect(center=(400, 240))
        self.screen.blit(stats, stats_rect)

        hint1 = self.font.render("Press SPACE to continue", True, (200,200,200))
        hint1_rect = hint1.get_rect(center=(400, 320))
        self.screen.blit(hint1, hint1_rect)

        hint2 = self.font.render("Press ESC to menu", True, (200,200,200))
        hint2_rect = hint2.get_rect(center=(400, 360))
        self.screen.blit(hint2, hint2_rect)

        for e in events:
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    if self.current_level < 5:
                        self.start_level(self.current_level + 1)
                    else:
                        self.state = "level_select"
                elif e.key == K_ESCAPE:
                    self.state = "menu"
                    save_progress(self.max_unlocked_level, self.best)

    def update_gameover(self, events):
        self.screen.fill((0,0,0))
        go_text = self.font_large.render("GAME OVER", True, (220, 40, 40))
        go_rect = go_text.get_rect(center=(400, 180))
        self.screen.blit(go_text, go_rect)

        score_t = self.font.render(f"Score: {self.score}", True, (255,255,255))
        score_rect = score_t.get_rect(center=(400, 240))
        self.screen.blit(score_t, score_rect)

        best_t = self.font.render(f"Best: {self.best}", True, (255,255,0))
        best_rect = best_t.get_rect(center=(400, 280))
        self.screen.blit(best_t, best_rect)

        hint1 = self.font.render("Press SPACE to retry level", True, (200, 200, 200))
        hint1_rect = hint1.get_rect(center=(400, 340))
        self.screen.blit(hint1, hint1_rect)

        hint2 = self.font.render("Press ESC to menu", True, (200, 200, 200))
        hint2_rect = hint2.get_rect(center=(400, 380))
        self.screen.blit(hint2, hint2_rect)

        for e in events:
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    self.start_level(self.current_level)
                elif e.key == K_ESCAPE:
                    self.state = "menu"
                    save_progress(self.max_unlocked_level, self.best)

if __name__ == "__main__":
    Game().run()