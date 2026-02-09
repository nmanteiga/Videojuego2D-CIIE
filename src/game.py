# TW: el código está en spanglish, sorry I'm a diva
import pygame
import sys
import os 
from sprtesheet import SpriteSheet


ANCHO = 800
ALTO = 600
FPS = 60
SCALE = 4  

HOME = os.path.dirname(__file__)
ASSESTS_FILE = os.path.join(HOME, "..", "assets")
GRAPHICS_FILE = os.path.join(ASSESTS_FILE, "graphics")
FONDO = os.path.join(GRAPHICS_FILE, "environments", "fondo_prueba.jpg")
PERSONAJE_IDLE = os.path.join(GRAPHICS_FILE, "characters", "Idle sheet info.png")
PERSONAJE_MOVE = os.path.join(GRAPHICS_FILE, "characters", "Walk-Sheet.png")

class player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        try:
            # Cargar la spritesheet
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
            
            
            # Cargar una fila de sprites para animación
            # (x_inicial, y_inicial, ancho_sprite, alto_sprite)
            self.last_action_base = 'down'
            self.current_animation = 'idle_down'
            self.facing_right = True
            # Guardar el frame actual
            self.current_frame = 0
            self.animation_speed = 0.1
            self.animation_timer = 0
            
            # Escalar el sprite (sin suavizado para mantener píxeles nítidos)
            frame = self.animations[self.current_animation][self.current_frame]
            new_width = frame.get_width() * SCALE
            new_height = frame.get_height() * SCALE
            self.image = pygame.transform.scale(frame, (new_width, new_height))
            
        except (FileNotFoundError, pygame.error) as e:
            print(f"Error cargando spritesheet: {e}")

        self.rect = self.image.get_rect()
        self.rect.center = (ANCHO // 2, ALTO // 2)
        self.velocidad = 5

    # módulo update
    def update(self):
        teclas = pygame.key.get_pressed()
        dx = 0
        dy = 0
        
        if teclas[pygame.K_a]: dx -= 1
        if teclas[pygame.K_d]: dx += 1
        if teclas[pygame.K_w]: dy -= 1
        if teclas[pygame.K_s]: dy += 1
        
        # Normalizar el vector
        if dx != 0 or dy != 0:
            magnitud = (dx**2 + dy**2) ** 0.5
            dx /= magnitud
            dy /= magnitud
        
        self.rect.x += dx * self.velocidad
        self.rect.y += dy * self.velocidad
        
        # 1. Determinar animación base y dirección de flip
        if dx == 0 and dy == 0:
            # Quieto
            animation_base = f'idle_{self.last_action_base}'  # la última dirección
            
        elif dx != 0 and dy != 0:
            # DIAGONAL (ambas teclas presionadas)
            if dy > 0:
                animation_base = 'walk_dup'
                self.last_action_base = 'dup'
            elif dy < 0:
                animation_base = 'walk_ddown'
                self.last_action_base = 'ddown'
            if dx > 0:
                self.facing_right = True   # Diagonal derecha
            else:
                self.facing_right = False  # Diagonal izquierda (flip)
                
        elif dy != 0 and dx == 0:
            # Solo vertical (arriba/abajo)
            if dy < 0:
                animation_base = 'walk_up'
                self.last_action_base = 'up'     # Fila específica para arriba
            else:
                animation_base = 'walk_down'
                self.last_action_base = 'down'   # Fila específica para abajo
                
        else:
            # Solo horizontal (izquierda/derecha)
            animation_base = 'walk_r'
            self.last_action_base = 'r'
            if dx > 0:
                self.facing_right = True
            else:
                self.facing_right = False
        
        # Si cambió la animación, reiniciar frame
        if animation_base != self.current_animation:
            self.current_animation = animation_base
            self.current_frame = 0
        
        # Actualizar animación (avanzar frames)
        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1:
            self.animation_timer = 0
            frames = self.animations[self.current_animation]
            self.current_frame = (self.current_frame + 1) % len(frames)
        
        # Actualizar la imagen cada frame (sin suavizado)
        frames = self.animations[self.current_animation]
        frame = frames[self.current_frame]
        new_width = frame.get_width() * SCALE
        new_height = frame.get_height() * SCALE
        old_center = self.rect.center
        
        # Escalar
        scaled_frame = pygame.transform.scale(frame, (new_width, new_height))
        
        # Aplicar flip si mira a la izquierda
        if not self.facing_right:
            scaled_frame = pygame.transform.flip(scaled_frame, True, False)
        
        self.image = scaled_frame
        self.rect = self.image.get_rect()
        self.rect.center = old_center

pygame.init()
screen = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Prueba")
reloj = pygame.time.Clock()

try:
    fondo = pygame.image.load(FONDO).convert()
    fondo = pygame.transform.scale(fondo, (ANCHO, ALTO))
except FileNotFoundError:
    print(f"error")

jugador = player()
sprites = pygame.sprite.Group()
sprites.add(jugador)
ejecutando = True

while ejecutando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False

    sprites.update()
    screen.blit(fondo, (0, 0)) 
    sprites.draw(screen)
    
    pygame.display.flip()
    reloj.tick(FPS)

pygame.quit()
sys.exit()