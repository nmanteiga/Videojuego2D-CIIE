import pygame
import sys
import os
from escena import *
from menuPausa import MenuPausa
from sprtesheet import SpriteSheet
from cocinado import XestorCocina
from escena_room2 import Room2Event

SCALE = 4  
# ANCHO, ALTO = 800, 600 (Definidos en escena.py)

ANCHO_MAPA = 2112 # El anterior ancho era 1472, pero era demasiado estrecho
ALTO_MAPA = 3200

COLISION_SCALE_DOWN = 4

DÍA = 1
NOITE = True
DEBUG_COLISION_MAPA = False

HOME = os.path.dirname(__file__)
ASSESTS_FILE = os.path.join(HOME, "..", "assets")
GRAPHICS_FILE = os.path.join(ASSESTS_FILE, "graphics")

FONDO_IMG = os.path.join(GRAPHICS_FILE, "environments", "fondo_completo.png")  
FRENTE_IMG = os.path.join(GRAPHICS_FILE, "environments", "capa_frente.png")
COLISION_IMG = os.path.join(GRAPHICS_FILE, "environments", "colisiones2.png")
FRENTE_CLASE1 = os.path.join(GRAPHICS_FILE, "environments", "capa_frente_clase1.png")

PERSONAJE_IDLE = os.path.join(GRAPHICS_FILE, "characters", "Idle sheet info.png")
PERSONAJE_MOVE = os.path.join(GRAPHICS_FILE, "characters", "Walk-Sheet.png")

