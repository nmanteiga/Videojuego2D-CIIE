import pygame
import sys
import time


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Visual Novel")
font = pygame.font.Font(None, 24)
WHITE = (240, 240, 240)
BLACK = (0, 0, 0)

# Background image variable
BACKGROUND_IMG = pygame.image.load("../assets/graphics/cinematica/bus1.png").convert()
BACKGROUND_IMG = pygame.transform.scale(BACKGROUND_IMG, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Function to change background image
def set_background(image_path):
    global BACKGROUND_IMG
    img = pygame.image.load(image_path).convert()
    BACKGROUND_IMG = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Fade functions
def fade_in(surface, speed=4):
    fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade.fill((0, 0, 0))
    for alpha in range(255, -1, -speed):
        fade.set_alpha(alpha)
        surface.blit(BACKGROUND_IMG, (0, 0))
        surface.blit(fade, (0, 0))
        pygame.display.flip()
        pygame.time.delay(10)

def fade_out(surface, speed=4):
    fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade.fill((0, 0, 0))
    for alpha in range(0, 256, speed):
        fade.set_alpha(alpha)
        surface.blit(BACKGROUND_IMG, (0, 0))
        surface.blit(fade, (0, 0))
        pygame.display.flip()
        pygame.time.delay(10)

def display_text(text, x, y, font, color=WHITE):
    lines = text.split('\n')
    y_offset = 0
    for line in lines:
        text_surface = font.render(line, True, color)
        screen.blit(text_surface, (x, y + y_offset))
        y_offset += text_surface.get_height()

def show_dialogue(dialogue_list, font, color=WHITE):
    index = 0
    TEXTBOX_Y_OFFSET = 50
    TEXTBOX_HEIGHT = 100
    TEXTBOX_WIDTH = SCREEN_WIDTH - 40
    TEXTBOX_X = 20
    TEXTBOX_Y = SCREEN_HEIGHT - TEXTBOX_Y_OFFSET - TEXTBOX_HEIGHT
    TEXT_PADDING_X = 30
    TEXT_PADDING_Y = 15
    while index < len(dialogue_list):
        phrase = dialogue_list[index]
        current_length = 0
        finished = False
        skip = False
        while not finished:
            screen.blit(BACKGROUND_IMG, (0, 0))
            draw_text_box(TEXTBOX_Y_OFFSET, width=TEXTBOX_WIDTH, height=TEXTBOX_HEIGHT, color=BLACK)
            # Show only up to current_length characters
            display_text(
                phrase[:current_length],
                TEXTBOX_X + TEXT_PADDING_X,
                TEXTBOX_Y + TEXT_PADDING_Y,
                font,
                color
            )
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
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
                current_length += 1
                pygame.time.delay(30)  # Adjust speed here (milliseconds per character)
            elif current_length >= len(phrase):
                skip = False  # Reset skip for next phrase
                # Wait for user to press SPACE to continue
                # (Handled in event loop above)

def draw_text_box(y_offset, width=SCREEN_WIDTH-40, height=100, color=BLACK):
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

# Example dialogue
dialogues1 = [
    "Érase una vez blablablabla",
    "Nuestro personaje blabla",
    "blablabla..."
]
dialogues2 = [
    "LLegó a clase blablablabla",
    "blabla",
    "blablabla..."
]

# Main loop
running = True
fade_in(screen)  # Fade from black at start
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    show_dialogue(dialogues1, font, WHITE)
    fade_out(screen)
    set_background("../assets/graphics/cinematica/facu1.png")
    fade_in(screen)
    show_dialogue(dialogues2, font, WHITE)
    fade_out(screen)  # Fade to black at end
    pygame.quit()
    sys.exit()