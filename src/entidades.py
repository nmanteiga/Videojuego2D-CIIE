import pygame
import os
from sprtesheet import SpriteSheet
from escena import ANCHO, ALTO # pillamos el tamaño de pantalla 

# numeritos generales del mapa y tal
SCALE = 4  
ANCHO_MAPA = 1472
ALTO_MAPA = 3200

# donde estan guardabas las animaciones del pj
HOME = os.path.dirname(__file__)
ASSESTS_FILE = os.path.join(HOME, "..", "assets")
GRAPHICS_FILE = os.path.join(ASSESTS_FILE, "graphics")
PERSONAJE_IDLE = os.path.join(GRAPHICS_FILE, "characters", "Idle sheet info.png")
PERSONAJE_MOVE = os.path.join(GRAPHICS_FILE, "characters", "Walk-Sheet.png")

class Camara:
    def __init__(self, width, height):
        self.camara = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def aplicar(self, entidad):
        return entidad.rect.move(self.camara.topleft)

    def aplicar_rect(self, rect):
        return rect.move(self.camara.topleft)

    def actualizar(self, objetivo):
        x = -objetivo.rect.centerx + int(ANCHO / 2)
        y = -objetivo.rect.centery + int(ALTO / 2)

        x = min(0, x)  
        y = min(0, y)  
        x = max(-(self.width - ANCHO), x)  
        y = max(-(self.height - ALTO), y)  

        self.camara = pygame.Rect(x, y, self.width, self.height)

class Player(pygame.sprite.Sprite):
    def __init__(self, mask_colision_mapa):
        super().__init__()
        
        self.mask_colision_mapa = mask_colision_mapa
        self.extra_scale = 1.8 
        self.total_scale = SCALE * self.extra_scale

        try:
            sprite_sheet = SpriteSheet(PERSONAJE_IDLE)
            walk_sheet = SpriteSheet(PERSONAJE_MOVE)
            self.animations = {
                'idle_down': sprite_sheet.load_strip((0, 0, 16, 16), 4),
                'idle_dup': sprite_sheet.load_strip((0, 16, 16, 16), 4),
                'idle_r': sprite_sheet.load_strip((0, 32, 16, 16), 4),
                'idle_ddown': sprite_sheet.load_strip((0, 48, 16, 16), 4),
                'idle_up': sprite_sheet.load_strip((0, 64, 16, 16), 4),
                'walk_down': walk_sheet.load_strip((0, 0, 16, 16), 4),
                'walk_dup': walk_sheet.load_strip((0, 16, 16, 16), 4),
                'walk_r': walk_sheet.load_strip((0, 32, 16, 16), 4),
                'walk_ddown': walk_sheet.load_strip((0, 48, 16, 16), 4),
                'walk_up': walk_sheet.load_strip((0, 64, 16, 16), 4),
            }
            
            self.last_action_base = 'down'
            self.current_animation = 'idle_down'
            self.facing_right = True
            self.current_frame = 0
            self.animation_speed = 4/60
            self.animation_timer = 0
            
            frame = self.animations[self.current_animation][self.current_frame]
            new_width = int(frame.get_width() * self.total_scale)  
            new_height = int(frame.get_height() * self.total_scale) 
            self.image = pygame.transform.scale(frame, (new_width, new_height))
            
            self.mask = pygame.mask.from_surface(self.image)

        except (FileNotFoundError, pygame.error) as e:
            print(f"Error cargando spritesheet: {e}")

        self.rect = self.image.get_rect()
        # donde aparece el jugador al inicio de la partida
        self.rect.center = (400, ALTO_MAPA - 300) 
        self.velocidad = 6 
        
    def check_collision(self):
        offset = (self.rect.x, self.rect.y)
        return self.mask_colision_mapa.overlap(self.mask, offset)

    def update(self):
        teclas = pygame.key.get_pressed()
        dx, dy = 0, 0
        
        if teclas[pygame.K_a]: dx -= 1
        if teclas[pygame.K_d]: dx += 1
        if teclas[pygame.K_w]: dy -= 1
        if teclas[pygame.K_s]: dy += 1
        
        if dx != 0 or dy != 0:
            magnitud = (dx**2 + dy**2) ** 0.5
            dx /= magnitud
            dy /= magnitud
        
        move_x = dx * self.velocidad
        self.rect.x += move_x
        if self.check_collision(): 
            self.rect.x -= move_x 
        
        move_y = dy * self.velocidad
        self.rect.y += move_y
        if self.check_collision(): 
            self.rect.y -= move_y  

        if dx == 0 and dy == 0:
            animation_base = f'idle_{self.last_action_base}'  
        elif dx != 0 and dy != 0:
            if dy > 0: animation_base, self.last_action_base = 'walk_dup', 'dup'
            elif dy < 0: animation_base, self.last_action_base = 'walk_ddown', 'ddown'
            self.facing_right = (dx > 0)
        elif dy != 0 and dx == 0:
            if dy < 0: animation_base, self.last_action_base = 'walk_up', 'up'
            else: animation_base, self.last_action_base = 'walk_down', 'down'
        else:
            animation_base, self.last_action_base = 'walk_r', 'r'
            self.facing_right = (dx > 0)

        if animation_base != self.current_animation:
            self.current_animation = animation_base
            self.current_frame = 0
        
        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1:
            self.animation_timer = 0
            frames = self.animations[self.current_animation]
            self.current_frame = (self.current_frame + 1) % len(frames)
        
        frames = self.animations[self.current_animation]
        frame = frames[self.current_frame]
        
        new_width = int(frame.get_width() * self.total_scale)
        new_height = int(frame.get_height() * self.total_scale)
        old_center = self.rect.center
        
        scaled_frame = pygame.transform.scale(frame, (new_width, new_height))
        if not self.facing_right:
            scaled_frame = pygame.transform.flip(scaled_frame, True, False)
        
        self.image = scaled_frame
        self.rect = self.image.get_rect()
        self.rect.center = old_center
        self.mask = pygame.mask.from_surface(self.image)