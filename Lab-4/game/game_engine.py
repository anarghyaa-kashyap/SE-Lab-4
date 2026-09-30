import math
import pygame
from .player import Player
from .obstacle import Obstacle
from .sounds import Sounds

# Game Engine

WHITE = (255, 255, 255)
BROWN = (120, 80, 40)
DARK_GREEN = (30, 100, 30)

PLAYING = "PLAYING"
GAME_OVER = "GAME_OVER"

DIFFICULTIES = {
    "Easy": {"key": pygame.K_1, "speed": 5, "spawn_interval": 90},
    "Medium": {"key": pygame.K_2, "speed": 6, "spawn_interval": 70},
    "Hard": {"key": pygame.K_3, "speed": 8, "spawn_interval": 55},
}

class GameEngine:
    MAX_SPEED = 20
    DEBUG_SPEED = 80
    GAME_OVER_INPUT_DELAY_MS = 500

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.ground_y = height - 40

        self.speed_increase_per_frame = 0.003

        self.font = pygame.font.SysFont("Arial", 30)
        self.title_font = pygame.font.SysFont("Arial", 64, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 22)

        self.overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 160))

        self.sounds = Sounds()

        self.quit_requested = False
        self.reset("Medium")

    def reset(self, difficulty):
        preset = DIFFICULTIES[difficulty]
        self.difficulty = difficulty

        self.player = Player(80, self.ground_y)

        self.speed = preset["speed"]
        self.speed_cap_enabled = True

        self.spawn_interval = preset["spawn_interval"]  # frames between obstacle spawns
        self._spawn_timer = 0
        self.obstacles = []

        self.distance = 0
        self.score = 0

        self.state = PLAYING
        self.game_over_time = 0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.state == PLAYING:
            if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                if self.player.jump():
                    self.sounds.play("jump")
            elif event.key == pygame.K_F1:
                self.speed = self.DEBUG_SPEED
                self.speed_cap_enabled = False

        elif self.state == GAME_OVER:
            if pygame.time.get_ticks() - self.game_over_time < self.GAME_OVER_INPUT_DELAY_MS:
                return
            if event.key in (pygame.K_q, pygame.K_ESCAPE):
                self.quit_requested = True
                return
            for name, preset in DIFFICULTIES.items():
                if event.key == preset["key"]:
                    self.reset(name)
                    return

    def handle_input(self):
        # Reserved for continuously-held-key input; this runner only
        # needs an edge-triggered jump, handled in handle_event.
        pass

    def update(self):
        if self.state != PLAYING:
            return

        self.speed += self.speed_increase_per_frame
        if self.speed_cap_enabled:
            self.speed = min(self.speed, self.MAX_SPEED)
        self.player.update()

        self._spawn_timer += 1
        if self._spawn_timer >= self.spawn_interval:
            self._spawn_timer = 0
            self.obstacles.append(Obstacle(self.width, self.ground_y, self.speed))

        previous_x = [obstacle.x for obstacle in self.obstacles]
        for obstacle in self.obstacles:
            obstacle.move()
            obstacle.speed = self.speed

        player_rect = self.player.rect()
        for obstacle, prev_x in zip(self.obstacles, previous_x):
            if self._swept_rect(obstacle, prev_x).colliderect(player_rect):
                self.state = GAME_OVER
                self.game_over_time = pygame.time.get_ticks()
                self.sounds.play("game_over")
                return

        for obstacle in self.obstacles:
            if not obstacle.scored and obstacle.x + obstacle.width < self.player.x:
                obstacle.scored = True
                self.score += 1
                self.sounds.play("score")

        self.obstacles = [o for o in self.obstacles if not o.off_screen()]

        self.distance += self.speed

    def _swept_rect(self, obstacle, prev_x):
        left = math.floor(min(prev_x, obstacle.x))
        right = math.ceil(max(prev_x, obstacle.x) + obstacle.width)
        return pygame.Rect(left, obstacle.y, right - left, obstacle.height)

    def _blit_centered(self, screen, font, text, center_y, color=WHITE):
        surface = font.render(text, True, color)
        screen.blit(surface, surface.get_rect(center=(self.width // 2, center_y)))

    def render(self, screen):
        pygame.draw.line(screen, BROWN, (0, self.ground_y), (self.width, self.ground_y), 4)

        pygame.draw.rect(screen, WHITE, self.player.rect())
        for obstacle in self.obstacles:
            pygame.draw.rect(screen, DARK_GREEN, obstacle.rect())

        score_text = self.font.render(f"Score: {self.score}", True, (0, 0, 0))
        screen.blit(score_text, (10, 10))

        difficulty_text = self.font.render(f"Difficulty: {self.difficulty}", True, (0, 0, 0))
        screen.blit(difficulty_text, difficulty_text.get_rect(topright=(self.width - 10, 10)))

        if self.state == GAME_OVER:
            screen.blit(self.overlay, (0, 0))
            self._blit_centered(screen, self.title_font, "GAME OVER", 120)
            self._blit_centered(screen, self.font, f"Final score: {self.score}  ({self.difficulty})", 190)
            options = "   ".join(
                f"{pygame.key.name(preset['key'])} - {name}" for name, preset in DIFFICULTIES.items()
            )
            self._blit_centered(screen, self.small_font, f"Play again:  {options}", 250)
            self._blit_centered(screen, self.small_font, "Q / Esc - Quit", 285)
