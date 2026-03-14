import pygame
import sys
import os
import math
from escena import *
from menuPausa import MenuPausa
from sprtesheet import SpriteSheet
from cocinado import XestorCocina
from escena_room2 import Room2Event
from gestorAudio import GestorAudio, VOL_MUSICA

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
FONDO_IMG_PARED = os.path.join(GRAPHICS_FILE, "environments", "fondo_completo_pared.png")  
FONDO_IMG_POSTER = os.path.join(GRAPHICS_FILE, "environments", "fondo_completo_poster.png")  
FRENTE_IMG = os.path.join(GRAPHICS_FILE, "environments", "capa_frente.png")
COLISION_IMG = os.path.join(GRAPHICS_FILE, "environments", "colisiones2.png")
FRENTE_CLASE1 = os.path.join(GRAPHICS_FILE, "environments", "capa_frente_clase1.png")
FRENTE_PASILLO = os.path.join(GRAPHICS_FILE, "environments", "capa_frente_pasllo.png")

PERSONAJE_IDLE = os.path.join(GRAPHICS_FILE, "characters", "Idle sheet info.png")
PERSONAJE_MOVE = os.path.join(GRAPHICS_FILE, "characters", "Walk-Sheet.png")
PERSONAJE_INTERACT = os.path.join(GRAPHICS_FILE, "characters", "Interact-Sheet.png")

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


class Disparador:
    def __init__(self, condicion_func, callback_accion, delay_ms=0):
        self.condicion_func = condicion_func     #o que ten que pasar (true/false)
        self.callback_accion = callback_accion   #función a executar cando se cumpra a condición
        self.delay_ms = delay_ms                 #canto espera (0 por defecto)
        
        self.tiempo_acumulado = 0
        self.disparado = False

    def update(self, tiempo_pasado):
        #se xa excecutada non facemos nada
        if self.disparado:
            return

        #se se cumple a condición
        if self.condicion_func():
            self.tiempo_acumulado += tiempo_pasado
            
            #e pasou o tempo necesario (se delay_ms é 0, entra instantáneo)
            if self.tiempo_acumulado >= self.delay_ms:
                self.disparado = True
                self.callback_accion()  # ¡Ejecutamos el comando!
        else:
            #se xogador sae da zona, reiniciamos o contador
            self.tiempo_acumulado = 0


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

        #para ver cando saltan os disparadores de cambio de sala
        self.vel_x = 0.0


    def esta_quieta_x(self):
        #se se move menos de medio píxel por fotograma en horizontal, a cámara considérase quieta (o que indica que se ha centrado en la sala)
        return self.vel_x < 0.01

    # Interpolación lineal para el suavizado de la cámara:
    def interp(self, a, b, t):
        return a + (b - a) * t

    def aplicar(self, entidad):
        return entidad.rect.move(self.camara.topleft)

    def aplicar_rect(self, rect):
        return rect.move(self.camara.topleft)
    
    # La cámara se actualiza dependiendo de si el jugador se encuentra o no en una sala:
    def update(self, objetivo, salas, focus_world_pos=None):
        #gardamos a x anterior
        old_x = self.cam_x

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

                #calculamos a velocidade horizontal da cámara para saber cando se centra completamente na sala e disparar os eventos de cambio de sala
                self.vel_x = abs(self.cam_x - old_x)
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

        #calculamos a velocidade x
        self.vel_x = abs(self.cam_x - old_x)
        return

class Player(pygame.sprite.Sprite):
    def __init__(self, mask_colision_mapa):
        super().__init__()
        self.audio = GestorAudio()
        
        self.mask_colision_mapa = mask_colision_mapa
        self.colision_scale_down = COLISION_SCALE_DOWN
        self.extra_scale = 1.8 
        self.total_scale = SCALE * self.extra_scale

        try:
            sprite_sheet = SpriteSheet(PERSONAJE_IDLE)
            walk_sheet = SpriteSheet(PERSONAJE_MOVE)
            interact_sheet = SpriteSheet(PERSONAJE_INTERACT)
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
                'interact_down': interact_sheet.load_strip((0, 0, 16, 16), 4),
                'interact_dup': interact_sheet.load_strip((0, 16, 16, 16), 4),
                'interact_r': interact_sheet.load_strip((0, 32, 16, 16), 4),
                'interact_ddown': interact_sheet.load_strip((0, 48, 16, 16), 4),
                'interact_up': interact_sheet.load_strip((0, 64, 16, 16), 4),
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
        self.animation_speed = 6/60
        self.animation_timer = 0
        
        self.image = self.animations['idle_down'][0]
        self.mask  = self.masks['idle_down'][0]
        self.rect  = self.image.get_rect()
        self.rect.center = (400, ALTO_MAPA - 300)
        self.velocidad = 5


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

        self.one_shot_active = False
        self.one_shot_animation = None

    def play_one_shot(self, animation_name):
        self.one_shot_active = True
        self.one_shot_animation = animation_name
        self.current_animation = animation_name
        self.current_frame = 0
        self.animation_timer = 0

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
        if self.one_shot_active:
            self.animation_timer += 2 * self.animation_speed
            if self.animation_timer >= 1:
                self.animation_timer = 0
                self.current_frame += 1
                if self.current_frame >= len(self.animations[self.one_shot_animation]):
                    self.one_shot_active = False
                    self.one_shot_animation = None
                    self.current_frame = 0
                    self.current_animation = f'idle_{self.last_action_base}'
            if self.one_shot_active:
                anim = self.one_shot_animation
                frame = min(self.current_frame, len(self.animations[anim]) - 1)
                if self.facing_right:
                    self.image = self.animations[anim][frame]
                    self.mask  = self.masks[anim][frame]
                else:
                    self.image = self.animations_flip[anim][frame]
                    self.mask  = self.masks_flip[anim][frame]
                self.rect = self.image.get_rect()
                self.rect.center = self.hitbox.center
                return

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

            # Al moverse, se reproduce el sonido de los pasos del personaje:
            if not self.audio.canal_personaje.get_busy():
                self.audio.reproducir_sonido("pasos", self.audio.canal_personaje)
        else:
            # Cuando el personaje se pare, se detiene el audio:
            if self.audio.canal_personaje.get_busy():
                self.audio.canal_personaje.stop()
        
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


