import pygame
import os
from escena import Escena, ANCHO, ALTO
from sprtesheet import SpriteSheet
from gestorAudio import GestorAudio

class EscenaCinematicaFinal(Escena):
    def __init__(self, director):
        super().__init__(director)
        self.audio = GestorAudio()
        
        HOME = os.path.dirname(__file__)
        GRAPHICS_FILE = os.path.join(HOME, "..", "assets", "graphics")
        MICHEL_SHEET = os.path.join(GRAPHICS_FILE, "characters", "míchel", "michel_sheet.png")
        
        self.scale = 4 * 1.8  
        self.michel_loaded = False
        self.michel_frames = []  
        self.michel_image = None  
        
        try:
            sprite_sheet = SpriteSheet(MICHEL_SHEET)
            raw_frames = sprite_sheet.load_strip((0, 0, 16, 16), 4)
            
            for frame in raw_frames:
                w = int(frame.get_width() * self.scale)
                h = int(frame.get_height() * self.scale)
                scaled = pygame.transform.scale(frame, (w, h))
                self.michel_frames.append(scaled)
            
            self.michel_loaded = True
        except Exception as e:
            print(f"Error cargando spritesheet: {e}")
            try:
                img = pygame.image.load(MICHEL_SHEET).convert_alpha()
                w = int(img.get_width() * 2)
                h = int(img.get_height() * 2)
                self.michel_image = pygame.transform.scale(img, (w, h))
                self.michel_loaded = True
            except:
                self.michel_loaded = False
        
        self.juego = None
        if len(director.pila) > 1:
            self.juego = director.pila[-2]
        
        # variables de animación de Michel
        self.michel_x = ANCHO // 2 - 40  
        self.michel_y = ALTO + 100 
        self.michel_velocity = 12 
        self.michel_frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 0.15
        self.tiempo_total = 0
        self.fase = "dialogo_inicial" 
        self.tiempo_fase = 0
        self.dialogo_mostrado = False
        self.dialogo_texto = "¡ESPERAAAAAA!"
        self.personaje_girado = False
        self.caracteres_mostrados = 0
        self.velocidad_escritura = 0.1
        self.caracter_anterior = 0
        self.fade_alpha = 0
    
    def eventos(self, lista_eventos):
        """Permite avanzar en los diálogos o en la cinemática"""
        for evento in lista_eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
                if self.fase == "dialogo_inicial":
                    self.fase = "giro_personaje"
                    self.tiempo_fase = 0
                    self.dialogo_mostrado = False
                elif self.fase in ["corriendo", "pausa"]:
                    self.fase = "captura_dialogo"
                    self.tiempo_fase = 0
                    self.dialogo_mostrado = False
                elif self.fase == "captura_dialogo":
                    self.fase = "fade_out"
                    self.tiempo_fase = 0
    
    def update(self, tiempo_pasado):
        """Actualiza la cinemática"""
        if not self.michel_loaded:
            self.director.salirEscena()
            return
        
        self.tiempo_total += tiempo_pasado
        self.tiempo_fase += tiempo_pasado
        
        if self.fase == "dialogo_inicial":
            if self.tiempo_fase < 500: 
                pass
            else:
                self.dialogo_mostrado = True
                if self.caracteres_mostrados < len(self.dialogo_texto):
                    self.caracteres_mostrados += self.velocidad_escritura * tiempo_pasado
            
            if self.tiempo_fase >= 5000:
                self.fase = "giro_personaje"
                self.tiempo_fase = 0
                self.dialogo_mostrado = False
        
        elif self.fase == "giro_personaje":
            if self.juego and not self.personaje_girado:
                self.juego.jugador.last_action_base = 'down'
                self.juego.jugador.current_animation = 'idle_down'
                self.juego.jugador.facing_right = True
                self.personaje_girado = True
            
            if self.tiempo_fase >= 500:
                self.fase = "corriendo"
                self.tiempo_fase = 0
        
        elif self.fase == "corriendo":
            self.michel_y -= self.michel_velocity
            
            self.animation_timer += tiempo_pasado / 1000.0
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.michel_frame_index = (self.michel_frame_index + 1) % len(self.michel_frames)
            
            if self.michel_y <= ALTO // 3:
                self.fase = "pausa"
                self.tiempo_fase = 0
        
        elif self.fase == "pausa":
            if self.tiempo_fase >= 800:
                self.fase = "captura_dialogo"
                self.tiempo_fase = 0
        
        elif self.fase == "captura_dialogo":
            if self.tiempo_fase < 300:
                pass
            else:
                self.dialogo_mostrado = True
                self.dialogo_texto = "¡Fuiste atrapado!"
            
            if self.tiempo_fase >= 4000:
                self.fase = "fade_out"
                self.tiempo_fase = 0
        
        elif self.fase == "fade_out":
            fade_progress = min(1.0, self.tiempo_fase / 2000.0)
            self.fade_alpha = int(255 * fade_progress)
            
            if fade_progress >= 1.0:
                from menuInicio import MenuPrincipal
                self.director.salirEscena()
                self.director.cambiarEscena(MenuPrincipal(self.director))
    
    def dibujar(self, pantalla):
        if len(self.director.pila) > 1:
            for i in range(len(self.director.pila) - 1, -1, -1):
                escena = self.director.pila[i]
                if escena.__class__.__name__ == 'Juego':
                    es_de_noche_original = escena.es_de_noche
                    escena.es_de_noche = False
                    escena.dibujar(pantalla)
                    escena.es_de_noche = es_de_noche_original
                    break
        
        if self.michel_loaded and self.fase not in ["dialogo_inicial", "giro_personaje"]:
            if self.michel_frames:
                if self.michel_frame_index < len(self.michel_frames):
                    frame = self.michel_frames[self.michel_frame_index]
                    pantalla.blit(frame, (int(self.michel_x), int(self.michel_y)))
            elif self.michel_image:
                pantalla.blit(self.michel_image, (int(self.michel_x), int(self.michel_y)))
        
        overlay = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
        overlay.fill((12, 4, 33, 180))  
        pantalla.blit(overlay, (0, 0))
        
        if self.dialogo_mostrado and self.fase == "dialogo_inicial":
            HOME = os.path.dirname(__file__)
            FONT_FILE = os.path.join(HOME, "..", "assets", "fonts", "PressStart2P-Regular.ttf")
            try:
                font = pygame.font.Font(FONT_FILE, 14)
            except:
                font = pygame.font.Font(None, 14)
            
            caja_rect = pygame.Rect(40, ALTO - 140, ANCHO - 80, 120)
            pygame.draw.rect(pantalla, (40, 40, 60), caja_rect, border_radius=10)
            pygame.draw.rect(pantalla, (255, 215, 0), caja_rect, 3, border_radius=10)
            
            caracteres_mostrados_int = int(self.caracteres_mostrados)
            texto_a_mostrar = self.dialogo_texto[:caracteres_mostrados_int]
            texto_surf = font.render(texto_a_mostrar, True, (240, 240, 240))
            pantalla.blit(texto_surf, (caja_rect.x + 20, caja_rect.y + 20))
            
            if caracteres_mostrados_int >= len(self.dialogo_texto):
                try:
                    font_ind = pygame.font.Font(FONT_FILE, 14)
                except:
                    font_ind = pygame.font.Font(None, 14)
                ind_render = font_ind.render("ESPACIO", True, (200, 200, 200))
                pantalla.blit(ind_render, (caja_rect.right - 120, caja_rect.bottom - 25))
        
        if self.dialogo_mostrado and self.fase == "captura_dialogo":
            HOME = os.path.dirname(__file__)
            FONT_FILE = os.path.join(HOME, "..", "assets", "fonts", "PressStart2P-Regular.ttf")
            try:
                font = pygame.font.Font(FONT_FILE, 24)
            except:
                font = pygame.font.Font(None, 24)
            
            texto_surf = font.render("¡Fuiste atrapado!", False, (255, 100, 100))
            texto_rect = texto_surf.get_rect(center=(ANCHO // 2, ALTO // 3))
            pantalla.blit(texto_surf, texto_rect)
        
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface((ANCHO, ALTO))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(self.fade_alpha)
            pantalla.blit(fade_surf, (0, 0))
