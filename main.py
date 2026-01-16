import pygame
import random
import sys

pygame.init()

W, H = 800, 600
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()

COLORS = {
    'white': (255, 255, 255),
    'red': (231, 76, 60),
    'green': (46, 204, 113),
    'blue': (52, 152, 219),
    'yellow': (241, 196, 15),
    'purple': (155, 89, 182),
    'bg': (15, 30, 60),
    'wood': (139, 69, 19),
    'gold': (255, 215, 0),
    'snow': (240, 248, 255),
    'pink': (255, 182, 193),
    'dark_green': (0, 100, 0),
    'tree_brown': (101, 67, 33)
}


class RecordManager:
    def __init__(self):
        self.record = 0
        self.load_record()

    def load_record(self):
        try:
            with open('record.txt', 'r') as f:
                self.record = int(f.read())
        except:
            self.save_record()

    def save_record(self):
        with open('record.txt', 'w') as f:
            f.write(str(self.record))

    def update_record(self, score):
        if score > self.record:
            self.record = score
            self.save_record()


class GameState:
    def __init__(self):
        self.slot_count = 4
        self.fall_speed = 1.0
        self.spawn_chance = 1.0
        self.slot_width = W // self.slot_count
        self.santa_pos = 0
        self.score = 1
        self.lives = 3
        self.gifts = []
        self.over = False
        self.active = False
        self.snowflakes = [(random.randint(0, W), random.randint(-100, 0),
                            random.uniform(0.5, 2)) for _ in range(80)]
        self.record_manager = RecordManager()
        self.last_spawn_time = 0
        self.spawn_delay = 1000
        self.active_slots = set()
        self.message = ""
        self.message_timer = 0
        self.last_speed_increase = 0
        self.game_100_passed = False
        self.game_555_passed = False
        self.waiting_for_plus = False
        self.shown_achievements = set()

    def show_message(self, text, duration=3000):
        self.message = text
        self.message_timer = pygame.time.get_ticks() + duration

    def move_santa(self, slot):
        if 0 <= slot < self.slot_count:
            self.santa_pos = slot

    def spawn_gift(self):
        current_time = pygame.time.get_ticks()

        if current_time - self.last_spawn_time < self.spawn_delay:
            return False

        available_slots = [i for i in range(self.slot_count) if i not in self.active_slots]

        if not available_slots:
            return False

        slot = random.choice(available_slots)
        x = slot * self.slot_width + self.slot_width // 2 - 20

        self.gifts.append({
            'x': x, 'y': 150, 's': self.fall_speed,
            'c': random.choice([COLORS['red'], COLORS['green'], COLORS['blue'], COLORS['yellow'], COLORS['purple']]),
            'r': 0,
            'slot': slot
        })

        self.active_slots.add(slot)
        self.last_spawn_time = current_time
        return True

    def update(self):
        if self.over or not self.active or self.waiting_for_plus:
            return

        for i in range(len(self.snowflakes)):
            x, y, s = self.snowflakes[i]
            y += s
            if y > H:
                y = random.randint(-50, 0)
                x = random.randint(0, W)
            self.snowflakes[i] = (x, y, s)

        if random.random() * 100 < self.spawn_chance:
            self.spawn_gift()

        gifts_to_remove = []
        slots_to_clear = set()

        for gift in self.gifts:
            gift['y'] += gift['s']
            gift['r'] += gift['s'] * 1.5

            sx = self.santa_pos * self.slot_width + (self.slot_width - 80) // 2

            if (gift['y'] > H - 100 - 30 and
                    gift['x'] + 40 > sx and
                    gift['x'] < sx + 80):
                self.score += 1
                gifts_to_remove.append(gift)
                slots_to_clear.add(gift['slot'])

                if self.score % 10 == 0 and self.score > self.last_speed_increase:
                    self.fall_speed += 0.2
                    self.last_speed_increase = self.score

                achievements = {
                    10: "0+",
                    13: "мзиф",
                    31: "на превьюшечку",
                    42: "Всем нашим",
                    55: "пять пять пять",
                    87: "Ремнант",
                    89: "офф",
                    404: "не найдено",
                    505: "имя"
                }

                if self.score in achievements and self.score not in self.shown_achievements:
                    self.shown_achievements.add(self.score)
                    self.show_message(f"Получена ачивка: {achievements[self.score]}", 3000)

                if self.score == 100 and not self.game_100_passed:
                    self.waiting_for_plus = True
                    self.game_100_passed = True

                if self.score == 555 and not self.game_555_passed:
                    self.over = True
                    self.game_555_passed = True
                    self.record_manager.update_record(self.score)

            elif gift['y'] > H:
                self.lives -= 1
                gifts_to_remove.append(gift)
                slots_to_clear.add(gift['slot'])
                if self.lives <= 0:
                    self.over = True
                    self.record_manager.update_record(self.score)

        for gift in gifts_to_remove:
            if gift in self.gifts:
                self.gifts.remove(gift)

        for slot in slots_to_clear:
            self.active_slots.discard(slot)

        if self.message and pygame.time.get_ticks() > self.message_timer:
            self.message = ""


