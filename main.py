import pygame, os, sys

WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 700, 700
FPS = 15
MAP_DIR = 'levels'
IMAGE_DIR = 'images'
COUNT_LEVELS = 4
TILE_SIZE = 55

pygame.init()
screen = pygame.display.set_mode(WINDOW_SIZE)


def load_image(name, colorkey=None):
    fullname = name
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


SIGNS = {'grass': '-', 'wall': '#', 'hero': '@', 'box': '$', 'target': '.', 'free': ' '}

IMAGES = {'hero': pygame.transform.scale(load_image(f'{IMAGE_DIR}/hero.png'), (TILE_SIZE, TILE_SIZE)),
          'wall': pygame.transform.scale(load_image(f'{IMAGE_DIR}/wall.jpg'), (TILE_SIZE, TILE_SIZE)),
          'grass': pygame.transform.scale(load_image(f'{IMAGE_DIR}/grass.jpg'), (TILE_SIZE, TILE_SIZE)),
          'target': pygame.transform.scale(load_image(f'{IMAGE_DIR}/target.jpg'), (TILE_SIZE, TILE_SIZE)),
          'box': pygame.transform.scale(load_image(f'{IMAGE_DIR}/box.jpg'), (TILE_SIZE, TILE_SIZE)),
          'free': pygame.transform.scale(load_image(f'{IMAGE_DIR}/free.jpg'), (TILE_SIZE, TILE_SIZE)),
          'next': load_image(f'{IMAGE_DIR}/next.png'),
          'back': load_image(f'{IMAGE_DIR}/back.png'),
          'again': load_image(f'{IMAGE_DIR}/again.png')}