#patrón Estado: progresión do xogo
class EstadoProgresion:
    def entrar(self, juego): pass
    def update(self, juego): pass

class Dia1(EstadoProgresion):
    def __init__(self):
        self.audio = GestorAudio()
        
    def entrar(self, juego):
        juego.es_de_noche = False
        juego.tortillas_objetivo = 2 #cambiar
        juego.cocina.puntos = 0 #reiniciamos contador tortillas
        juego.cocina_bloqueada = True

        juego._fade_inicial = False
        juego._fade_alpha = 0

        self.audio.reproducir_sonido("m_buenos_dias_papi")
        
        #lanzamos o diálogo inicial usando a nosa nova escena
        from escena_dialogo import EscenaDialogo
        dialogo = [
            "¡Pichi, a currar! Hoy hay mucha clientela",
            f"No te vas a la cama hasta que saques {juego.tortillas_objetivo} tortillas.",
            "¡Ponte a cocinar ya!"
        ]

        juego.director.apilarEscena(EscenaDialogo(juego.director, dialogo, "voz_michel"))

    def update(self, juego):
        #transición: unha vez feitas as 3 tortillas, pasa á Noche 1
        if juego.cocina.puntos >= juego.tortillas_objetivo:
            from escena_dialogo import EscenaDialogo
            dialogo_fin = ["¡Buen trabajo papi! Has terminado por hoy.", "La cafetería está cerrada."]
            
            #ao terminar de ler, cambiamos de estado a Noche 1
            def pasar_a_noche():
                self.audio.reproducir_sonido("m_buenas_noches")
                juego.cambiar_estado(Noche1())
                
            juego.director.apilarEscena(EscenaDialogo(juego.director, dialogo_fin, "voz_michel", pasar_a_noche))
            #para evitar bucles infinitos
            juego.cocina.puntos = 0 


class Noche1(EstadoProgresion):
    def entrar(self, juego):
        juego.es_de_noche = True
        juego.tiene_cuchara = False
        juego.agujero_excavado = False
        juego.actualizar_sala() #como se fai de noite hai que cambiar a música

    def update(self, juego):
        pass


class Dia2(EstadoProgresion):
    def __init__(self):
        self.audio = GestorAudio()

    def entrar(self, juego):
        juego.es_de_noche = False
        juego.tortillas_objetivo = 3 #cambiar
        juego.cocina.puntos = 0
        juego.cocina_bloqueada = True #o muro da cociña está bloqueado para obligar a cociñar
        juego.actualizar_sala()

        self.audio.reproducir_sonido("m_buenos_dias_pichi")
        
        from escena_dialogo import EscenaDialogo
        dialogo = [
            "¡Despierta, pichi!",
            "¿Y ese póster? ¿De onichan, arigato?",
            "Menudo friki estás hecho...",
            "Pero bueno...",
            f"Ayer estuviste vagonetas.",
            f"Hoy quiero {juego.tortillas_objetivo} tortillas. ¡A los fogones!"
        ]

        # Se usa callback para añadir diálogo tras el texto:
        def tras_dialogo2():
            self.audio.reproducir_sonido("m_una_tortillita")
        
        juego.director.apilarEscena(EscenaDialogo(juego.director, dialogo, "voz_michel", tras_dialogo2))

    def update(self, juego):
        if juego.cocina.puntos >= juego.tortillas_objetivo:
            from escena_dialogo import EscenaDialogo
            dialogo_fin = ["¡Ya era hora!", "Cerramos por hoy. A mimir."]
            def pasar_a_noche2():
                self.audio.reproducir_sonido("m_buenas_noches")
                juego.cambiar_estado(Noche2()) #pasamos á noite 2
            juego.director.apilarEscena(EscenaDialogo(juego.director, dialogo_fin, "voz_michel", pasar_a_noche2))
            juego.cocina.puntos = 0


class Noche2(EstadoProgresion):
    def __init__(self):
        self.audio = GestorAudio()

    def entrar(self, juego):
        juego.es_de_noche = True
        juego.cocina_bloqueada = False #agora xa se pode ir ao pasillo
        juego.actualizar_sala()

        self.mensaje_mostrado = False

    def update(self, juego):
        #comprobamos constantemente se carlitos pisou o pasillo
        if not self.mensaje_mostrado and juego.obtener_sala_actual() == "fuera_de_cocina":
            #damos 150 píxeles de marxe para que a cámara termine o scroll
            if juego.jugador.hitbox.left > (juego.puerta_cocina.right + 150):
                self.mensaje_mostrado = True #marcamos pa evitar bucles infinitos

                self.audio.reproducir_sonido("burbuja_texto", self.audio.canal_ui)
                from escena_dialogo import EscenaDialogo
                dialogo = [
                    "Anda, hay una puerta al final del pasillo...",
                    "Debería ir a investigar."
                ]
                juego.director.apilarEscena(EscenaDialogo(juego.director, dialogo, "voz_carlitos"))