def draw_simple_background():
    screen.fill(COLORS['bg'])
    for _ in range(50):
        x, y = random.randint(0, W), random.randint(0, H // 2)
        size = random.randint(1, 2)
        brightness = random.randint(100, 255)
        pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), size)
    pygame.draw.rect(screen, COLORS['snow'], (0, H - 40, W, 40))


def draw_slots(state):
    for i in range(state.slot_count):
        x = i * state.slot_width
        pygame.draw.rect(screen, COLORS['wood'], (x + 20, 100, state.slot_width - 40, 20))
        pygame.draw.rect(screen, COLORS['wood'], (x + 30, 120, 10, 20))
        pygame.draw.rect(screen, COLORS['wood'], (x + state.slot_width - 40, 120, 10, 20))

        slot_text = pygame.font.Font(None, 28).render(str(i + 1), True, COLORS['white'])
        screen.blit(slot_text, (x + state.slot_width // 2 - 5, 130))


def draw_santa(state):
    x = state.santa_pos * state.slot_width + (state.slot_width - 80) // 2
    y = H - 120

    pygame.draw.rect(screen, COLORS['red'], (x, y, 80, 100))
    pygame.draw.rect(screen, COLORS['white'], (x, y, 80, 15))
    pygame.draw.rect(screen, COLORS['white'], (x, y + 85, 80, 15))
    pygame.draw.rect(screen, (255, 229, 204), (x + 25, y + 20, 30, 25))
    pygame.draw.rect(screen, COLORS['blue'], (x + 30, y + 25, 6, 6))
    pygame.draw.rect(screen, COLORS['blue'], (x + 44, y + 25, 6, 6))
    pygame.draw.rect(screen, COLORS['white'], (x + 20, y + 40, 40, 35))


def draw_gifts(state):
    for gift in state.gifts:
        gift['s'] = state.fall_speed

        s = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(s, gift['c'], (0, 0, 40, 40))
        rc = COLORS['white'] if gift['c'] != COLORS['white'] else COLORS['red']
        pygame.draw.rect(s, rc, (17, 0, 6, 40))
        pygame.draw.rect(s, rc, (0, 17, 40, 6))
        r = pygame.transform.rotate(s, gift['r'])
        screen.blit(r, (gift['x'] - r.get_width() // 2 + 20, gift['y'] - r.get_height() // 2 + 20))


def draw_simple_ui(state):
    score_text = pygame.font.Font(None, 48).render(str(state.score), True, COLORS['white'])
    screen.blit(score_text, (W - 100, 20))

    lives_text = pygame.font.Font(None, 28).render("Жизни:", True, COLORS['white'])
    screen.blit(lives_text, (20, 15))
    for i in range(state.lives):
        pygame.draw.circle(screen, COLORS['red'], (100 + i * 35, 35), 12)
        pygame.draw.circle(screen, COLORS['white'], (100 + i * 35, 35), 8, 2)

    controls = pygame.font.Font(None, 24).render("Управление: 1 2 3 4", True, COLORS['white'])
    screen.blit(controls, (W // 2 - 140, H - 30))

    speed_text = pygame.font.Font(None, 24).render(f"Скорость: {state.fall_speed:.1f}", True, COLORS['yellow'])
    screen.blit(speed_text, (W - 150, 70))


def draw_message(state):
    if state.message:
        message_font = pygame.font.Font(None, 36)
        text_surface = message_font.render(state.message, True, COLORS['gold'])
        text_width = text_surface.get_width()
        text_height = text_surface.get_height()

        bg = pygame.Surface((text_width + 40, text_height + 20), pygame.SRCALPHA)
        pygame.draw.rect(bg, (0, 0, 0, 180), (0, 0, text_width + 40, text_height + 20), border_radius=10)
        pygame.draw.rect(bg, (255, 215, 0, 100), (0, 0, text_width + 40, text_height + 20), 2, border_radius=10)

        screen.blit(bg, (W // 2 - (text_width + 40) // 2, 50))
        screen.blit(text_surface, (W // 2 - text_width // 2, 60))


def draw_snowflakes(state):
    for x, y, size in state.snowflakes:
        pygame.draw.circle(screen, COLORS['white'], (int(x), int(y)), int(size))


def draw_tree(x, y, width, height):
    trunk_width = width // 4
    trunk_height = height // 4
    trunk_rect = (x + width // 2 - trunk_width // 2, y + height - trunk_height, trunk_width, trunk_height)
    pygame.draw.rect(screen, COLORS['tree_brown'], trunk_rect)

    triangle_height = height - trunk_height
    layers = 3
    for i in range(layers):
        layer_y = y + i * (triangle_height // layers)
        layer_height = triangle_height // layers
        layer_width = width * (layers - i) // (layers + 1)

        points = [
            (x + width // 2, layer_y),
            (x + width // 2 - layer_width // 2, layer_y + layer_height),
            (x + width // 2 + layer_width // 2, layer_y + layer_height)
        ]
        pygame.draw.polygon(screen, COLORS['dark_green'], points)

        for _ in range(3):
            star_x = random.randint(x + width // 2 - layer_width // 4, x + width // 2 + layer_width // 4)
            star_y = random.randint(layer_y + 5, layer_y + layer_height - 5)
            pygame.draw.circle(screen, COLORS['gold'], (star_x, star_y), 3)


def draw_fancy_background():
    screen.fill(COLORS['bg'])

    for i in range(5):
        x = (W // 6) * (i + 1)
        draw_tree(x - 50, H - 240, 100, 200)

    for _ in range(100):
        x, y = random.randint(0, W), random.randint(0, H // 2)
        size = random.randint(1, 3)
        brightness = random.randint(150, 255)
        pygame.draw.circle(screen, (brightness, brightness, 200), (x, y), size)


def draw_main_menu(record_manager):
    draw_fancy_background()

    title = pygame.font.Font(None, 64).render("Дед мороз и подарки", True, COLORS['gold'])

    start_bg_width = 400
    start_bg = pygame.Surface((start_bg_width, 100), pygame.SRCALPHA)
    pygame.draw.rect(start_bg, (34, 139, 34, 180), (0, 0, start_bg_width, 100), border_radius=20)
    pygame.draw.rect(start_bg, (255, 255, 255, 50), (0, 0, start_bg_width, 100), 3, border_radius=20)

    screen.blit(title, (W // 2 - title.get_width() // 2, 50))
    screen.blit(start_bg, (W // 2 - start_bg_width // 2, 200))

    start_text = pygame.font.Font(None, 48).render("СТАРТ", True, COLORS['snow'])
    record_text = pygame.font.Font(None, 36).render(f"Рекорд: {record_manager.record}", True, COLORS['gold'])

    screen.blit(start_text, (W // 2 - start_text.get_width() // 2, 220))
    screen.blit(record_text, (W // 2 - record_text.get_width() // 2, 280))

    hint = pygame.font.Font(None, 24).render("Нажмите ПРОБЕЛ для начала игры", True, COLORS['gold'])
    screen.blit(hint, (W // 2 - hint.get_width() // 2, 480))

    pygame.display.flip()


def draw_100_win_screen(state):
    screen.fill(COLORS['bg'])

    message_font = pygame.font.Font(None, 72)
    message_text = message_font.render("Вы прошли игру!", True, COLORS['gold'])
    screen.blit(message_text, (W // 2 - message_text.get_width() // 2, H // 3))

    score_text = pygame.font.Font(None, 48).render(f"Счет: {state.score}", True, COLORS['white'])
    screen.blit(score_text, (W // 2 - score_text.get_width() // 2, H // 2 - 30))

    record_text = pygame.font.Font(None, 36).render(f"Рекорд: {state.record_manager.record}", True, COLORS['gold'])
    screen.blit(record_text, (W // 2 - record_text.get_width() // 2, H // 2 + 20))

    restart = pygame.font.Font(None, 36).render("ПРОБЕЛ - заново   ESC - меню", True, COLORS['green'])
    screen.blit(restart, (W // 2 - restart.get_width() // 2, H // 2 + 80))


def draw_555_win_screen(state):
    screen.fill(COLORS['bg'])

    message_font = pygame.font.Font(None, 72)
    message_text = message_font.render("Вы действительно прошли игру.", True, COLORS['gold'])
    screen.blit(message_text, (W // 2 - message_text.get_width() // 2, H // 3))

    score_text = pygame.font.Font(None, 48).render(f"Счет: {state.score}", True, COLORS['white'])
    screen.blit(score_text, (W // 2 - score_text.get_width() // 2, H // 2 - 30))

    record_text = pygame.font.Font(None, 36).render(f"Рекорд: {state.record_manager.record}", True, COLORS['gold'])
    screen.blit(record_text, (W // 2 - record_text.get_width() // 2, H // 2 + 20))

    restart = pygame.font.Font(None, 36).render("ПРОБЕЛ - заново   ESC - меню", True, COLORS['green'])
    screen.blit(restart, (W // 2 - restart.get_width() // 2, H // 2 + 80))


def draw_game_over_screen(state):
    screen.fill(COLORS['bg'])

    over_text = pygame.font.Font(None, 72).render("ИГРА ОКОНЧЕНА", True, COLORS['red'])
    screen.blit(over_text, (W // 2 - over_text.get_width() // 2, H // 3))

    score_text = pygame.font.Font(None, 48).render(f"Счет: {state.score}", True, COLORS['white'])
    screen.blit(score_text, (W // 2 - score_text.get_width() // 2, H // 2 - 30))

    record_text = pygame.font.Font(None, 36).render(f"Рекорд: {state.record_manager.record}", True, COLORS['gold'])
    screen.blit(record_text, (W // 2 - record_text.get_width() // 2, H // 2 + 20))

    restart = pygame.font.Font(None, 36).render("ПРОБЕЛ - заново   ESC - меню", True, COLORS['green'])
    screen.blit(restart, (W // 2 - restart.get_width() // 2, H // 2 + 80))


def main():
    record_manager = RecordManager()

    while True:
        draw_main_menu(record_manager)

        waiting_for_start = True
        while waiting_for_start:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting_for_start = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            clock.tick(60)

        state = GameState()
        state.record_manager = record_manager
        state.active = True

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        break

                    if (event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS) and state.waiting_for_plus:
                        state.waiting_for_plus = False

                    if event.key == pygame.K_SPACE and state.over:
                        state = GameState()
                        state.record_manager = record_manager
                        state.active = True

                    if not state.over and state.active and not state.waiting_for_plus:
                        if event.key == pygame.K_1:
                            state.move_santa(0)
                        elif event.key == pygame.K_2:
                            state.move_santa(1)
                        elif event.key == pygame.K_3:
                            state.move_santa(2)
                        elif event.key == pygame.K_4:
                            state.move_santa(3)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                break

            if state.over:
                if state.game_555_passed:
                    draw_555_win_screen(state)
                else:
                    draw_game_over_screen(state)
            elif state.waiting_for_plus:
                draw_100_win_screen(state)
            else:
                state.update()
                draw_simple_background()
                draw_snowflakes(state)
                draw_slots(state)
                draw_gifts(state)
                draw_santa(state)
                draw_simple_ui(state)
                draw_message(state)

            pygame.display.flip()
            clock.tick(60)


if __name__ == "__main__":
    main()