class Level:
    def __init__(self, filename):
        self.map = []
        self.targets = []
        with open(f'{MAP_DIR}/{filename}') as input_file:
            for line in input_file:
                self.map.append(list(line.rstrip()))
        self.height = len(self.map)
        self.width = max((map(lambda x: len(x), self.map)))
        self.tile_size = TILE_SIZE
        self.left = max(0, (WINDOW_WIDTH // TILE_SIZE - self.width) // 2)
        self.top = max(0, (WINDOW_HEIGHT // TILE_SIZE - self.height) // 2)
        self.edit_map()

    def edit_map(self):
        for i in range(self.height):
            self.map[i] = list(''.join(self.map[i]).ljust(self.width, SIGNS['grass']))
        for i in range(self.height):
            for q in range(self.width):
                if self.map[i][q] == SIGNS['target']:
                    self.targets.append((q, i))
                    self.map[i][q] = SIGNS['free']

    def get_hero_start_position(self):
        x, y = [(self.map[i].index(SIGNS['hero']), i) for i in range(self.height) if SIGNS['hero'] in self.map[i]][0]
        self.map[y][x] = SIGNS['free']
        return x, y

    def render(self, screen):
        for y in range(self.height):
            for x in range(self.width):
                screen.blit(IMAGES['free'], ((self.left + x) * TILE_SIZE, (self.top + y) * TILE_SIZE))
        for x, y in self.targets:
            screen.blit(IMAGES['target'], ((self.left + x) * TILE_SIZE, (self.top + y) * TILE_SIZE))
        for y in range(self.height):
            for x in range(self.width):
                if self.map[y][x] == SIGNS['wall']:
                    screen.blit(IMAGES['wall'], ((self.left + x) * TILE_SIZE, (self.top + y) * TILE_SIZE))
                elif self.map[y][x] == SIGNS['grass']:
                    screen.blit(IMAGES['grass'], ((self.left + x) * TILE_SIZE, (self.top + y) * TILE_SIZE))
                elif self.map[y][x] == SIGNS['box']:
                    screen.blit(IMAGES['box'], ((self.left + x) * TILE_SIZE, (self.top + y) * TILE_SIZE))

    def how_go(self, pos):
        return self.map[pos[1]][pos[0]]

    def move_box(self, spos, epos):
        self.map[spos[1]][spos[0]] = SIGNS['free']
        self.map[epos[1]][epos[0]] = SIGNS['box']

    def get_boxs_pos(self):
        boxes = []
        for i in range(self.height):
            for q in range(self.width):
                if self.map[i][q] == SIGNS['box']:
                    boxes.append((q, i))
        return boxes


class Hero:
    def __init__(self, position):
        self.x, self.y = position
        self.left = 0
        self.top = 0

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    def render(self, screen):
        screen.blit(IMAGES['hero'], ((self.left + self.x) * TILE_SIZE, (self.top + self.y) * TILE_SIZE))


class Game:
    def __init__(self, level, hero):
        self.level = level
        self.hero = hero
        hero.left = level.left
        hero.top = level.top

    def render(self, screen):
        self.level.render(screen)
        self.hero.render(screen)

    def update_hero(self, pos):
        x, y = self.hero.get_position()
        next_x, next_y = pos
        if next_x == next_y == 0:
            return
        res = self.level.how_go((next_x + x, next_y + y))
        if res == SIGNS['free']:
            self.hero.set_position((next_x + x, next_y + y))
        elif res == SIGNS['box'] and self.level.how_go((2 * next_x + x, 2 * next_y + y)) == SIGNS['free']:
            self.level.move_box((next_x + x, next_y + y), (2 * next_x + x, 2 * next_y + y))
            self.hero.set_position((next_x + x, next_y + y))

    def check_win(self):
        return set(self.level.targets) == set(self.level.get_boxs_pos())


class Buttons:
    def __init__(self):
        self.pos = None
        self.size = None

    def get_click(self, pos):
        if self.pos is None or self.size is None:
            return
        if self.pos[0] <= pos[0] <= (self.pos[0] + self.size[0]) \
                and self.pos[0] <= pos[0] <= (self.pos[0] + self.size[0]):
            return self.on_click()
        else:
            return None

    def render(self, screen):
        if self.pos is None or self.size is None:
            return
        screen.blit(self.image, self.pos)


class Again(Buttons):
    def __init__(self):
        super().__init__()
        self.size = (45, 45)
        self.pos = (640, 640)
        self.image = pygame.transform.scale(IMAGES['again'], self.size)

    def on_click(self):
        return 0


class Next(Buttons):
    def __init__(self):
        super().__init__()
        self.size = (45, 45)
        self.pos = (580, 640)
        self.image = pygame.transform.scale(IMAGES['next'], self.size)

    def on_click(self):
        return 1


class Back(Buttons):
    def __init__(self):
        super().__init__()
        self.size = (45, 45)
        self.pos = (520, 640)
        self.image = pygame.transform.scale(IMAGES['back'], self.size)

    def on_click(self):
        return -1


def show_message(screen, message):
    font = pygame.font.Font(None, 20)
    text = font.render(message, True, (255, 0, 0))
    text_x = WINDOW_WIDTH // 2 - text.get_width() // 2
    text_y = WINDOW_HEIGHT // 2 - text.get_height() // 2
    text_w = text.get_width()
    text_h = text.get_height()
    # pygame.draw.rect(screen, (200, 150, 50), (text_x - 10, text_y - 10, text_w + 20, text_h + 20))
    screen.blit(text, (text_x, text_y))


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    screen.fill(('#f5f5dc'))

    level = Level('1.txt')
    hero = Hero(level.get_hero_start_position())
    game = Game(level, hero)
    game_over = False
    new_game = False
    now_level = 1

    buttons = {'again': Again(), 'next': Next(), 'back': Back()}

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and not game_over:
                next_x, next_y = 0, 0
                if event.key == pygame.K_UP:
                    next_x, next_y = 0, -1
                elif event.key == pygame.K_DOWN:
                    next_x, next_y = 0, 1
                elif event.key == pygame.K_RIGHT:
                    next_x, next_y = 1, 0
                elif event.key == pygame.K_LEFT:
                    next_x, next_y = -1, 0
                game.update_hero((next_x, next_y))
            if event.type == pygame.MOUSEBUTTONDOWN:
                for e in buttons:
                    res = buttons[e].get_click(event.pos)
                    if res is not None:
                        now_level += res
                        now_level = min(max(1, now_level), COUNT_LEVELS)
                        new_game = True
        if new_game:
            level = Level(f'{now_level}.txt')
            hero = Hero(level.get_hero_start_position())
            game = Game(level, hero)
            game_over = False
            new_game = False
        screen.fill(('#f5f5dc'))
        game.render(screen)
        for e in buttons:
            buttons[e].render(screen)
        if game.check_win():
            show_message(screen, "Вы победили! Перейдите на следующий уровень")
            game_over = True
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == '__main__':
    main()
