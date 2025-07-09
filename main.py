import pygame
import sys
import random
import time
from datetime import datetime
import os
import math

# Initialize pygame
pygame.init()

# Constants
GRID_SIZE = 7
CELL_SIZE = 80
MARGIN = 10
SCREEN_WIDTH = GRID_SIZE * CELL_SIZE + (GRID_SIZE + 1) * MARGIN
SCREEN_HEIGHT = GRID_SIZE * CELL_SIZE + (GRID_SIZE + 1) * MARGIN + 100  # Extra space for UI
CELL_SIZE = 80
GOLD = (255, 215, 0)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
LIGHT_GREEN = (100, 255, 100)
GOLD = (255, 215, 0)

# Game parameters
MAX_MOVES = 10
FRUIT_GOAL = 75
FRUITS_PER_GAME = 3  # Number of fruit types to use in each game

# Star rating thresholds
STAR_THRESHOLDS = [
    (0, 0),     # 0 stars: 0-85 points
    (86, 1),    # 1 star: 86-95 points
    (96, 2),    # 2 stars: 96-105 points
    (106, 3)    # 3 stars: 106+ points
]


# Load images
def load_image(filename, subdirectory=None):
    if subdirectory:
        path = os.path.join('assets', subdirectory, filename)
    else:
        path = os.path.join('assets', filename)
    try:
        image = pygame.image.load(path)
        return pygame.transform.scale(image, (CELL_SIZE - 10, CELL_SIZE - 10))
    except pygame.error as e:
        print(f"Error loading image {filename}: {e}")
        # Create a colored square as fallback
        surface = pygame.Surface((CELL_SIZE - 10, CELL_SIZE - 10))
        surface.fill((255, 0, 0))
        return surface


