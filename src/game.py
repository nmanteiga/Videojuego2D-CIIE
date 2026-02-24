import pygame
import sys
import os
from escena import *
from menuPausa import MenuPausa
from sprtesheet import SpriteSheet

# NOTA: todas las partes que he puesto COMENTADO son las de la capa de delante del counter en la cocina 
#       las he comentado porque no lo apliqué al mapa completo aún, pero no afectan a la funcionalidad
#       es más algo estético, cuando toque se cambiará pero mientras NO borrar las líneas con el # COMENTADO tysm

SCALE = 4  
# ANCHO, ALTO = 800, 600 (Definidos en escena.py)

ANCHO_MAPA = 1472
ALTO_MAPA = 3200

HOME = os.path.dirname(__file__)
ASSESTS_FILE = os.path.join(HOME, "..", "assets")
GRAPHICS_FILE = os.path.join(ASSESTS_FILE, "graphics")

FONDO_IMG = os.path.join(GRAPHICS_FILE, "environments", "fondo_completo.png")  
# FRENTE_IMG = os.path.join(GRAPHICS_FILE, "environments", "capa_frente.png")  # COMENTADO
COLISION_IMG = os.path.join(GRAPHICS_FILE, "environments", "colisiones_fondo_completo.png") 

PERSONAJE_IDLE = os.path.join(GRAPHICS_FILE, "characters", "Idle sheet info.png")
PERSONAJE_MOVE = os.path.join(GRAPHICS_FILE, "characters", "Walk-Sheet.png")

# --- CLASE CÁMARA ---
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
        # Spawn point en la cocina (abajo a la izquierda)
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

        self.rect.clamp_ip(pygame.Rect(0, 0, ANCHO_MAPA, ALTO_MAPA))

        if dx == 0 and dy == 0:
            animation_base = f'idle_{self.last_action_base}'  
        elif dx != 0 and dy != 0:
            if dy > 0:
                animation_base = 'walk_dup'
                self.last_action_base = 'dup'
            elif dy < 0:
                animation_base = 'walk_ddown'
                self.last_action_base = 'ddown'
            if dx > 0: self.facing_right = True
            else: self.facing_right = False 
        elif dy != 0 and dx == 0:
            if dy < 0:
                animation_base = 'walk_up'
                self.last_action_base = 'up'
            else:
                animation_base = 'walk_down'
                self.last_action_base = 'down'
        else:
            animation_base = 'walk_r'
            self.last_action_base = 'r'
            if dx > 0: self.facing_right = True
            else: self.facing_right = False

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


class Juego(Escena):

    def __init__(self, director):
        Escena.__init__(self, director)
        
        self.fondo = pygame.image.load(FONDO_IMG).convert_alpha()
        self.fondo = pygame.transform.scale(self.fondo, (ANCHO_MAPA, ALTO_MAPA))

        # COMENTADO
        # self.frente = pygame.image.load(FRENTE_IMG).convert_alpha()
        # self.frente = pygame.transform.scale(self.frente, (ANCHO_MAPA, ALTO_MAPA))

        col_img = pygame.image.load(COLISION_IMG).convert_alpha()
        col_img = pygame.transform.scale(col_img, (ANCHO_MAPA, ALTO_MAPA))
        self.mask_colision = pygame.mask.from_surface(col_img)

        self.jugador = Player(self.mask_colision)
        self.sprites = pygame.sprite.Group()
        self.sprites.add(self.jugador)

        self.camara = Camara(ANCHO_MAPA, ALTO_MAPA)

    def eventos(self, lista_eventos):
        for evento in lista_eventos:
            if evento.type == pygame.QUIT:
                self.director.salirPrograma()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.director.apilarEscena(MenuPausa(self.director))

    def update(self, tiempo_pasado):
        self.sprites.update()
        self.camara.actualizar(self.jugador)

    def dibujar(self, pantalla):
        pantalla.fill((0, 0, 0))

        pantalla.blit(self.fondo, self.camara.aplicar_rect(self.fondo.get_rect()))       
        
        for sprite in self.sprites:
            pantalla.blit(sprite.image, self.camara.aplicar(sprite))
            
        # COMENTADO
        # pantalla.blit(self.frente, self.camara.aplicar_rect(self.frente.get_rect()))