def _preescalar_animaciones(animaciones, total_scale):
    """Escala y voltea todos los frames UNA sola vez al arrancar."""
    normales, volteados = {}, {}
    for nombre, frames in animaciones.items():
        fn, fv = [], []
        for frame in frames:
            w   = int(frame.get_width()  * total_scale)
            h   = int(frame.get_height() * total_scale)
            esc = pygame.transform.scale(frame, (w, h))
            fn.append(esc)
            fv.append(pygame.transform.flip(esc, True, False))
        normales[nombre]  = fn
        volteados[nombre] = fv
    return normales, volteados

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
    def update(self, objetivo, salas, focus_world_pos=None):
        if focus_world_pos is None:
            objetivo_cx, objetivo_cy = objetivo.hitbox.center
        else:
            objetivo_cx, objetivo_cy = focus_world_pos

        # En caso de que el jugador se encuentre en una sala:
        for sala in salas:
            if sala.collidepoint((objetivo_cx, objetivo_cy)):
                if sala.width <= self.ancho_cam and sala.height <= self.alto_cam:
                    # Si la sala es más pequeña que la cámara, esta se centra y se bloquea:
                    x = -sala.centerx + int(self.ancho_cam / 2)
                    y = -sala.centery + int(self.alto_cam / 2)
                else:
                    # En el caso contrario, la cámara se puede desplazar, pero sólo dentro de la sala:
                    x = -objetivo_cx + int(self.ancho_cam / 2)
                    y = -objetivo_cy + int(self.alto_cam / 2)

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
        x = -objetivo_cx + int(self.ancho_cam / 2)
        y = -objetivo_cy + int(self.alto_cam / 2)

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
        self.colision_scale_down = COLISION_SCALE_DOWN
        self.extra_scale = 1.8 
        self.total_scale = SCALE * self.extra_scale

        try:
            sprite_sheet = SpriteSheet(PERSONAJE_IDLE)
            walk_sheet = SpriteSheet(PERSONAJE_MOVE)
            raw = {
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
            self.animations, self.animations_flip = _preescalar_animaciones(raw, self.total_scale)
            # Máscaras pre-calculadas — nunca más en update()
            self.masks      = {k: [pygame.mask.from_surface(f) for f in v]
                               for k, v in self.animations.items()}
            self.masks_flip = {k: [pygame.mask.from_surface(f) for f in v]
                               for k, v in self.animations_flip.items()}
        except (FileNotFoundError, pygame.error) as e:
            print(f"Error cargando spritesheet: {e}")
            raise
            
        self.last_action_base = 'down'
        self.current_animation = 'idle_down'
        self.facing_right = True
        self.current_frame = 0
        self.animation_speed = 4/60
        self.animation_timer = 0
        
        self.image = self.animations['idle_down'][0]
        self.mask  = self.masks['idle_down'][0]
        self.rect  = self.image.get_rect()
        self.rect.center = (400, ALTO_MAPA - 300)
        self.velocidad = 6


        HITBOX_ANCHO = 70
        HITBOX_ALTO = 120
        self.hitbox = pygame.Rect(0, 0, HITBOX_ANCHO, HITBOX_ALTO)
        self.hitbox.center = self.rect.center

        s = self.colision_scale_down
        hw_r, hh_r = max(1, HITBOX_ANCHO // s), max(1, HITBOX_ALTO // s)
        hsurf = pygame.Surface((hw_r, hh_r), pygame.SRCALPHA)
        hsurf.fill((255, 255, 255, 255))
        self.hitbox_mask = pygame.mask.from_surface(hsurf)

        self.pos_x = float(self.hitbox.x)
        self.pos_y = float(self.hitbox.y)
        self.controls_enabled = True
        self.extra_collision_rects = []

    def set_extra_collision_rects(self, rects):
        self.extra_collision_rects = list(rects)
        
    def check_collision(self):
        s  = self.colision_scale_down
        ox = self.hitbox.x // s
        oy = self.hitbox.y // s
        if self.mask_colision_mapa.overlap(self.hitbox_mask, (ox, oy)):
            return True

        for blocker in self.extra_collision_rects:
            if self.hitbox.colliderect(blocker):
                return True
        return False

    def update(self):
        teclas = pygame.key.get_pressed() if self.controls_enabled else None
        dx, dy = 0, 0
        
        if teclas:
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
            self.current_frame = (self.current_frame + 1) % len(self.animations[self.current_animation])

        # Imagen y máscara PRE-CALCULADAS — sin transform en runtime
        if self.facing_right:
            self.image = self.animations[self.current_animation][self.current_frame]
            self.mask  = self.masks[self.current_animation][self.current_frame]
        else:
            self.image = self.animations_flip[self.current_animation][self.current_frame]
            self.mask  = self.masks_flip[self.current_animation][self.current_frame]

        self.rect = self.image.get_rect()
        self.rect.center = self.hitbox.center


class Juego(Escena):

    def __init__(self, director):
        Escena.__init__(self, director)
        
        self.fondo = pygame.image.load(FONDO_IMG).convert_alpha()
        self.fondo = pygame.transform.scale(self.fondo, (ANCHO_MAPA, ALTO_MAPA))

        self.frente = pygame.image.load(FRENTE_IMG).convert_alpha()
        self.frente = pygame.transform.scale(self.frente, (ANCHO_MAPA, ALTO_MAPA))

        
        self.frente_clase1 = pygame.image.load(FRENTE_CLASE1).convert_alpha()
        self.frente_clase1 = pygame.transform.scale(self.frente_clase1, (ANCHO_MAPA, ALTO_MAPA))

        s = COLISION_SCALE_DOWN
        col_img = pygame.image.load(COLISION_IMG).convert_alpha()
        col_w   = ANCHO_MAPA // s
        col_h   = ALTO_MAPA  // s
        col_img = pygame.transform.scale(col_img, (col_w, col_h))
        self.mask_colision = pygame.mask.from_surface(col_img)

        col_debug = pygame.image.load(COLISION_IMG).convert_alpha()
        col_debug = pygame.transform.scale(col_debug, (ANCHO_MAPA, ALTO_MAPA))
        col_debug.set_alpha(80)
        self.colision_debug_overlay = col_debug

        self.jugador = Player(self.mask_colision)
        self.sprites = pygame.sprite.Group()
        self.sprites.add(self.jugador)

        self.camara = Camara(ANCHO, ALTO, ANCHO_MAPA, ALTO_MAPA, zoom = 0.95)

        # Se definen las coordenadas de las salas para el funcionamiento de la cámara:
        self.salas = [
            pygame.Rect(0, ALTO_MAPA - 640, 832, 630), # Cocina
            pygame.Rect(1280, 1910, 832, 660), # Sala del medio derecha
            pygame.Rect(0, 640, 832, 1280) # Laberinto de arriba izquierda
        ]
        self.room2_event = Room2Event(
            GRAPHICS_FILE,
            COLISION_SCALE_DOWN,
            self.salas[2],
            (ANCHO_MAPA, ALTO_MAPA),
        )

        # Al comenzar, la cámara se centra en la sala inicial (la cocina):
        self.sala_inicial = pygame.Rect(0, ALTO_MAPA - 640, 828, 630)
        x = -self.sala_inicial.centerx + int(ANCHO / 2)
        y = -self.sala_inicial.centery + int(ALTO / 2)

        x = min(0, x)
        y = min(0, y)
        x = max(-(ANCHO_MAPA - ANCHO), x)
        y = max(-(ALTO_MAPA - ALTO), y)

        self.cocina = XestorCocina(self.jugador)

        self._render_surf = pygame.Surface(
            (self.camara.ancho_cam, self.camara.alto_cam), pygame.SRCALPHA
        )

        # Pre-cargar y pre-escalar a imaxe de cuberta de sala unha soa vez:
        bg_path = os.path.join(GRAPHICS_FILE, 'environments', 'background.png')
        if os.path.exists(bg_path):
            _bg_src = pygame.image.load(bg_path).convert_alpha()
            self._area_bg_imgs = [
                pygame.transform.scale(_bg_src, (sala.width, sala.height))
                for sala in self.salas
            ]
        else:
            self._area_bg_imgs = None

    def eventos(self, lista_eventos):
        self.cocina.eventos(lista_eventos) 
        for evento in lista_eventos:
            if evento.type == pygame.QUIT:
                self.director.salirPrograma()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.director.apilarEscena(MenuPausa(self.director))

    def update(self, tiempo_pasado):
        self.jugador.set_extra_collision_rects(self.room2_event.get_extra_collision_rects())

        self.sprites.update()
        focus_pos = self.room2_event.update(self.jugador, tiempo_pasado)

        self.camara.update(self.jugador, self.salas, focus_world_pos=focus_pos)
        self.cocina.update(tiempo_pasado)

    def dibujar(self, pantalla):
        pantalla.fill((0, 0, 0))
        

        # Ahora, la pantalla se dibuja y luego se escala correctamente:
        self._render_surf.fill((0, 0, 0, 0))
        self._render_surf.blit(self.fondo, self.camara.aplicar_rect(self.fondo.get_rect()))
        self.room2_event.draw_objects(self._render_surf, self.camara)

        for sprite in self.sprites:
            self._render_surf.blit(sprite.image, self.camara.aplicar(sprite))

        self.room2_event.draw_front(self._render_surf, self.camara)

        self._render_surf.blit(self.frente, self.camara.aplicar_rect(self.frente.get_rect()))

        sala_clase1 = self.salas[1]  # Sala del medio derecha
        if sala_clase1.collidepoint(self.jugador.hitbox.center):
            self._render_surf.blit(self.frente_clase1, self.camara.aplicar_rect(self.frente_clase1.get_rect()))

        if DEBUG_COLISION_MAPA:
            self._render_surf.blit(
                self.colision_debug_overlay,
                self.camara.aplicar_rect(self.colision_debug_overlay.get_rect())
            )
            self.colision_debug_overlay.set_alpha(80)

        self.room2_event.draw_light_overlay(self._render_surf, self.camara, self.jugador)

        # Cubrir as salas onde o xogador NON está (dentro de _render_surf, antes de escalar):
        if self._area_bg_imgs:
            for sala, area_img in zip(self.salas, self._area_bg_imgs):
                if not sala.collidepoint(self.jugador.hitbox.center):
                    self._render_surf.blit(area_img, self.camara.aplicar_rect(sala))

        self.cocina.dibujar(self._render_surf, self.camara)

        # La resolución anterior se escala al tamaño real de la pantalla
        scaled_surface = pygame.transform.scale(self._render_surf, (ANCHO, ALTO))
        pantalla.blit(scaled_surface, (0, 0))

        if NOITE == 1:
            overlay = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
            overlay.fill((12, 4, 33, 180)) 
            pantalla.blit(overlay, (0, 0))
