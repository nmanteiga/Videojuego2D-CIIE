import pygame
import sys
import time
import os
from gestorAudio import GestorAudio

HOME = os.path.dirname(__file__)
FONT_FILE = os.path.join(HOME, "..", "assets", "fonts", "PressStart2P-Regular.ttf")
ASSETS_PATH = os.path.join(HOME, "..", "assets")

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
LINE_SPACING = 8  
WHITE = (240, 240, 240)
BLACK = (0, 0, 0)

screen = None
font = None
BACKGROUND_IMG = None
CHARACTER_IMG = None
ITEM_IMG = None
audio = None

#excepción para saltar cinemáticas
class SaltarCinematica(Exception):
    pass

def check_skip(): 
    teclas = pygame.key.get_pressed()
    if teclas[pygame.K_ESCAPE]:
        raise SaltarCinematica()
    
def tempo_espera(ms):
    tiempo_fin = pygame.time.get_ticks() + ms
    while pygame.time.get_ticks() < tiempo_fin:
        check_skip()
        pygame.time.delay(10)



def init_cinematics(pantalla):
    global screen, font, BACKGROUND_IMG, audio
    screen = pantalla
    font = pygame.font.Font(FONT_FILE, 14)
    img = pygame.image.load(os.path.join(ASSETS_PATH, "graphics", "cinematica", "bus1.png")).convert()
    BACKGROUND_IMG = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    audio = GestorAudio()

def set_background(image_path):
    global BACKGROUND_IMG
    img = pygame.image.load(image_path).convert()
    BACKGROUND_IMG = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))

def set_black_background():
    global BACKGROUND_IMG
    BACKGROUND_IMG = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    BACKGROUND_IMG.fill(BLACK)

def set_character(image_path, scale=4):
    global CHARACTER_IMG
    if image_path is None:
        CHARACTER_IMG = None
        return
    img = pygame.image.load(image_path).convert_alpha()
    w, h = img.get_width() * scale, img.get_height() * scale
    CHARACTER_IMG = pygame.transform.scale(img, (w, h))

def set_item(image_path, scale=1):
    global ITEM_IMG
    if image_path is None:
        ITEM_IMG = None
        return
    img = pygame.image.load(image_path).convert_alpha()
    w, h = int(img.get_width() * scale), int(img.get_height() * scale)
    ITEM_IMG = pygame.transform.scale(img, (w, h))

def clear_character():
    global CHARACTER_IMG
    CHARACTER_IMG = None

def clear_item():
    global ITEM_IMG
    ITEM_IMG = None

# Fade functions
def fade_in(surface, speed=4):
    fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade.fill((0, 0, 0))
    for alpha in range(255, -1, -speed):
        fade.set_alpha(alpha)
        surface.blit(BACKGROUND_IMG, (0, 0))
        surface.blit(fade, (0, 0))
        pygame.display.flip()
        tempo_espera(10)

def fade_out(surface, speed=4):
    fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade.fill((0, 0, 0))
    for alpha in range(0, 256, speed):
        fade.set_alpha(alpha)
        surface.blit(BACKGROUND_IMG, (0, 0))
        surface.blit(fade, (0, 0))
        pygame.display.flip()
        tempo_espera(10)

def show_item_from_bottom(image_path, scale=1, rise_speed=5, hold_time=2000):
    img = pygame.image.load(image_path).convert_alpha()
    w, h = int(img.get_width() * scale), int(img.get_height() * scale)
    item = pygame.transform.scale(img, (w, h))
    
    item_x = (SCREEN_WIDTH - w) // 2
    final_y = SCREEN_HEIGHT - h  
    start_y = SCREEN_HEIGHT 
    
    current_y = start_y
    while current_y > final_y:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        screen.blit(BACKGROUND_IMG, (0, 0))
        screen.blit(item, (item_x, current_y))
        pygame.display.flip()
        current_y -= rise_speed
        tempo_espera(10)
    
    # Mantener en posición final
    screen.blit(BACKGROUND_IMG, (0, 0))
    screen.blit(item, (item_x, final_y))
    pygame.display.flip()
    tempo_espera(hold_time)

def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + word + " " if current_line else word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.rstrip())
            current_line = word + " "
    
    if current_line:
        lines.append(current_line.rstrip())
    
    return lines

