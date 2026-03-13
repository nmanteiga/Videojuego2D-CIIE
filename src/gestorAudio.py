import pygame
import os

HOME = os.path.dirname(__file__)
ASSESTS_FILE = os.path.join(HOME, "..", "assets")
SOUNDS_FILE = os.path.join(ASSESTS_FILE, "sounds")
SFX_FILE = os.path.join(SOUNDS_FILE, "sfx")
MUSIC_FILE = os.path.join(SOUNDS_FILE, "music")

# Volumen por defecto de los efectos de sonido y la música:
VOL_SFX = 1.0
VOL_MUSICA = 0.6

# Gestor de audio para todo el proyecto:
class GestorAudio:
    _instance = None # Instancia única

    # Se usa el patrón Singleton para que solo haya una instancia global de audio:
    def __new__(cls):
        if cls._instance is None:

            # Se inicializa el mixer, si aún no se hubiese hecho:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100, 16, 2, 4096)
                pygame.mixer.init()
            
            cls._instance = super().__new__(cls)
            cls._instance._inicializado = False
        return cls._instance

    def __init__(self):
        # Se comprueba si "_inicializado" ya existe. En ese caso, se sale de "__init__" inmediatamente:
        if getattr(self, "_inicializado", False):
            return
        self._inicializado = True
        
        # Ajusta el volumen de los sonidos (sfx) y la música:
        self.volumen_sfx = VOL_SFX
        self.volumen_musica = VOL_MUSICA

        self.sonidos = {} # Diccionario de sonidos
        self.musica = {} # Diccionario de música
        self.musica_actual = None # Canción sonando actualmente

        # Carga de sonidos:
        self.cargar_sonido("click_menu_fw", os.path.join(SFX_FILE, "click_menu_fw.wav")) # UI
        self.cargar_sonido("click_menu_bw", os.path.join(SFX_FILE, "click_menu_bw.wav"))
        self.cargar_sonido("click_menu_big", os.path.join(SFX_FILE, "click_menu_big.wav"))
        self.cargar_sonido("burbuja_texto", os.path.join(SFX_FILE, "burbuja_texto.wav"))
        self.cargar_sonido("pasos", os.path.join(SFX_FILE, "footsteps.wav")) # Movimiento del personaje
        self.cargar_sonido("coger_item", os.path.join(SFX_FILE, "coger_item.wav")) # Interacciones
        self.cargar_sonido("dejar_item", os.path.join(SFX_FILE, "dejar_item.wav"))
        self.cargar_sonido("cortar", os.path.join(SFX_FILE, "cortar.wav")) # Cocina
        self.cargar_sonido("batir", os.path.join(SFX_FILE, "batir.wav"))
        self.cargar_sonido("hervir", os.path.join(SFX_FILE, "boiling.wav"))
        self.cargar_sonido("campana", os.path.join(SFX_FILE, "campana.wav"))
        self.cargar_sonido("voz_narrador", os.path.join(SFX_FILE, "blip_narrador.wav")) # Voces (blips)
        self.cargar_sonido("voz_michel", os.path.join(SFX_FILE, "blip_michel.wav"))
        self.cargar_sonido("voz_michel_grave", os.path.join(SFX_FILE, "blip_michel_grave.wav"))
        self.cargar_sonido("voz_carlitos", os.path.join(SFX_FILE, "blip_carlitos.wav"))
        self.cargar_sonido("golpe_sarten", os.path.join(SFX_FILE, "golpe_sarten.wav")) # Cutscene inicial
        self.cargar_sonido("m_buenos_dias_papi", os.path.join(SFX_FILE, "michel_buenos_dias_papi.wav")) # Frasecitas de Michel
        self.cargar_sonido("m_buenos_dias_pichi", os.path.join(SFX_FILE, "michel_buenos_dias_pichi.wav"))
        self.cargar_sonido("m_buenas_noches", os.path.join(SFX_FILE, "michel_buenas_noches.wav"))
        self.cargar_sonido("m_una_tortillita", os.path.join(SFX_FILE, "michel_una_tortillita.wav"))
        self.cargar_sonido("m_risa_malevola", os.path.join(SFX_FILE, "michel_risa_malevola.wav"))
        self.cargar_sonido("m_amenaza", os.path.join(SFX_FILE, "michel_te_amenaza.wav"))
        self.cargar_sonido("m_risa_malevola_final", os.path.join(SFX_FILE, "michel_risa_malevola_slowdown&reverb.wav")) # Fue divertido hacer esto
        self.cargar_sonido("pasos_pasillo", os.path.join(SFX_FILE, "pasos_caseros.wav"))
        self.cargar_sonido("toc_toc", os.path.join(SFX_FILE, "629987__flem0527__knocking-on-wood-door-1.wav"))
        self.cargar_sonido("abre_puerta", os.path.join(SFX_FILE, "15419__pagancow__dorm-door-opening.wav"))



        # Diccionario de música. La música no se carga directamente:
        self.musica["cocina"] = os.path.join(MUSIC_FILE, "Cocina.mp3")
        self.musica["escape"] = os.path.join(MUSIC_FILE, "Escape.mp3")
        self.musica["cafeteria"] = os.path.join(MUSIC_FILE, "ambiente_cafeteria.mp3")
        self.musica["parada_bus"] = os.path.join(MUSIC_FILE, "ambiente_parada_bus.mp3")
        self.musica["una_vida_restante"] = os.path.join(MUSIC_FILE, "175205__minigunfiend__scary-creaking-knocking-wood.wav")
        self.musica["dos_vidas_restantes"] = os.path.join(MUSIC_FILE, "Scary-Monster.flac")
        self.musica["jumpscare_musica"] = os.path.join(MUSIC_FILE, "Scary Ambient Wind.ogg")

        # Reserva de canales:
        pygame.mixer.set_reserved(4) # Número de canales reservados
        self.canal_ui = pygame.mixer.Channel(0) # Interfaz de Usuario (UI)
        self.canal_personaje = pygame.mixer.Channel(1) # Personaje principal (pasos...)
        self.canal_accion = pygame.mixer.Channel(2) # Acciones del personaje (coger ítems, dejar ítems...)
        self.canal_texto = pygame.mixer.Channel(3) # Texto y diálogo (cinemática inicial...). NO voces de Michel
    
    # Cargar un sonido usando "pygame.mixer.Sound":
    def cargar_sonido(self, nombre, ruta):
        sonido = pygame.mixer.Sound(ruta)
        sonido.set_volume(self.volumen_sfx)
        self.sonidos[nombre] = sonido # Tras cargar el sonido, este se añade al diccionario

    # Reproducir un sonido, si está disponible:
    def reproducir_sonido(self, nombre, canal = None, loops = 0, fadein = 0):
        if nombre in self.sonidos:
            if canal is not None: # Si se ha especificado un canal
                canal.play(self.sonidos[nombre], loops, fade_ms = fadein)
            else:
                self.sonidos[nombre].play(loops, fade_ms = fadein)
    
    # Reproducir música, si está disponible:
    def reproducir_musica(self, nombre, loops = -1, fadein = 0):
        if nombre in self.musica:
            musica = self.musica[nombre]
            pygame.mixer.music.load(musica)
            pygame.mixer.music.set_volume(self.volumen_musica)

            # Por defecto, la música se reproduce en bucle y sin fade-in:
            pygame.mixer.music.play(loops, fade_ms = fadein)
            self.musica_actual = nombre
    
    # Pausar la música actual, sin perder la posición:
    def pausar_musica(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
    
    # Reanuda la música actual:
    def reanudar_musica(self):
        pygame.mixer.music.unpause()
    
    # Detener la música actual:
    def detener_musica(self, fadeout = 1000):
        if pygame.mixer.music.get_busy():

            # Por defecto, la música se detiene con un fade-out de 1000ms:
            pygame.mixer.music.fadeout(fadeout)
            self.musica_actual = None
    
    # Cambia el volúmen actual de la música:
    def cambiar_volumen_musica(self, volumen):
        volumen = max(0.0, min(1.0, volumen)) # Evita que el volumen esté fuera de 0 y 1
        self.volumen_musica = volumen
        pygame.mixer.music.set_volume(self.volumen_musica)