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
PERSONAJE = os.path.join(GRAPHICS_FILE, "characters", "Idle sheet info.png")

class player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        try:
            # Cargar la spritesheet
            sprite_sheet = SpriteSheet(PERSONAJE)
            
            # Opción 1: Cargar un sprite individual (ajusta los valores según tu spritesheet)
            # frame = sprite_sheet.image_at((0, 0, 32, 32), colorkey=-1)
            
            # Opción 2: Cargar una fila de sprites para animación
            # Si tu spritesheet tiene sprites en fila, especifica:
            # (x_inicial, y_inicial, ancho_sprite, alto_sprite)
            self.frames = sprite_sheet.load_strip((0, 0, 16, 16), 4, colorkey=-1)
            
            # Guardar el frame actual
            self.current_frame = 0
            self.animation_speed = 0.1
            self.animation_timer = 0
            
            # Escalar el sprite (sin suavizado para mantener píxeles nítidos)
            frame = self.frames[self.current_frame]
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
        
        # Actualizar animación
        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            
            # Actualizar la imagen con el frame actual (sin suavizado)
            frame = self.frames[self.current_frame]
            new_width = frame.get_width() * SCALE
            new_height = frame.get_height() * SCALE
            old_center = self.rect.center
            self.image = pygame.transform.scale(frame, (new_width, new_height))
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