def display_text(text, x, y, font, color=WHITE, max_width=None):
    lines = text.split('\n')
    y_offset = 0
    for line in lines:
        # Si hay max_width, hacer word wrap
        if max_width:
            wrapped_lines = wrap_text(line, font, max_width)
        else:
            wrapped_lines = [line]
        
        for wrapped_line in wrapped_lines:
            text_surface = font.render(wrapped_line, True, color)
            screen.blit(text_surface, (x, y + y_offset))
            y_offset += text_surface.get_height() + LINE_SPACING

def show_dialogue(dialogue_list, font, color=WHITE, voz = "voz_narrador"):
    index = 0
    TEXTBOX_Y_OFFSET = 50
    TEXTBOX_HEIGHT = 100
    TEXTBOX_WIDTH = SCREEN_WIDTH - 40
    TEXTBOX_X = 20
    TEXTBOX_Y = SCREEN_HEIGHT - TEXTBOX_Y_OFFSET - TEXTBOX_HEIGHT
    TEXT_PADDING_X = 30
    TEXT_PADDING_Y = 15
    TEXT_MAX_WIDTH = TEXTBOX_WIDTH - (TEXT_PADDING_X * 2)
    while index < len(dialogue_list):
        phrase = dialogue_list[index]
        current_length = 0
        finished = False
        skip = False
        while not finished:
            screen.blit(BACKGROUND_IMG, (0, 0))
            if CHARACTER_IMG is not None:
                char_x = (SCREEN_WIDTH - CHARACTER_IMG.get_width()) // 2
                char_y = TEXTBOX_Y - CHARACTER_IMG.get_height()
                if ITEM_IMG is not None:
                    char_x = (SCREEN_WIDTH // 2) - CHARACTER_IMG.get_width() + 40
                screen.blit(CHARACTER_IMG, (char_x, char_y))
            if ITEM_IMG is not None:
                item_x = (SCREEN_WIDTH // 2) - 40
                item_y = TEXTBOX_Y - ITEM_IMG.get_height()
                screen.blit(ITEM_IMG, (item_x, item_y))
            show_indicator = current_length >= len(phrase)
            draw_text_box(TEXTBOX_Y_OFFSET, width=TEXTBOX_WIDTH, height=TEXTBOX_HEIGHT, color=BLACK, show_space_indicator=show_indicator)
            display_text(
                phrase[:current_length],
                TEXTBOX_X + TEXT_PADDING_X,
                TEXTBOX_Y + TEXT_PADDING_Y,
                font,
                color,
                max_width=TEXT_MAX_WIDTH
            )
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        raise SaltarCinematica()
                    
                    if event.key == pygame.K_SPACE:
                        if current_length < len(phrase):
                            # Skip to full phrase
                            current_length = len(phrase)
                            skip = True
                        else:
                            finished = True
                            index += 1
                        break

            if not skip and current_length < len(phrase):
                if phrase[current_length] != " " and (current_length % 2 == 0):
                    audio.canal_texto.stop()
                    audio.reproducir_sonido(voz, audio.canal_texto)
                current_length += 1
                tempo_espera(30) 
            elif current_length >= len(phrase):
                skip = False  

                check_skip()
                pygame.time.delay(10)

def draw_text_box(y_offset, width=SCREEN_WIDTH-40, height=100, color=BLACK, show_space_indicator=False):
    # Estilo como los botones del menú de inicio
    rect = pygame.Rect(20, SCREEN_HEIGHT - y_offset - height, width, height)
    color_fondo = (40, 40, 60)
    color_borde = (255, 215, 0)
    border_radius = 15
    grosor_borde = 3
    # Fondo
    pygame.draw.rect(screen, color_fondo, rect, border_radius=border_radius)
    # Borde
    pygame.draw.rect(screen, color_borde, rect, grosor_borde, border_radius=border_radius)
    
    if show_space_indicator:
        try:
            font_ind = pygame.font.Font(FONT_FILE, 14)
        except:
            font_ind = pygame.font.Font(None, 14)
        ind_render = font_ind.render("ESPACIO", True, (200, 200, 200))
        screen.blit(ind_render, (rect.right - 120, rect.bottom - 25))

dialogues1 = [
    "Era principios de Septiembre de 20XX...",
    "En un lugar de la UDC, de cuyo nombre no quiero acordarme...",
    "Donde los autobuses siempre van o vacíos o llevan a facultades enteras dentro..."
]
dialogues2 = [
    "Carlitos, (por alguna razón) estaba muy emocionado de empezar su primer año de facultad...",
    "Sin embargo...",
    "No tenía ni idea de lo que su destino le depararía..."
]

dialogues3 = [
    "Hola pichi, ¿qué vas a querer?",
    "¿Una tortilla? Maaaaarchando papi.",
]

dialogues3_jumpscare = [
    "¡LÁZARO UNA TORTILLA PARA EL RUBIO ESTE!"
]

dialogues3_tras_jumpscare = [
    "(Carlitos no es rubio)"
]

dialogues4_tortilla = [
    "Aquí tienes tu tortilla, papi.",
    "Que aproveche.",
    "Espera pichi, primero tienes que pagar.",
    "Serían $$$ en total."
]

dialogues4_enfadado = [
    "¿Cómo que no tienes dinero?",
    "¡¿?!"
]

dialogues4_golpe = [
    "(Carlitos siente un duro golpe y la vista se le pone en negro)"
]

dialogue_transicion = [
    "Parece que Michel ha secuestrado a Carlitos...",
    "Y lo va a obligar a trabajar en la cafetería para pagar su deuda."
]

def run_cinematics(pantalla):
    init_cinematics(pantalla)

    try:
        audio.reproducir_musica("parada_bus", -1, 1000)
        fade_in(screen) 
        show_dialogue(dialogues1, font, WHITE)
        fade_out(screen)
        set_background(os.path.join(ASSETS_PATH, "graphics", "cinematica", "facu1.png"))
        fade_in(screen)
        show_dialogue(dialogues2, font, WHITE)
        audio.detener_musica(500)
        fade_out(screen)
        set_background(os.path.join(ASSETS_PATH, "graphics", "cinematica", "cafeta.png"))
        set_character(os.path.join(ASSETS_PATH, "graphics", "characters", "míchel", "michel_normal.png"), scale=0.60)
        audio.reproducir_musica("cafeteria", -1, 1000)
        fade_in(screen)
        audio.reproducir_sonido("m_buenos_dias_pichi")
        show_dialogue(dialogues3, font, WHITE, "voz_michel")
        set_character(os.path.join(ASSETS_PATH, "graphics", "characters", "míchel", "michel_jumpScare.png"), scale=0.75)
        show_dialogue(dialogues3_jumpscare, font, WHITE, "voz_michel")
        audio.reproducir_sonido("m_risa_malevola")
        show_dialogue(dialogues3_tras_jumpscare, font, WHITE)     
        clear_character()
        fade_out(screen)
        
        set_character(os.path.join(ASSETS_PATH, "graphics", "characters", "míchel", "michel_normal.png"), scale=0.60)
        set_item(os.path.join(ASSETS_PATH, "graphics", "ui", "tortilla.png"), scale=0.5)
        fade_in(screen)
        audio.reproducir_sonido("m_una_tortillita")
        show_dialogue(dialogues4_tortilla, font, WHITE, "voz_michel")
        clear_item()
        clear_character()
        show_item_from_bottom(os.path.join(ASSETS_PATH, "graphics", "ui", "cartera_vacia.png"), scale=0.8, rise_speed=8, hold_time=2500)
        set_character(os.path.join(ASSETS_PATH, "graphics", "characters", "míchel", "michel_enfadao.png"), scale=0.60)
        show_dialogue(dialogues4_enfadado, font, WHITE, "voz_michel_grave")
        show_dialogue(dialogues4_golpe, font, WHITE)
        clear_character()
        audio.reproducir_sonido("m_buenas_noches")
        tempo_espera(1000)
        audio.reproducir_sonido("golpe_sarten")
        tempo_espera(500)
        audio.detener_musica(500)
        fade_out(screen)
        
        tempo_espera(1000)
        set_black_background()
        screen.fill(BLACK)
        pygame.display.flip()
        show_dialogue(dialogue_transicion, font, WHITE)

    except SaltarCinematica:
        audio.detener_musica(100)
        audio.canal_texto.stop()
        clear_character()
        clear_item()
        set_black_background()
        screen.fill(BLACK)
        pygame.display.flip()
        
    finally:
        pygame.event.clear()

if __name__ == "__main__":
    pygame.init()
    pantalla = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Cinematicas - Test")
    run_cinematics(pantalla)
    pygame.quit()
    sys.exit()