class Dia3(EstadoProgresion):
    def __init__(self):
        self.audio = GestorAudio()

    def entrar(self, juego):
        juego.es_de_noche = False
        juego.tortillas_objetivo = 5 #cambiar
        juego.cocina.puntos = 0
        juego.cocina_bloqueada = True #cerramos a cociña de novo
        juego.actualizar_sala()

        self.audio.reproducir_sonido("m_buenos_dias_pichi")
        
        from escena_dialogo import EscenaDialogo
        dialogo = [
            "¡Pichi! Ayer te fuiste sin fregar.",
            f"Como castigo, hoy me vas a hacer {juego.tortillas_objetivo} tortillas.",
            "¡Venga, dale a esos huevos!"
        ]

        # Se usa callback para añadir diálogo tras el texto:
        def tras_dialogo3():
            self.audio.reproducir_sonido("m_risa_malevola")

        juego.director.apilarEscena(EscenaDialogo(juego.director, dialogo, "voz_michel", tras_dialogo3))

    def update(self, juego):
        if juego.cocina.puntos >= juego.tortillas_objetivo:
            from escena_dialogo import EscenaDialogo
            dialogo_fin = ["¡Por fin primo!", "Ya cayó la noche..."]
            def pasar_a_noche3():
                self.audio.reproducir_sonido("m_buenas_noches")
                juego.cambiar_estado(Noche3())
            juego.director.apilarEscena(EscenaDialogo(juego.director, dialogo_fin, "voz_michel", pasar_a_noche3))
            juego.cocina.puntos = 0

class Noche3(EstadoProgresion):
    def entrar(self, juego):
        juego.es_de_noche = True
        juego.cocina_bloqueada = False
        juego.actualizar_sala()

    def update(self, juego):
        pass