# Load all available fruit images from assets/fruits directory
def load_all_fruits():
    all_fruits = {}
    try:
        fruits_dir = os.path.join('assets', 'fruits')
        # Create the directory if it doesn't exist
        if not os.path.exists(fruits_dir):
            print("Fruits directory not found. Creating it.")
            os.makedirs(fruits_dir, exist_ok=True)

        for filename in os.listdir(fruits_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                fruit_name = os.path.splitext(filename)[0]  # Remove extension
                all_fruits[fruit_name] = load_image(filename, 'fruits')
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error accessing fruits directory: {e}")
        # Fallback to default fruits
        all_fruits = {
            'apple': load_image('apple.png'),
            'orange': load_image('orange.png'),
            'pear': load_image('pear.png')
        }

    # Ensure we have at least 3 fruits
    if len(all_fruits) < FRUITS_PER_GAME:
        print(f"Not enough fruit images found. Need at least {FRUITS_PER_GAME}.")
        # Create some colored squares as fallback
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        for i in range(FRUITS_PER_GAME - len(all_fruits)):
            surface = pygame.Surface((CELL_SIZE - 10, CELL_SIZE - 10))
            surface.fill(colors[i % len(colors)])
            all_fruits[f'fruit{i + 1}'] = surface

    return all_fruits

# Load all available fruits
ALL_FRUIT_IMAGES = load_all_fruits()

# Mouse and kitty images
MOUSE_IMAGE = load_image('mouse.png')
KITTY_IMAGE = load_image('kitty.png')
ARROW_IMAGE = load_image('arrow_right.png')

# Create star images
def create_star_image(filled=True, size=50):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    if filled:
        color = GOLD
    else:
        color = (100, 100, 100)  # Gray for empty star

    # Draw a simple star
    points = []
    for i in range(5):
        # Outer point
        angle = math.pi * 2 * i / 5 - math.pi / 2
        points.append((size / 2 + size / 2 * math.cos(angle), size / 2 + size / 2 * math.sin(angle)))
        # Inner point
        angle += math.pi / 5
        points.append((size / 2 + size / 4 * math.cos(angle), size / 2 + size / 4 * math.sin(angle)))

    pygame.draw.polygon(surface, color, points)
    return surface

# Star images
EMPTY_STAR = create_star_image(filled=False)
FILLED_STAR = create_star_image(filled=True)

# Calculate angle between two points
def calculate_angle(start_pos, end_pos):
    dx = end_pos[1] - start_pos[1]  # Column difference (x)
    dy = end_pos[0] - start_pos[0]  # Row difference (y)
    angle = math.degrees(math.atan2(dy, dx))
    return angle


# Game class initialization
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Fruit Collection Game")
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        self.large_font = pygame.font.SysFont("Arial", 36)
        
        # Create collect button
        self.collect_button_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 60, 
            SCREEN_HEIGHT - 50, 
            120, 
            40
        )
        
        # Load best score and time
        self.best_score = 0
        self.best_time = float('inf')
        self.load_best_score()
        
        self.reset_game()
        
    def reset_game(self):
        # Select random fruit types for this game
        self.select_game_fruits()
        
        # Initialize game state
        self.board = [[random.choice(self.fruits) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.mice = []  # List to store mouse positions [(x, y), ...]
        self.selected_cells = []  # List to store selected cells
        self.score = 0
        self.fruits_collected = 0
        self.moves = 0
        self.game_over = False
        self.game_won = False
        self.final_move = False  # Flag to track if this is the final move
        self.start_time = time.time()
        self.elapsed_time = 0
        self.stars_earned = 0
        self.show_results = False
        self.should_add_mouse = False  # Flag to track if we should add a mouse after animation
        
        # Animation variables
        self.dim_alpha = 0  # Opacity of the dim overlay (0-180)
        self.panel_y_offset = -400  # Start position off-screen
        self.animation_start_time = 0
        self.animation_in_progress = False
        
        # Score counter animation
        self.counter_animation_active = False
        self.counter_start_time = 0
        self.displayed_score = 0
        self.stars_shown = 0
        
        # Kitty movement animation
        self.kitty_animation_active = False
        self.kitty_animation_start_time = 0
        self.kitty_start_pos = None
        self.kitty_target_pos = None
        self.kitty_current_pos = None  # Floating point position for smooth animation
        self.animation_path = []  # Path of cells for kitty to follow
        self.current_path_index = 0  # Current position in the animation path
        
        # Fruit replacement animation
        self.fruit_replacement_active = False
        self.fruit_replacement_start_time = 0
        self.cells_to_replace = []
        self.old_kitty_pos = None
        
        # Score animation
        self.score_animation_active = False
        self.total_points_to_add = 0
        self.points_added_so_far = 0
        self.points_popup_text = ""
        self.points_popup_alpha = 255
        self.points_popup_time = 0
        
        # Place kitty in the middle of the board
        self.kitty_pos = (GRID_SIZE // 2, GRID_SIZE // 2)  # (3,3) for a 7x7 grid
        
        # Remove fruit from kitty's position
        kitty_row, kitty_col = self.kitty_pos
        self.board[kitty_row][kitty_col] = None
    
    def select_game_fruits(self):
        # Select random fruit types for this game
        all_fruit_names = list(ALL_FRUIT_IMAGES.keys())
        # Ensure we have enough fruits to choose from
        if len(all_fruit_names) <= FRUITS_PER_GAME:
            self.fruits = all_fruit_names
        else:
            self.fruits = random.sample(all_fruit_names, FRUITS_PER_GAME)
        
        # Create a dictionary of fruit images for this game
        self.fruit_images = {fruit: ALL_FRUIT_IMAGES[fruit] for fruit in self.fruits}
        
        print(f"Selected fruits for this game: {self.fruits}")
        
    def add_mouse(self):
        # Add a mouse to a random empty cell if there are fewer than 3 mice
        if len(self.mice) < 3:
            empty_cells = [(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE) 
                          if (x, y) not in self.mice and (x, y) != self.kitty_pos]
            if empty_cells:
                pos = random.choice(empty_cells)
                self.mice.append(pos)
                # Remove fruit under mouse
                row, col = pos
                self.board[row][col] = None
    
    def is_adjacent_to_kitty(self, row, col):
        # Check if the cell is adjacent to the kitty (including diagonals)
        kitty_row, kitty_col = self.kitty_pos
        return abs(row - kitty_row) <= 1 and abs(col - kitty_col) <= 1 and (row, col) != self.kitty_pos

# Constants needed for this file
GRID_SIZE = 7
SCREEN_WIDTH = GRID_SIZE * 80 + (GRID_SIZE + 1) * 10
SCREEN_HEIGHT = GRID_SIZE * 80 + (GRID_SIZE + 1) * 10 + 100
FRUITS_PER_GAME = 3

# Mock objects for the file to run independently
class MockImage:
    def __init__(self):
        pass
        
ALL_FRUIT_IMAGES = {"apple": MockImage(), "orange": MockImage(), "banana": MockImage()} 
