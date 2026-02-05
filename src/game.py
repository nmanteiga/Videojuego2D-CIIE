# TW: el código está en spanglish, sorry I'm a diva
import pygame
import sys
import os 

ANCHO = 800
ALTO = 600
FPS = 60
SCALE = 4  

HOME = os.path.dirname(__file__)
ASSESTS_FILE = os.path.join(HOME, "..", "assets")
GRAPHICS_FILE = os.path.join(ASSESTS_FILE, "graphics")
FONDO = os.path.join(GRAPHICS_FILE, "environments", "fondo_prueba.jpg")
PERSONAJE = os.path.join(GRAPHICS_FILE, "characters", "personaje_prueba.png")

class player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        try:
            img = pygame.image.load(PERSONAJE).convert_alpha()
            
            # así el personaje está escalado en proporción al fondo
            new_width = img.get_width() // SCALE
            new_height = img.get_height() // SCALE
            self.image = pygame.transform.smoothscale(img, (new_width, new_height))
            
        except FileNotFoundError:
            print(f"error") # por si no reconoce el path

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