class EscenaMuerte(Escena):
    def __init__(self, director):
        super().__init__(director)
        self.audio = GestorAudio()
        
        pygame.mixer.music.stop()
        
        self.cronometro = 0
        self.fase = 0
        
        #variables control para as imaxes
        self.mostrar_michel_estatico = False 
        self.mostrar_pantalla_completa = False
        
        self.tiempo_golpe = 0 
        self.tiempo_silencio_final = 0
        self.dialogo_jumpscare_lanzado = False 
        self.escala_michel = 200 #tamaño inicial jumpscare
        
        #rutas imaxes
        HOME = os.path.dirname(__file__)
        
        ruta_michel_normal = os.path.join(HOME, "..", "assets", "graphics", "characters", "míchel", "michel_enfadao.png")
        ruta_jump = os.path.join(HOME, "..", "assets", "graphics", "characters", "míchel", "michel_jumpScare.png")
        ruta_fullscreen = os.path.join(HOME, "..", "assets", "graphics", "cinematica", "pantalla_de_inicio.jpg")


        try:
            #Michel estático
            img_temp = pygame.image.load(ruta_michel_normal).convert_alpha()
            self.img_michel_estatico = pygame.transform.scale(img_temp, (300, 300))
        except FileNotFoundError:
            print(f"AVISO: No se encontró {ruta_michel_normal}")
            self.img_michel_estatico = None

        try:
            #Michel Jumpscare
            self.img_michel_jumpscare = pygame.image.load(ruta_jump).convert_alpha()
        except FileNotFoundError:
            print(f"AVISO: No se encontró {ruta_jump}")
            self.img_michel_jumpscare = None

        try:
            #fondo de pantalla inicio
            self.img_fullscreen = pygame.image.load(ruta_fullscreen).convert_alpha()
            self.img_fullscreen = pygame.transform.scale(self.img_fullscreen, (ANCHO, ALTO))
        except FileNotFoundError:
            print(f"AVISO: No se encontró {ruta_fullscreen}")
            self.img_fullscreen = None

    def update(self, tiempo_pasado):
        self.cronometro += tiempo_pasado
        
        #fase 0: porta
        if self.fase == 0:
            self.audio.reproducir_sonido("abre_puerta") 
            self.fase = 1
            self.cronometro = 0
            
        #fase 1: pasos
        elif self.fase == 1 and self.cronometro > 1500:
            self.audio.reproducir_sonido("pasos_pasillo")
            self.fase = 2
            self.cronometro = 0
            
        #fase 2: silencio e primeiro diálogo
        elif self.fase == 2 and self.cronometro > 2000:
            self.fase = 3 
            
            from escena_dialogo import EscenaDialogo
            dialogo_previo = ["Te dije que no salieras de la cocina."]
            
            def jumpscare_michel():
                self.audio.reproducir_sonido("golpe_sarten")
                pygame.time.delay(600)
                self.tiempo_golpe = pygame.time.get_ticks()
                self.fase = 4 
                
            self.director.apilarEscena(EscenaDialogo(
                self.director, 
                dialogo_previo, 
                "voz_michel_grave", 
                callback_fin=jumpscare_michel, 
                color_texto=(200, 0, 0), 
                fondo_negro=True 
            ))

        #fase 4: pausa de 2s e segundo texto
        elif self.fase == 4 and not self.dialogo_jumpscare_lanzado:
            tiempo_actual = pygame.time.get_ticks()
            
            if (tiempo_actual - self.tiempo_golpe) >= 2000:
                self.audio.reproducir_musica("jumpscare_musica")
                self.mostrar_michel_estatico = True
                pygame.time.delay(1000)
                self.dialogo_jumpscare_lanzado = True 
                
                from escena_dialogo import EscenaDialogo
                dialogo_jumpscare = ["Me has roto el corazón, Carlitos.", "Yo solo te quería ayudar...", "Pero has husmeado donde no debías...", "Nunca debiste venir a estudiar a la FIC."]
                
                def iniciar_silencio_final():
                    self.mostrar_michel_estatico = False 
                    self.mostrar_pantalla_completa = True 
                    self.fase = 5
                    pygame.mixer.music.stop()
                    self._musica_sonando = None
                    self.tiempo_silencio_final = pygame.time.get_ticks()
                    
                self.director.apilarEscena(EscenaDialogo(
                    self.director, 
                    dialogo_jumpscare, 
                    "voz_michel_grave", 
                    callback_fin=iniciar_silencio_final, 
                    color_texto=(0, 0, 0),         
                    fondo_negro=False,             
                    color_fondo_caja=(200, 0, 0),  
                    color_borde_caja=(0, 0, 0)     
                ))

        #fase 5: 3 segundos de silencio
        elif self.fase == 5:
            if (pygame.time.get_ticks() - self.tiempo_silencio_final) >= 2000:
                self.fase = 6
                self.audio.reproducir_sonido("m_risa_malevola")

        #fase 6: jumpscare e feche do xogo
        elif self.fase == 6:
            #a imaxe crece 60 pixels por fotograma
            self.escala_michel += 60 
            
            #cando crezca de todo a imaxe, fechamos xogo
            if self.escala_michel > 2500:
                self.director.salirPrograma() 


    def eventos(self, lista_eventos):
        pass

    def dibujar(self, pantalla):
        pantalla.fill((0, 0, 0))
        
        #debuxar img a pantalla completa se estamos en fase 5 o 6
        if self.mostrar_pantalla_completa and self.img_fullscreen:
            pantalla.blit(self.img_fullscreen, (0, 0))
            
        #debuxar Michel normal en Fase 4
        if self.mostrar_michel_estatico and self.img_michel_estatico:
            rect_michel = self.img_michel_estatico.get_rect(center=(ANCHO // 2, ALTO // 2 - 50))
            pantalla.blit(self.img_michel_estatico, rect_michel)   
            
        #debuxar Michel jumpscare creciendo en fase 6
        if self.fase == 6 and self.img_michel_jumpscare:
            img_zoom = pygame.transform.scale(self.img_michel_jumpscare, (int(self.escala_michel), int(self.escala_michel)))
            rect_zoom = img_zoom.get_rect(center=(ANCHO // 2, ALTO // 2))
            pantalla.blit(img_zoom, rect_zoom)


class Juego(Escena):

    def __init__(self, director):
        Escena.__init__(self, director)
        self.audio = GestorAudio()

        #reprodúcese a música da cociña
        self.audio.reproducir_musica("cocina")
        
        self.fondo = pygame.image.load(FONDO_IMG).convert_alpha()
        self.fondo = pygame.transform.scale(self.fondo, (ANCHO_MAPA, ALTO_MAPA))

        self.fondo_pared = pygame.image.load(FONDO_IMG_PARED).convert_alpha()
        self.fondo_pared = pygame.transform.scale(self.fondo_pared, (ANCHO_MAPA, ALTO_MAPA))

        self.fondo_poster = pygame.image.load(FONDO_IMG_POSTER).convert_alpha()
        self.fondo_poster = pygame.transform.scale(self.fondo_poster, (ANCHO_MAPA, ALTO_MAPA))

        self.frente = pygame.image.load(FRENTE_IMG).convert_alpha()
        self.frente = pygame.transform.scale(self.frente, (ANCHO_MAPA, ALTO_MAPA))

        self.frente_clase1 = pygame.image.load(FRENTE_CLASE1).convert_alpha()
        self.frente_clase1 = pygame.transform.scale(self.frente_clase1, (ANCHO_MAPA, ALTO_MAPA))

        self.frente_pasllo = pygame.image.load(FRENTE_PASILLO).convert_alpha()
        self.frente_pasllo = pygame.transform.scale(self.frente_pasllo, (ANCHO_MAPA, ALTO_MAPA))

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

        self.sala_actual = "cocina" # Para gestionar las salas (audio)

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

        self.cocina = XestorCocina(self.jugador, GRAPHICS_FILE)

        self.zona_pizarra = pygame.Rect(1919, 2086, 80, 80) #pulsar e para interactuar coa pizarra
        self.pizarra_resuelta = False  #control de estado
        self.vidas_pizarra = 3

        #bloqueo da porta da aula ata resolver a pizarra
        self.puerta_aula = pygame.Rect(1245, 2140, 60, 150)
        self.aula_bloqueada = False

        #para noites na cociña
        self.zona_cuchara = pygame.Rect(635, 2800, 80, 80) 
        
        #maior tamaño para facilitar a interacción
        self.zona_agujero = pygame.Rect(750, 2880, 120, 150) 
        
        #burato cociña
        self.puerta_cocina = pygame.Rect(807, 2880, 60, 150)

        #bloqueo exterior laberinto
        self.bloqueo_laberinto = pygame.Rect(810, 1554, 45, 150)

        #porta saída final
        self.zona_salida = pygame.Rect(1015, 90, 80, 80)

        self.cocina_bloqueada = True
        self.tiene_cuchara = False
        self.agujero_excavado = False

        self._render_surf = pygame.Surface(
            (self.camara.ancho_cam, self.camara.alto_cam), pygame.SRCALPHA
        )

        #pre-cargar e pre-escalar a imaxe de cuberta de sala unha soa vez:
        bg_path = os.path.join(GRAPHICS_FILE, 'environments', 'background.png')
        if os.path.exists(bg_path):
            _bg_src = pygame.image.load(bg_path).convert_alpha()
            self._area_bg_imgs = [
                pygame.transform.scale(_bg_src, (sala.width, sala.height))
                for sala in self.salas
            ]
        else:
            self._area_bg_imgs = None
        
        # Control del fade in inicial
        self._fade_inicial = True
        self._fade_alpha = 255

        
        #configuración da máquina de estados
        self.es_de_noche = False
        self.tortillas_objetivo = 999 
        self.estado_actual = None
        
        self.juego_arrancado = False

        self.ayuda_pulsada_alguna_vez = False


        #patrón Comando: sistema de disparadores para lanzar diálogos ou eventos en función da posición do xogador, a cámara, e outros factores
        #funcións auxiliares para simplificar a creación dos disparadores, callbacks Patrón Comando
        def lanzar_dialogo(textos, voz="voz_narrador"):
            from escena_dialogo import EscenaDialogo
            self.audio.reproducir_sonido("burbuja_texto", self.audio.canal_ui)
            self.director.apilarEscena(EscenaDialogo(self.director, textos, voz))

        def evento_vuelta_cocina():
            self.debe_volver_a_cocina = False
            self.cambiar_estado(Dia3())

        self.disparadores = [
            #volver á cociña
            Disparador(
                condicion_func=lambda: getattr(self, 'debe_volver_a_cocina', False) and 
                                       self.obtener_sala_actual() == "cocina" and 
                                       self.jugador.hitbox.right < self.puerta_cocina.left and #só esiximos que se cruce a porta
                                       self.camara.esta_quieta_x(),                            #e que a cámara estea centrada
                callback_accion=evento_vuelta_cocina
            ),
            
            #diálogo aula da pizarra (depende de cámara X)
            Disparador(
                condicion_func=lambda: self.salas[1].collidepoint(self.jugador.hitbox.center) and 
                                       self.camara.esta_quieta_x(),
                callback_accion=lambda: lanzar_dialogo([
                    "Se escucha una voz que te dice al oído:", 
                    "Hasta que todos acaben el examen no podrás salir."
                ]),
                delay_ms=0
            ),

            #diálogo aula da pizarra (depende de cámara X)
            Disparador(
                condicion_func=lambda: self.room2_event.event_started and 
                                       self.camara.esta_quieta_x(),
                callback_accion=lambda: lanzar_dialogo([
                    "Escuchas como se cierra la puerta con pestillo detrás de ti.", 
                    "Pero parece que al final de esta habitación hay algo escondido, deberías investigar a ver que es."
                ]),
                delay_ms=0
            ),

            #diálogo ao saír do laberinto (depende de saír da porta da sala)
            Disparador(
                condicion_func=lambda: self.room2_event.key_collected and 
                                       not self.salas[2].collidepoint(self.jugador.hitbox.center) and 
                                       self.jugador.hitbox.left > (self.bloqueo_laberinto.right + 50),
                callback_accion=lambda: lanzar_dialogo([
                    "Ya tengo las 2 llaves.", 
                    "Debería ir a la puerta al final de este pasillo."
                ], voz="voz_carlitos")
            )
        ]


    def eventos(self, lista_eventos):
        if not self.es_de_noche:
            self.cocina.eventos(lista_eventos)
        for evento in lista_eventos:
            if evento.type == pygame.QUIT:
                self.director.salirPrograma()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.audio.reproducir_sonido("click_menu_bw", self.audio.canal_ui)
                    self.audio.cambiar_volumen_musica(VOL_MUSICA / 2) # Se atenúa el volúmen de la música al pausar
                    self.director.apilarEscena(MenuPausa(self.director))

                if evento.key == pygame.K_h:
                    self.audio.reproducir_sonido("click_menu_bw", self.audio.canal_ui)
                    #alternar aberto e fechado
                    self.cocina.tutorial_activo = not self.cocina.tutorial_activo
                    self.cocina.ayuda_pulsada_alguna_vez = True

                #cambiar
                if evento.key == pygame.K_t:
                    self.cocina.puntos += 1
                    self.audio.reproducir_sonido("campana", self.audio.canal_accion)

                #pizarra
                if evento.key in [pygame.K_e, pygame.K_x]:
                    self.jugador.play_one_shot(f'interact_{self.jugador.last_action_base}')
                    _surf = pygame.display.get_surface()
                    _reloj = pygame.time.Clock()
                    _interrupted = False
                    while self.jugador.one_shot_active:
                        for _ev in pygame.event.get(pygame.KEYDOWN):
                            if _ev.key in (pygame.K_e, pygame.K_x):
                                pygame.event.post(_ev)  # put it back for the outer loop
                                _interrupted = True
                                break
                            pygame.event.post(_ev)  # put back any other key
                        if _interrupted:
                            self.jugador.one_shot_active = False
                            break
                        self.sprites.update()
                        self.dibujar(_surf)
                        pygame.display.flip()
                        _reloj.tick(60)
                    if not _interrupted:
                        pygame.event.clear(pygame.KEYDOWN)
                    #condición 'not self.pizarra_resuelta' para que unha vez resuelta a pizarra, non se poida volver a interactuar con ela
                    if not self.pizarra_resuelta and self.zona_pizarra.colliderect(self.jugador.hitbox):
                        from escena_pizarra import EscenaPizarra
                        self.audio.reproducir_sonido("burbuja_texto", self.audio.canal_ui)

                        def restar_vida():
                            self.vidas_pizarra -= 1
                            
                        def penalizacion_fallo(vidas_restantes):
                            from escena_dialogo import EscenaDialogo

                            #paramos música
                            pygame.mixer.music.stop()
                            self._musica_sonando = None
                            pygame.time.delay(1000)
                            
                            #fallo 1, vidas = 2
                            if vidas_restantes == 2:
                                self.audio.reproducir_sonido("pasos_pasillo") 
                                dialogo = ["(Se escuchan pasos en el pasillo...)"]
                                self.director.apilarEscena(EscenaDialogo(self.director, dialogo, "voz_michel", color_texto=(255, 50, 50)))

                                self.nivel_tension = 1
                            
                            #fallo 2, vidas = 1
                            elif vidas_restantes == 1:
                                self.audio.reproducir_sonido("toc_toc") 
                                dialogo = ["(Escuchas a alguien en el pasillo, intentando abrir la puerta)"]
                                self.director.apilarEscena(EscenaDialogo(self.director, dialogo, "voz_michel", color_texto=(255, 50, 50)))

                                self.nivel_tension = 2
                        
                        #patrón Callback: pasamos 'self.superar_pizarra' a escena
                        escena_pizz = EscenaPizarra(self.director, self.vidas_pizarra, self.superar_pizarra, self.perder_juego, restar_vida, penalizacion_fallo)
                        self.director.apilarEscena(escena_pizz)

                    #culler (Solo Noche 1)
                    if isinstance(self.estado_actual, Noche1) and not self.tiene_cuchara and self.zona_cuchara.colliderect(self.jugador.hitbox):
                        from escena_dialogo import EscenaDialogo
                        self.audio.reproducir_sonido("coger_item", self.audio.canal_accion)
                        self.tiene_cuchara = True
                        dialogo = ["¡Has encontrado una cuchara sucia escondida!", "Quizás sirva para excavar en esa pared de la derecha..."]
                        self.director.apilarEscena(EscenaDialogo(self.director, dialogo, "voz_narrador"))

                    #pared/burato (Solo Noche 1)
                    if isinstance(self.estado_actual, Noche1) and self.zona_agujero.colliderect(self.jugador.hitbox):
                        from escena_dialogo import EscenaDialogo
                        if not self.tiene_cuchara:
                            self.audio.reproducir_sonido("burbuja_texto", self.audio.canal_ui)
                            dialogo = ["La pared de aquí parece frágil...", "Pero necesitas una herramienta para excavar."]
                            self.director.apilarEscena(EscenaDialogo(self.director, dialogo, "voz_narrador"))
                        else:
                            self.audio.reproducir_sonido("burbuja_texto", self.audio.canal_ui)
                            self.agujero_excavado = True
                            #Carlitos non pode escapar porque se fai de día
                            dialogo = [
                                "Te pasas toda la noche excavando con la cuchara...",
                                "¡Has hecho un agujero que da al misterioso pasillo!",
                                "Pero estás agotado y ya se ha hecho de día...",
                                "Escondes lo que hiciste con un póster de anime."
                            ]
                            def fin_excavar():
                                self.cambiar_estado(Dia2())
                            self.director.apilarEscena(EscenaDialogo(self.director, dialogo, "voz_narrador", fin_excavar))

                            
                    #diálogos de portas bloqueadas
                    #Noche 2: o laberinto está bloqueado
                    if isinstance(self.estado_actual, Noche2) and self.bloqueo_laberinto.inflate(20, 20).colliderect(self.jugador.hitbox):
                        from escena_dialogo import EscenaDialogo
                        self.audio.reproducir_sonido("burbuja_texto", self.audio.canal_ui)
                        dialogo = ["Debería explorar esta zona otro día."]
                        self.director.apilarEscena(EscenaDialogo(self.director, dialogo, "voz_carlitos"))

                    #Noche 3: a sala da pizarra está fechada
                    if isinstance(self.estado_actual, Noche3) and self.puerta_aula.inflate(20, 20).colliderect(self.jugador.hitbox):
                        from escena_dialogo import EscenaDialogo
                        self.audio.reproducir_sonido("burbuja_texto", self.audio.canal_ui)
                        dialogo = ["Aquí no tengo nada más que hacer."]
                        self.director.apilarEscena(EscenaDialogo(self.director, dialogo, "voz_carlitos"))

                    #laberinto rematado: mensaxe de ir ao final
                    if self.room2_event.key_collected and self.bloqueo_laberinto.inflate(20, 20).colliderect(self.jugador.hitbox):
                        from escena_dialogo import EscenaDialogo
                        self.audio.reproducir_sonido("burbuja_texto", self.audio.canal_ui)
                        dialogo = ["Aquí no tengo nada más que hacer."]
                        self.director.apilarEscena(EscenaDialogo(self.director, dialogo, "voz_carlitos"))


                    #porta final (escape)
                    if self.zona_salida.colliderect(self.jugador.hitbox):
                        from escena_dialogo import EscenaDialogo
                        from escena_cinematica_final import EscenaCinematicaFinal
                        
                        #comprobar se ten ambas chaves
                        if self.pizarra_resuelta and self.room2_event.key_collected:
                            self.audio.reproducir_sonido("burbuja_texto", self.audio.canal_ui)
                            # Mostrar cinemática final con Michel
                            self.director.apilarEscena(EscenaCinematicaFinal(self.director))
                        
                        #se falta algunha chave
                        else:
                            self.audio.reproducir_sonido("burbuja_texto", self.audio.canal_ui)
                            dialogo = [
                                "La puerta está en modo 'no molestar'.",
                                "Hay 2 cerrojos."
                            ]
                            self.director.apilarEscena(EscenaDialogo(self.director, dialogo, "voz_carlitos"))        

    
    # Se gestionan las salas en las que se encuentra el jugador (para audio, y quizá otros).
    # De momento, sólo es necesario saber si el jugador se encuentra o no en la cocina:
    def obtener_sala_actual(self):
            pos = self.jugador.hitbox.center

            if self.salas[0].collidepoint(pos):
                return "cocina"
            else:
                return "fuera_de_cocina"
            
            
    def actualizar_sala(self):
        nueva_sala = self.obtener_sala_actual()

        #lemos o nivel de tensión para decidir se a música de escape é máis intensa ou non, no caso da pizarra
        nivel = getattr(self, 'nivel_tension', 0)
        
        if nivel == 1:
            musica_objetivo = "dos_vidas_restantes" #2 vidas
        elif nivel == 2:
            musica_objetivo = "una_vida_restante" #1 vida
        else:
            #se está na cociña de noite soa a música de escape, senón a música de cociñado
            if nueva_sala == "cocina":
                musica_objetivo = "escape" if self.es_de_noche else "cocina"
            else:
                musica_objetivo = "escape"
            
        #comprobar qué música está soando realmente para non reiniciarla
        musica_actual = getattr(self, '_musica_sonando', None)
        
        if musica_objetivo != musica_actual:
            self.audio.reproducir_musica(musica_objetivo)
            self._musica_sonando = musica_objetivo
            
        self.sala_actual = nueva_sala   


    def cambiar_estado(self, nuevo_estado):
        #Patrón Estado: cambia o comportamento do xogo segundo se é noite ou día
        self.estado_actual = nuevo_estado
        self.estado_actual.entrar(self)    

    def superar_pizarra(self):
        #se executa unha vez o xogador resolva a pizarra
        self.pizarra_resuelta = True
        self.nivel_tension = 0

        from escena_dialogo import EscenaDialogo
        dialogo = [
            "¡Has conseguido la llave pizarra!",
            "Pero parece que está amaneciendo...",
            "Deberías volver rápido a la cocina, antes de que Michel te pille."
        ]
        self.director.apilarEscena(EscenaDialogo(self.director, dialogo, "voz_narrador"))
        
        #avisamos ao xogo que estamos na fase de volta á cociña
        self.debe_volver_a_cocina = True

    #game over ao non completar a pizarra
    def perder_juego(self):
        # ¡Arrancamos la secuencia cinemática de muerte!
        # Usamos cambiarEscena para destruir el juego por completo
        self.director.cambiarEscena(EscenaMuerte(self.director))


    def update(self, tiempo_pasado):
        #debuggeo
        #print(f"Posición de Carlitos -> X: {self.jugador.hitbox.x} | Y: {self.jugador.hitbox.y}")

        #arrancamos o Día 1 no primeiro fotograma, cando o Juego está xa na pantalla
        if not self.juego_arrancado:
            self.juego_arrancado = True
            self.cambiar_estado(Dia1())


        #a máquina de estados vixila se fixemos a tortillas
        if self.estado_actual:
            self.estado_actual.update(self)


        #comproba se o xogador está na aula
        en_aula = self.salas[1].collidepoint(self.jugador.hitbox.center)
        
        #para evitar que quede encerrado carlitos na porta
        paso_la_puerta = self.jugador.hitbox.centerx > (self.puerta_aula.right + 50)


        #se está na aula, cruzou a porta e non resolveu a pizarra
        if en_aula and paso_la_puerta and not self.pizarra_resuelta:
            self.aula_bloqueada = True
        #se xa a resolveu ou saíu da aula
        elif self.pizarra_resuelta or not en_aula:
            self.aula_bloqueada = False


        #actualizar as colisiones extra, engade a porta se bloqueada
        colisiones_extra = self.room2_event.get_extra_collision_rects()

        if self.aula_bloqueada or isinstance(self.estado_actual, Noche3): #se na Noche 3, fechamos aula para obligar a ir ao laberinto
            colisiones_extra.append(self.puerta_aula)

        #bloqueo cociña
        if self.cocina_bloqueada:
            colisiones_extra.append(self.puerta_cocina)    

        #bloqueo do laberinto
        en_laberinto = self.salas[2].collidepoint(self.jugador.hitbox.center)
        
        if isinstance(self.estado_actual, Noche2):
            colisiones_extra.append(self.bloqueo_laberinto)
            
        #na Noche 3, bloquéase só se tes a chave, saíches da sala e non estar a tocar o marco da porta
        elif self.room2_event.key_collected and not en_laberinto:
            if not self.jugador.hitbox.colliderect(self.bloqueo_laberinto):
                colisiones_extra.append(self.bloqueo_laberinto)   


        self.jugador.set_extra_collision_rects(colisiones_extra)

        self.sprites.update()
        focus_pos = self.room2_event.update(self.jugador, tiempo_pasado)

        self.camara.update(self.jugador, self.salas, focus_world_pos=focus_pos)
        if not self.es_de_noche:
            self.cocina.update(tiempo_pasado)

        #disparadores
        for disparador in self.disparadores:
            disparador.update(tiempo_pasado)    

        self.actualizar_sala()


    def dibujar(self, pantalla):
        pantalla.fill((0, 0, 0))
        

        # Ahora, la pantalla se dibuja y luego se escala correctamente:
        self._render_surf.fill((0, 0, 0, 0))
        if not self.agujero_excavado:
            fondo_actual = self.fondo_pared
        elif self.es_de_noche:
            fondo_actual = self.fondo
        else:
            fondo_actual = self.fondo_poster
        self._render_surf.blit(fondo_actual, self.camara.aplicar_rect(fondo_actual.get_rect()))
        self.room2_event.draw_objects(self._render_surf, self.camara)
        self.cocina.dibujar_highlight(self._render_surf, self.camara)
        self.cocina.dibujar_estaciones(self._render_surf, self.camara)

        for sprite in self.sprites:
            self._render_surf.blit(sprite.image, self.camara.aplicar(sprite))

        self.cocina.dibujar_item_en_man(self._render_surf, self.camara)

        self.room2_event.draw_front(self._render_surf, self.camara)

        self._render_surf.blit(self.frente, self.camara.aplicar_rect(self.frente.get_rect()))
        self.cocina.dibujar_highlight_frente(self._render_surf, self.camara)
        self.cocina.dibujar_bol_frente(self._render_surf, self.camara)
        self.cocina.dibujar_taboa_frente(self._render_surf, self.camara)
        self.cocina.dibujar_prato_frente(self._render_surf, self.camara)

        
        self._render_surf.blit(self.frente_pasllo, self.camara.aplicar_rect(self.frente_pasllo.get_rect()))

        sala_clase1 = self.salas[1]  # Sala del medio derecha
        if sala_clase1.collidepoint(self.jugador.hitbox.center):
            self._render_surf.blit(self.frente_clase1, self.camara.aplicar_rect(self.frente_clase1.get_rect()))

        if DEBUG_COLISION_MAPA:
            self._render_surf.blit(
                self.colision_debug_overlay,
                self.camara.aplicar_rect(self.colision_debug_overlay.get_rect())
            )
            self.colision_debug_overlay.set_alpha(80)

            #puerta aula tipo test (AZUL) 
            rect_cam_puerta = self.camara.aplicar_rect(self.puerta_aula)
            pygame.draw.rect(self._render_surf, (0, 0, 255), rect_cam_puerta, 3)
            
            #zona para pulsar a E da pizarra (ROJO)
            rect_cam_pizarra = self.camara.aplicar_rect(self.zona_pizarra)
            pygame.draw.rect(self._render_surf, (255, 0, 0), rect_cam_pizarra, 3)

            #rectángulo verde para a culler
            rect_cam_cuchara = self.camara.aplicar_rect(self.zona_cuchara)
            pygame.draw.rect(self._render_surf, (0, 255, 0), rect_cam_cuchara, 3)
            
            #rectángulo amarelo para o burato
            rect_cam_agujero = self.camara.aplicar_rect(self.zona_agujero)
            pygame.draw.rect(self._render_surf, (255, 255, 0), rect_cam_agujero, 3)

            #rectángulo morado para bloquear o Laberinto
            rect_cam_lab = self.camara.aplicar_rect(self.bloqueo_laberinto)
            pygame.draw.rect(self._render_surf, (255, 0, 255), rect_cam_lab, 3)

            #rectángulo cian para a porta Final
            rect_cam_salida = self.camara.aplicar_rect(self.zona_salida)
            pygame.draw.rect(self._render_surf, (0, 255, 255), rect_cam_salida, 3)

        self.room2_event.draw_light_overlay(self._render_surf, self.camara, self.jugador)

        # Cubrir as salas onde o xogador NON está (dentro de _render_surf, antes de escalar):
        if self._area_bg_imgs:
            for sala, area_img in zip(self.salas, self._area_bg_imgs):
                if not sala.collidepoint(self.jugador.hitbox.center):
                    self._render_surf.blit(area_img, self.camara.aplicar_rect(sala))

        self.cocina.dibujar(self._render_surf, self.camara)

        #efecto de destello na cuchara
        if isinstance(self.estado_actual, Noche1) and not self.tiene_cuchara:
            tiempo = pygame.time.get_ticks()
            alpha_brillo = int((math.sin(tiempo * 0.005) + 1) * 75) + 50
            
            #debuxa unha pequeña luz amarela
            surf_luz = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(surf_luz, (255, 255, 100, alpha_brillo), (20, 20), 15) #halo
            pygame.draw.circle(surf_luz, (255, 255, 255, alpha_brillo + 50), (20, 20), 5) #centro brillante
            
            rect_brillo = self.camara.aplicar_rect(self.zona_cuchara)
            self._render_surf.blit(surf_luz, (rect_brillo.centerx - 20, rect_brillo.centery - 20))

        # La resolución anterior se escala al tamaño real de la pantalla
        scaled_surface = pygame.transform.scale(self._render_surf, (ANCHO, ALTO))
        pantalla.blit(scaled_surface, (0, 0))


        if self.es_de_noche:
            overlay = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
            overlay.fill((12, 4, 33, 180)) 
            pantalla.blit(overlay, (0, 0))
        else:
            #filtro suave para baixar o brillo de día
            overlay_dia = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
            overlay_dia.fill((0, 0, 0, 70)) 
            pantalla.blit(overlay_dia, (0, 0))    

        # Fade in inicial al empezar el juego
        if self._fade_inicial:
            fade_surface = pygame.Surface(pantalla.get_size())
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(self._fade_alpha)
            pantalla.blit(fade_surface, (0, 0))
            self._fade_alpha -= 5
            if self._fade_alpha <= 0:
                self._fade_inicial = False
        
        self.cocina.dibujar_tutorial(pantalla, self.camara)
