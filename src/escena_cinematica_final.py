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
        UI_FILE = os.path.join(HOME, "..", "assets", "graphics", "ui")
        MICHEL_SHEET = os.path.join(GRAPHICS_FILE, "characters", "míchel", "michel_sheet.png")
        CINEMATICA_FINAL_IMG = os.path.join(UI_FILE, "cinematica_final.png")
        
        # cargamos la fotillo del final si o si y si no nos quejamos
        self.cinematica_final_image = None
        try:
            img = pygame.image.load(CINEMATICA_FINAL_IMG).convert()
            self.cinematica_final_image = pygame.transform.scale(img, (ANCHO, ALTO))
        except Exception as e:
            print(f"Error cargando cinematica_final.png: {e}")
        
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
        
        # dnd sale michel corriendo 
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
        self.velocidad_escritura = 0.05
        self.caracter_anterior = 0
        self.fade_alpha = 0
        
        # textos de cinemática final
        self.textos_negro = [
            "Michel consiguió atrapar a Carlitos justo antes de poder escapar.",
            "Michel no quería que Carlitos volviera a escaparse...",
            "... así que se lo entregó a la facultad y decidieron ponerlo a hacer el peor de los trabajos...",
            "Le pusieron a revisar las guías docentes de la FIC hasta el final de sus días."
        ]
        self.indice_texto_negro = 0

        self.audio_m_reproducido = False # chequeo para audio 
        self.tiempo_pasos = 100 # sonido pisadas d michel cuando corre:
        self.intervalo_pasos = 200
    
    def eventos(self, lista_eventos):
        for evento in lista_eventos:
            if evento.type == pygame.QUIT:
                self.director.salirPrograma()
                
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
                    self.fase = "texto_negro_1"
                    self.tiempo_fase = 0
                elif self.fase in ["texto_negro_1", "texto_negro_2", "texto_negro_3", "texto_negro_4"]:
                    # bloqueo la barra espaciadora hasta q salga la frase entera para q no se raye
                    if self.fase == "texto_negro_1" and self.caracteres_mostrados >= len(self.textos_negro[0]):
                        self.fase = "texto_negro_2"
                        self.tiempo_fase = 0
                        self.caracteres_mostrados = 0
                    elif self.fase == "texto_negro_2" and self.caracteres_mostrados >= len(self.textos_negro[1]):
                        self.fase = "texto_negro_3"
                        self.tiempo_fase = 0
                        self.caracteres_mostrados = 0
                    elif self.fase == "texto_negro_3" and self.caracteres_mostrados >= len(self.textos_negro[2]):
                        self.fase = "texto_negro_4"
                        self.tiempo_fase = 0
                        self.caracteres_mostrados = 0
                    elif self.fase == "texto_negro_4" and self.caracteres_mostrados >= len(self.textos_negro[3]):
                        self.fase = "imagen_sin_textbox"
                        self.tiempo_fase = 0
                    self.dialogo_mostrado = False
    
    def update(self, tiempo_pasado):
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

            # pisaditas de michel
            self.tiempo_pasos += tiempo_pasado
            if self.tiempo_pasos >= self.intervalo_pasos:
                self.audio.reproducir_sonido("pasos")
                self.tiempo_pasos = 0
            
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
            if not self.audio_m_reproducido: # q hable solo una vez 
                self.audio.reproducir_sonido("m_amenaza")
                self.audio_m_reproducido = True

            # cuando lo pilla al fundido negro y los textitos
            if self.tiempo_fase >= 1000:
                self.fase = "texto_negro_1"
                self.tiempo_fase = 0
                self.dialogo_mostrado = False
                self.caracteres_mostrados = 0  # reinicia para q pinte bien la frase
        
        elif self.fase == "texto_negro_1":
            if self.tiempo_fase < 300:
                pass
            else:
                self.dialogo_mostrado = True
                if self.caracteres_mostrados < len(self.textos_negro[0]):
                    self.caracteres_mostrados += self.velocidad_escritura * tiempo_pasado

        elif self.fase == "texto_negro_2":
            self.audio_m_reproducido = False # reseteando para volver a usar

            if self.tiempo_fase < 300:
                pass
            else:
                self.dialogo_mostrado = True
                if self.caracteres_mostrados < len(self.textos_negro[1]):
                    self.caracteres_mostrados += self.velocidad_escritura * tiempo_pasado

        elif self.fase == "texto_negro_3":
            # pintamos las letras poco a poco
            if self.tiempo_fase < 300:
                pass
            else:
                self.dialogo_mostrado = True
                if self.caracteres_mostrados < len(self.textos_negro[2]):
                    self.caracteres_mostrados += self.velocidad_escritura * tiempo_pasado

        elif self.fase == "texto_negro_4":
            # pintamos las letras poco a poco
            if self.tiempo_fase < 300:
                pass
            else:
                self.dialogo_mostrado = True
                if self.caracteres_mostrados < len(self.textos_negro[3]):
                    self.caracteres_mostrados += self.velocidad_escritura * tiempo_pasado
        
        elif self.fase == "imagen_sin_textbox":
            if not self.audio_m_reproducido: # para q no suene doble
                self.audio.reproducir_sonido("m_risa_malevola_final")
                self.audio_m_reproducido = True

            # unos segundos de espera para darle drama
            if self.tiempo_fase >= 3000:
                self.fase = "fade_out_final"
                self.tiempo_fase = 0
        
        elif self.fase == "fade_out_final":
            # fundido negro para acabar
            fade_progress = min(1.0, self.tiempo_fase / 2000.0)
            self.fade_alpha = int(255 * fade_progress)
            
            if fade_progress >= 1.0:
                from menuInicio import MenuPrincipal
                self.director.salirEscena()
                self.director.cambiarEscena(MenuPrincipal(self.director))
    
    def dibujar(self, pantalla):
        # dibuja el fondo de detras solo cuando aun estan corriendo
        if self.fase in ["dialogo_inicial", "giro_personaje", "corriendo", "pausa", "captura_dialogo"]:
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
        
        # partes con la pantalla en negro (salen cajitas de texto)
        if self.fase in ["texto_negro_1", "texto_negro_2", "texto_negro_3", "texto_negro_4"]:
            pantalla.fill((0, 0, 0))
        
        # al final sale la foto 
        if self.fase in ["imagen_sin_textbox"]:
            pantalla.fill((0, 0, 0))  # borro todo y pongo en nero
            if self.cinematica_final_image:
                pantalla.blit(self.cinematica_final_image, (0, 0))
        
        # pintamos los textitos poco a poco como en pokemon
        if self.fase in ["texto_negro_1", "texto_negro_2", "texto_negro_3", "texto_negro_4"] and self.dialogo_mostrado:
            HOME = os.path.dirname(__file__)
            FONT_FILE = os.path.join(HOME, "..", "assets", "fonts", "PressStart2P-Regular.ttf")
            try:
                font = pygame.font.Font(FONT_FILE, 14)
            except:
                font = pygame.font.Font(None, 14)
            
            # cogemos el texto que toque
            if self.fase == "texto_negro_1":
                texto_actual = self.textos_negro[0]
            elif self.fase == "texto_negro_2":
                texto_actual = self.textos_negro[1]
            elif self.fase == "texto_negro_3":
                texto_actual = self.textos_negro[2]
            else:  # texto_negro_4
                texto_actual = self.textos_negro[3]
            
            caja_rect = pygame.Rect(40, ALTO - 120, ANCHO - 80, 100)
            pygame.draw.rect(pantalla, (40, 40, 60), caja_rect, border_radius=10)
            pygame.draw.rect(pantalla, (255, 215, 0), caja_rect, 3, border_radius=10)
            
            # separar texto para que no se salga de la caja (igual que que en escena_dialogo)
            max_ancho_texto = caja_rect.width - 40
            palabras = texto_actual.split(' ')
            linas = []
            lina_actual = ""
            
            for palabra in palabras:
                proba_lina = lina_actual + palabra + " " if lina_actual else palabra + " "
                if font.size(proba_lina)[0] <= max_ancho_texto:
                    lina_actual = proba_lina
                else:
                    if lina_actual:
                        linas.append(lina_actual.rstrip())
                    lina_actual = palabra + " "
            
            if lina_actual:
                linas.append(lina_actual.rstrip())
            
            # escribir poquito a poco lineas (copiado y pegao del dialogo)
            caracteres_restantes = int(self.caracteres_mostrados)
            espazamento_linas = 8
            y_offset = 0
            
            for lina in linas:
                if caracteres_restantes <= 0:
                    break
                
                # dibuja solo lo q toque
                texto_lina = lina[:caracteres_restantes]
                caracteres_restantes -= len(lina)
                
                render = font.render(texto_lina, True, (240, 240, 240))
                pantalla.blit(render, (caja_rect.x + 20, caja_rect.y + 20 + y_offset))
                y_offset += render.get_height() + espazamento_linas
            
            # chivato de pulsar espacio cuando acabe
            if self.caracteres_mostrados >= len(texto_actual):
                ind_render = font.render("ESPACIO", True, (200, 200, 200))
                pantalla.blit(ind_render, (caja_rect.right - 120, caja_rect.bottom - 25))
        
        # cuadros de texto del principio
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
            pass
        
        # fade a negro
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface((ANCHO, ALTO))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(self.fade_alpha)
            pantalla.blit(fade_surf, (0, 0))
