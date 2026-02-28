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

ANCHO_MAPA = 2112 # El anterior ancho era 1472, pero era demasiado estrecho
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
    def __init__(self, width, height, world_width, world_height, zoom):
        # Tamaño de la ventana de visualización:
        self.width = width
        self.height = height

        # Tamaño del mapa:
        self.world_width = world_width
        self.world_height = world_height

        # Nivel de zoom:
        self.zoom = zoom

        # Tamaño de lo que ve la cámara con el zoom (viewport):
        self.viewport_width = int(self.width / self.zoom)
        self.viewport_height = int(self.height / self.zoom)

        # Inicializamos la cámara final:
        self.ancho_cam = self.viewport_width
        self.alto_cam = self.viewport_height
        self.camara = pygame.Rect(0, 0, self.ancho_cam, self.alto_cam)

        # Ajustes para el suavizado de la cámara:
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.camara.topleft = (int(self.cam_x), int(self.cam_y))
        self.factor_suav = 0.12 # Entre 0.10 y 0.15 es donde mejor funciona

    # Interpolación lineal para el suavizado de la cámara:
    def interp(self, a, b, t):
        return a + (b - a) * t

    def aplicar(self, entidad):
        return entidad.rect.move(self.camara.topleft)

    def aplicar_rect(self, rect):
        return rect.move(self.camara.topleft)
    
    # La cámara se actualiza dependiendo de si el jugador se encuentra o no en una sala:
    def update(self, objetivo, salas):
        # En caso de que el jugador se encuentre en una sala:
        for sala in salas:
            if sala.collidepoint(objetivo.rect.center):
                if sala.width <= self.ancho_cam and sala.height <= self.alto_cam:
                    # Si la sala es más pequeña que la cámara, esta se centra y se bloquea:
                    x = -sala.centerx + int(self.ancho_cam / 2)
                    y = -sala.centery + int(self.alto_cam / 2)
                else:
                    # En el caso contrario, la cámara se puede desplazar, pero sólo dentro de la sala:
                    x = -objetivo.hitbox.centerx + int(self.ancho_cam / 2) # Se usa la hitbox como referencia para...
                    y = -objetivo.hitbox.centery + int(self.alto_cam / 2) # ... intentar evitar errores de desincronización

                    # Establecemos los límites de la sala:
                    lim_izq = -sala.left
                    lim_der = -(sala.right - self.ancho_cam)
                    lim_sup = -sala.top
                    lim_inf = -(sala.bottom - self.alto_cam)

                    x = max(lim_der, min(lim_izq, x)) # Obliga a estar entre el límite derecho e izquierdo
                    y = max(lim_inf, min(lim_sup, y)) # Obliga a estar entre el límite superior e inferior
                
                # Actualización de la camara con suavizado:
                self.cam_x = self.interp(self.cam_x, x, self.factor_suav)
                self.cam_y = self.interp(self.cam_y, y, self.factor_suav)
                self.camara.topleft = (int(self.cam_x), int(self.cam_y))
                return
        
        # Si el jugador no se encuentra en ninguna sala, el comportamiento es el normal:
        x = -objetivo.hitbox.centerx + int(self.ancho_cam / 2) # Se usa la hitbox como referencia para...
        y = -objetivo.hitbox.centery + int(self.alto_cam / 2) # ... intentar evitar errores de desincronización

        # Se ajusta la cámara a los límites del mapa:
        x = min(0, x)
        y = min(0, y)
        x = max(-(self.world_width - self.ancho_cam), x)
        y = max(-(self.world_height - self.alto_cam), y)

        # Actualización de la camara con suavizado:
        self.cam_x = self.interp(self.cam_x, x, self.factor_suav)
        self.cam_y = self.interp(self.cam_y, y, self.factor_suav)
        self.camara.topleft = (int(self.cam_x), int(self.cam_y))
        return

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

        HITBOX_ANCHO = 120
        HITBOX_ALTO = 140
        self.hitbox = pygame.Rect(0, 0, HITBOX_ANCHO, HITBOX_ALTO)
        self.hitbox.center = self.rect.center

        hitbox_surf = pygame.Surface((HITBOX_ANCHO, HITBOX_ALTO), pygame.SRCALPHA)
        hitbox_surf.fill((255, 255, 255, 255))
        self.hitbox_mask = pygame.mask.from_surface(hitbox_surf)

        self.pos_x = float(self.hitbox.x)
        self.pos_y = float(self.hitbox.y)
        
    def check_collision(self):
        offset = (self.hitbox.x, self.hitbox.y)
        return self.mask_colision_mapa.overlap(self.hitbox_mask, offset)

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
        
        old_pos_x = self.pos_x
        self.pos_x += dx * self.velocidad
        self.hitbox.x = round(self.pos_x)
        if self.check_collision():
            self.pos_x = old_pos_x
            self.hitbox.x = round(self.pos_x)

        old_pos_y = self.pos_y
        self.pos_y += dy * self.velocidad
        self.hitbox.y = round(self.pos_y)
        if self.check_collision():
            self.pos_y = old_pos_y
            self.hitbox.y = round(self.pos_y)

        self.rect.clamp_ip(pygame.Rect(0, 0, ANCHO_MAPA, ALTO_MAPA))
        self.pos_x = float(self.hitbox.x)
        self.pos_y = float(self.hitbox.y)

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
        self.rect.center = self.hitbox.center
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

        self.camara = Camara(ANCHO, ALTO, ANCHO_MAPA, ALTO_MAPA, zoom = 0.95)

        # Se definen las coordenadas de las salas para el funcionamiento de la cámara:
        self.salas = [
            pygame.Rect(0, ALTO_MAPA - 640, 828, 630), # Cocina
            pygame.Rect(1280, 1920, 828, 630), # Sala del medio derecha
            pygame.Rect(0, 640, 828, 1280) # Laberinto de arriba izquierda
        ]

        # Al comenzar, la cámara se centra en la sala inicial (la cocina):
        self.sala_inicial = pygame.Rect(0, ALTO_MAPA - 640, 828, 630)
        x = -self.sala_inicial.centerx + int(ANCHO / 2)
        y = -self.sala_inicial.centery + int(ALTO / 2)

        x = min(0, x)
        y = min(0, y)
        x = max(-(ANCHO_MAPA - ANCHO), x)
        y = max(-(ALTO_MAPA - ALTO), y)

        # Se calculan cam_x y cam_y para que la cámara no de ningún salto brusco al inicio.
        # Ocurría porque cam_x y cam_y están como "0.0" en el init de la cámara:
        self.camara.cam_x = x + 20 # Se suman 20 y 16 para que no haya ningún...
        self.camara.cam_y = y + 16 # ... desplazamiento al inicio del juego
        self.camara.camara.topleft = (int(x), int(y))

    def eventos(self, lista_eventos):
        for evento in lista_eventos:
            if evento.type == pygame.QUIT:
                self.director.salirPrograma()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.director.apilarEscena(MenuPausa(self.director))

    def update(self, tiempo_pasado):
        self.sprites.update()
        self.camara.update(self.jugador, self.salas)

    def dibujar(self, pantalla):
        pantalla.fill((0, 0, 0))

        # Ahora, la pantalla se dibuja y luego se escala correctamente:
        render_surface = pygame.Surface((self.camara.ancho_cam, self.camara.alto_cam), pygame.SRCALPHA) # Resolución lógica más grande
        render_surface.blit(self.fondo, self.camara.aplicar_rect(self.fondo.get_rect())) # Se dibuja el mundo en esa resolución

        for sprite in self.sprites:
            render_surface.blit(sprite.image, self.camara.aplicar(sprite))

        # La resolución anterior se escala al tamaño real de la pantalla
        scaled_surface = pygame.transform.scale(render_surface, (ANCHO, ALTO))

        pantalla.blit(scaled_surface, (0, 0))
            
        # COMENTADO
        # pantalla.blit(self.frente, self.camara.aplicar_rect(self.frente.get_rect()))

        #debug para axustar a hitbox visualmente
        #hitbox_en_pantalla = self.camara.aplicar_rect(self.jugador.hitbox)
        #pygame.draw.rect(pantalla, (255, 0, 0), hitbox_en_pantalla, 2)
