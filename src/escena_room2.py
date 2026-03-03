import os
import pygame


ROOM2_DOOR_LINE_COL = ((209, 401), (209, 418))
ROOM2_INSIDE_TRIGGER_COL = (187, 414)
ROOM2_KEY_COL_POS = (188, 232)


class Room2Key:
    def __init__(self, center):
        self.image = pygame.Surface((52, 26), pygame.SRCALPHA)
        oro = (245, 208, 66)
        borde = (178, 134, 35)
        pygame.draw.circle(self.image, oro, (10, 13), 8)
        pygame.draw.circle(self.image, borde, (10, 13), 8, 2)
        pygame.draw.circle(self.image, (0, 0, 0, 0), (10, 13), 3)
        pygame.draw.rect(self.image, oro, pygame.Rect(16, 11, 22, 4), border_radius=2)
        pygame.draw.rect(self.image, oro, pygame.Rect(34, 11, 4, 8))
        pygame.draw.rect(self.image, oro, pygame.Rect(40, 11, 4, 6))
        pygame.draw.rect(self.image, borde, pygame.Rect(16, 11, 28, 4), 1, border_radius=2)
        self.rect = self.image.get_rect(center=center)


class Room2Event:
    def __init__(self, graphics_dir, collision_scale_down, room2_rect, map_size):
        self.collision_scale_down = collision_scale_down
        self.room2_rect = room2_rect

        room2_front_img = os.path.join(graphics_dir, "environments", "room2_front.png")
        self.room2_front = pygame.image.load(room2_front_img).convert_alpha()
        self.room2_front = pygame.transform.scale(self.room2_front, map_size)

        self.door_line_world_x = ROOM2_DOOR_LINE_COL[0][0] * self.collision_scale_down
        self.door_line_world_y1 = ROOM2_DOOR_LINE_COL[0][1] * self.collision_scale_down
        self.door_line_world_y2 = ROOM2_DOOR_LINE_COL[1][1] * self.collision_scale_down

        self.inside_trigger_world = (
            ROOM2_INSIDE_TRIGGER_COL[0] * self.collision_scale_down,
            ROOM2_INSIDE_TRIGGER_COL[1] * self.collision_scale_down,
        )
        self.inside_trigger_rect = pygame.Rect(0, 0, 120, 120)
        self.inside_trigger_rect.center = self.inside_trigger_world

        self.door_block_rect = pygame.Rect(0, 0, 60, (self.door_line_world_y2 - self.door_line_world_y1) + 140)
        self.door_block_rect.midleft = (
            self.door_line_world_x,
            (self.door_line_world_y1 + self.door_line_world_y2) // 2,
        )

        self.key_world = (
            ROOM2_KEY_COL_POS[0] * self.collision_scale_down,
            ROOM2_KEY_COL_POS[1] * self.collision_scale_down,
        )
        self.key = Room2Key(self.key_world)

        self.event_started = False
        self.door_locked = False
        self.key_collected = False

        self.focus_door_timer_ms = 0
        self.focus_door_duration_ms = 1400

        self.darkness_alpha = 245
        self.flashlight_radius = 82

        self._last_player_center = None
        self._last_inside_trigger = False
        self._darkness_surf = None

    def get_extra_collision_rects(self):
        if self.door_locked:
            return [self.door_block_rect]
        return []

    def _crossed_door_into_room(self, old_center, new_center):
        old_x, old_y = old_center
        new_x, new_y = new_center

        crossed_x = old_x >= self.door_line_world_x and new_x < self.door_line_world_x
        door_band_min = self.door_line_world_y1 - 80
        door_band_max = self.door_line_world_y2 + 80
        y_ok = door_band_min <= old_y <= door_band_max and door_band_min <= new_y <= door_band_max
        reached_inside = self.inside_trigger_rect.collidepoint(new_center)

        return crossed_x and y_ok and reached_inside

    def update(self, player, delta_ms):
        player_center = player.hitbox.center

        # jugador dentro de room2 y a la izquierda de la puerta
        # para que no haya bugs atrancándose con la puerta
        inside_room2 = self.room2_rect.collidepoint(player_center)
        past_door_line = player_center[0] < self.door_line_world_x
        
        # jugador ha cruzado completamente cuando todo su hitbox está dentro
        fully_past_door = player.hitbox.right < self.door_line_world_x

        # activar evento (luz) cuando el centro cruza
        if not self.event_started and inside_room2 and past_door_line:
            self.event_started = True

        # bloquear puerta solo cuando cruzó completamente
        if self.event_started and not self.door_locked and not self.key_collected and fully_past_door:
            self.door_locked = True

        if (self.event_started and not self.key_collected and
                player.hitbox.colliderect(self.key.rect)):
            self.key_collected = True
            self.door_locked = False
            self.focus_door_timer_ms = self.focus_door_duration_ms
            player.controls_enabled = False

        if self.focus_door_timer_ms > 0:
            self.focus_door_timer_ms = max(0, self.focus_door_timer_ms - delta_ms)
            focus_pos = self.door_block_rect.center
            if self.focus_door_timer_ms == 0:
                player.controls_enabled = True
        else:
            focus_pos = None

        return focus_pos

    def draw_objects(self, render_surf, camera):
        if self.event_started and not self.key_collected:
            render_surf.blit(self.key.image, camera.aplicar_rect(self.key.rect))

    def draw_front(self, render_surf, camera):
        render_surf.blit(self.room2_front, camera.aplicar_rect(self.room2_front.get_rect()))

    def draw_light_overlay(self, render_surf, camera, player):
        if not self.event_started:
            return

        if not self.room2_rect.collidepoint(player.hitbox.center):
            return

        if (self._darkness_surf is None or
                self._darkness_surf.get_size() != render_surf.get_size()):
            self._darkness_surf = pygame.Surface(render_surf.get_size(), pygame.SRCALPHA)

        self._darkness_surf.fill((0, 0, 0, self.darkness_alpha))
        light_center = camera.aplicar_rect(player.hitbox).center

        for radius, alpha in (
            (self.flashlight_radius + 70, 150),
            (self.flashlight_radius + 25, 70),
            (self.flashlight_radius, 0),
        ):
            pygame.draw.circle(self._darkness_surf, (0, 0, 0, alpha), light_center, radius)

        # halo de luz en la puerta durante la animación de enfoque
        if self.focus_door_timer_ms > 0:
            door_center = camera.aplicar_rect(self.door_block_rect).center
            door_light_radius = 120
            for radius, alpha in (
                (door_light_radius + 50, 180),
                (door_light_radius + 20, 100),
                (door_light_radius, 0),
            ):
                pygame.draw.circle(self._darkness_surf, (0, 0, 0, alpha), door_center, radius)

        render_surf.blit(self._darkness_surf, (0, 0))
