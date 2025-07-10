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

    def is_valid_selection(self, row, col):
        # Check if the cell can be selected

        # Never allow selecting the kitty's current position
        if (row, col) == self.kitty_pos:
            return False

        # If this is the first selection, it must be adjacent to the kitty
        if not self.selected_cells:
            return self.is_adjacent_to_kitty(row, col)

        # For subsequent selections, check if it's adjacent to the last selected cell
        last_row, last_col = self.selected_cells[-1]

        # Check if it's adjacent to the last selected cell (including diagonals)
        if abs(row - last_row) <= 1 and abs(col - last_col) <= 1:
            # Check if it's a mouse (can always be selected)
            if (row, col) in self.mice:
                return (row, col) not in self.selected_cells  # Just make sure we haven't selected it already

            # If not a mouse, check if it's the same fruit type as the first selection
            if (row, col) not in self.selected_cells:  # Make sure it's not already selected
                # Get the first fruit in the chain (skip mice)
                first_fruit = None
                for cell_row, cell_col in self.selected_cells:
                    if (cell_row, cell_col) not in self.mice and self.board[cell_row][cell_col] is not None:
                        first_fruit = self.board[cell_row][cell_col]
                        break

                # If we couldn't find a fruit in the chain yet, this is the first fruit
                if first_fruit is None:
                    return True

                current_fruit = self.board[row][col]
                # Make sure it's the same fruit type (if it's not None)
                return current_fruit is None or current_fruit == first_fruit

        return False

    def is_mouse_on_path(self):
        # Check if the selected path goes through any mice
        for mouse in self.mice:
            if mouse in self.selected_cells:
                return True
        return False

    def is_adjacent_to_kitty(self, row, col):
        # Check if the cell is adjacent to the kitty (including diagonals)
        kitty_row, kitty_col = self.kitty_pos
        return abs(row - kitty_row) <= 1 and abs(col - kitty_col) <= 1 and (row, col) != self.kitty_pos
    
    def collect_fruits(self):
        # Collect selected fruits, remove mice on path, and update score
        if len(self.selected_cells) > 1:  # Need at least 2 fruits to collect
            # Calculate points to add
            fruit_points = len(self.selected_cells)
            mice_caught = sum(1 for mouse in self.mice if mouse in self.selected_cells)
            mouse_points = mice_caught * 4
            self.total_points_to_add = fruit_points + mouse_points
            
            # Set up score animation
            self.score_animation_active = True
            self.points_added_so_far = 0
            self.displayed_score = self.fruits_collected
            self.points_popup_text = f"+{self.total_points_to_add}"
            self.points_popup_alpha = 255
            self.points_popup_time = time.time()
            
            # Store old kitty position to fill with fruit later
            self.old_kitty_pos = self.kitty_pos
            
            # Start kitty movement animation through the selected path
            if self.selected_cells:
                # Create animation path starting from kitty's current position
                self.animation_path = [self.kitty_pos] + self.selected_cells
                self.current_path_index = 0  # Start at the beginning of the path
                
                # Set up initial animation segment
                self.kitty_start_pos = self.animation_path[0]
                self.kitty_target_pos = self.animation_path[1]
                self.kitty_current_pos = list(self.kitty_start_pos)  # Convert to list for floating point
                self.kitty_animation_active = True
                self.kitty_animation_start_time = time.time()
                
                # Store cells that need to be replaced with new fruits later
                self.cells_to_replace = self.selected_cells.copy()
            
            # Increment moves
            self.moves += 1
            
            # We'll add a mouse after the animation completes, not here
            # Store if we need to add a mouse
            self.should_add_mouse = (self.moves % 2 == 0)
                
            # Check if this is the final move (but don't end the game yet)
            if self.moves >= MAX_MOVES:
                self.elapsed_time = time.time() - self.start_time
                # Set a flag to indicate this is the final move
                # We'll handle the game over state after the animation completes
                self.final_move = True
                
        # Clear selection
        self.selected_cells = []

        def calculate_stars(self):
        # Calculate stars based on score
        self.stars_earned = 0
        if self.fruits_collected < FRUIT_GOAL:
            # Game lost, no stars
            self.stars_earned = 0
        else:
            # Game won, calculate stars based on score
            for threshold, stars in STAR_THRESHOLDS:
                if self.fruits_collected >= threshold:
                    self.stars_earned = stars
    
    def load_best_score(self):
        try:
            with open("game_history.txt", "r") as file:
                lines = file.readlines()
                for line in lines:
                    parts = line.strip().split(", ")
                    if len(parts) >= 4:  # Ensure we have enough parts
                        try:
                            score = int(parts[1].split(": ")[1])
                            time_str = parts[3].split(": ")[1]
                            time_val = sum(float(x) * 60 ** i for i, x in enumerate(reversed(time_str.split(":"))))
                            
                            # Update best score if higher
                            if score > self.best_score:
                                self.best_score = score
                                
                            # Update best time if this score is >= goal and time is better
                            if score >= FRUIT_GOAL and time_val < self.best_time:
                                self.best_time = time_val
                        except (ValueError, IndexError):
                            continue
        except FileNotFoundError:
            pass  # No history file yet
    
    def save_game_history(self):
        # Save game history to file
        with open("game_history.txt", "a") as file:
            date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            minutes = int(self.elapsed_time) // 60
            seconds = int(self.elapsed_time) % 60
            time_str = f"{minutes}:{seconds:02d}"
            file.write(f"{date_time}, Score: {self.fruits_collected}, Moves: {self.moves}, Time: {time_str}, Stars: {self.stars_earned}\n")
            
        # Update best score and time
        if self.fruits_collected > self.best_score:
            self.best_score = self.fruits_collected
            
        if self.game_won and self.elapsed_time < self.best_time:
            self.best_time = self.elapsed_time

    def draw_board(self):
        # Fill the background
        self.screen.fill(WHITE)

        # Draw the grid and fruits
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                # Calculate position
                x = col * (CELL_SIZE + MARGIN) + MARGIN
                y = row * (CELL_SIZE + MARGIN) + MARGIN

                # Draw cell background
                cell_color = GRAY

                # Highlight selected cells
                if (row, col) in self.selected_cells:
                    if (row, col) == self.selected_cells[-1]:
                        cell_color = (100, 100, 255)  # Light blue for most recent
                    else:
                        cell_color = BLUE

                pygame.draw.rect(self.screen, cell_color, (x, y, CELL_SIZE, CELL_SIZE))

                # Draw fruit image (if there is one and no mouse or kitty)
                fruit_type = self.board[row][col]
                if fruit_type is not None and (row, col) not in self.mice and (row, col) != self.kitty_pos:
                    fruit_image = self.fruit_images[fruit_type]
                    fruit_rect = fruit_image.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                    self.screen.blit(fruit_image, fruit_rect)

                # Draw mouse if present
                if (row, col) in self.mice:
                    mouse_rect = MOUSE_IMAGE.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                    self.screen.blit(MOUSE_IMAGE, mouse_rect)

        # Update kitty animation if active
        if self.kitty_animation_active:
            self.update_kitty_animation()

        # Update fruit replacement animation if active
        if self.fruit_replacement_active:
            self.update_fruit_replacement()

        # Update score animation if active
        if self.score_animation_active:
            self.update_score_animation()

        # Draw kitty at its current position (animated or static)
        if self.kitty_animation_active:
            # Draw kitty at animated position
            row, col = self.kitty_current_pos
            x = col * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2
            y = row * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2
            kitty_rect = KITTY_IMAGE.get_rect(center=(x, y))
            self.screen.blit(KITTY_IMAGE, kitty_rect)
        else:
            # Draw kitty at static position
            row, col = self.kitty_pos
            x = col * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2
            y = row * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2
            kitty_rect = KITTY_IMAGE.get_rect(center=(x, y))
            self.screen.blit(KITTY_IMAGE, kitty_rect)

        # Draw direction arrows between selected cells
        self.draw_direction_arrows()

        # Draw UI elements
        current_time = time.time() - self.start_time if not self.game_over else self.elapsed_time

        # Draw score and goal
        score_text = self.font.render(f"Score: {self.displayed_score}/{FRUIT_GOAL}", True, BLACK)
        score_rect = score_text.get_rect(topleft=(20, SCREEN_HEIGHT - 80))
        self.screen.blit(score_text, score_rect)

        # Draw points popup if active
        if self.score_animation_active and self.points_popup_alpha > 0:
            popup_font = self.font
            popup_text = popup_font.render(self.points_popup_text, True, (50, 205, 50))
            popup_text.set_alpha(self.points_popup_alpha)
            # Position next to score
            popup_rect = popup_text.get_rect(left=score_rect.right + 10, centery=score_rect.centery)
            self.screen.blit(popup_text, popup_rect)

        # Draw timer
        minutes = int(current_time) // 60
        seconds = int(current_time) % 60
        time_text = self.font.render(f"Time: {minutes}:{seconds:02d}", True, BLACK)
        self.screen.blit(time_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 80))

        # Draw moves
        moves_text = self.small_font.render(f"Moves: {self.moves}/{MAX_MOVES}", True,
                                            RED if self.moves >= MAX_MOVES - 2 else BLACK)
        self.screen.blit(moves_text, (20, SCREEN_HEIGHT - 40))

        # Draw best score/time
        if self.best_score > 0:
            best_score_text = self.small_font.render(f"Best: {self.best_score} points", True, BLUE)
            self.screen.blit(best_score_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 40))

        # Draw collect button
        button_color = LIGHT_GREEN if len(self.selected_cells) > 1 else GRAY
        pygame.draw.rect(self.screen, button_color, self.collect_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, BLACK, self.collect_button_rect, 2, border_radius=5)

        collect_text = self.font.render("Collect", True, BLACK)
        text_rect = collect_text.get_rect(center=self.collect_button_rect.center)
        self.screen.blit(collect_text, text_rect)

        # Draw results screen if game is over
        if self.game_over:
            if self.animation_in_progress:
                self.update_animation()
            self.draw_results_screen()

    def draw_direction_arrows(self):
        # Draw arrows showing the direction between consecutive selected cells
        if not self.selected_cells:
            return

        # First, draw an arrow from kitty's position to the first selected cell
        start_cell = self.kitty_pos
        end_cell = self.selected_cells[0]

        # Calculate center positions of cells
        start_x = start_cell[1] * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2
        start_y = start_cell[0] * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2
        end_x = end_cell[1] * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2
        end_y = end_cell[0] * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2

        # Calculate midpoint between cells for arrow placement
        mid_x = (start_x + end_x) // 2
        mid_y = (start_y + end_y) // 2

        # Calculate angle between cells
        angle = calculate_angle(start_cell, end_cell)

        # Rotate arrow image
        rotated_arrow = pygame.transform.rotate(ARROW_IMAGE, -angle)  # Negative for clockwise rotation
        arrow_rect = rotated_arrow.get_rect(center=(mid_x, mid_y))

        # Draw arrow
        self.screen.blit(rotated_arrow, arrow_rect)

        # Then draw arrows between consecutive selected cells
        if len(self.selected_cells) < 2:
            return

        for i in range(len(self.selected_cells) - 1):
            start_cell = self.selected_cells[i]
            end_cell = self.selected_cells[i + 1]

            # Calculate center positions of cells
            start_x = start_cell[1] * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2
            start_y = start_cell[0] * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2
            end_x = end_cell[1] * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2
            end_y = end_cell[0] * (CELL_SIZE + MARGIN) + MARGIN + CELL_SIZE // 2

            # Calculate midpoint between cells for arrow placement
            mid_x = (start_x + end_x) // 2
            mid_y = (start_y + end_y) // 2

            # Calculate angle between cells
            angle = calculate_angle(start_cell, end_cell)

            # Rotate arrow image
            rotated_arrow = pygame.transform.rotate(ARROW_IMAGE, -angle)  # Negative for clockwise rotation
            arrow_rect = rotated_arrow.get_rect(center=(mid_x, mid_y))

            # Draw arrow
            self.screen.blit(rotated_arrow, arrow_rect)

    def draw_results_screen(self):
        # Create a semi-transparent overlay with current alpha
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.dim_alpha))  # Variable opacity black
        self.screen.blit(overlay, (0, 0))

        # Create results panel
        panel_width = 400
        panel_height = 300
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = self.panel_y_offset

        # Draw panel background
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_width, panel_height), border_radius=10)
        pygame.draw.rect(self.screen, BLACK, (panel_x, panel_y, panel_width, panel_height), 2, border_radius=10)

        # Draw game result
        if self.fruits_collected >= FRUIT_GOAL:
            result_text = self.large_font.render("VICTORY!", True, GREEN)
        else:
            result_text = self.large_font.render("GAME OVER", True, RED)

        result_rect = result_text.get_rect(center=(panel_x + panel_width // 2, panel_y + 40))
        self.screen.blit(result_text, result_rect)

        # Update counter animation if active
        if self.counter_animation_active:
            self.update_counter_animation()

        # Draw score with counter animation
        score_text = self.font.render(f"Fruits collected: {self.displayed_score}", True, BLACK)
        score_rect = score_text.get_rect(center=(panel_x + panel_width // 2, panel_y + 80))
        self.screen.blit(score_text, score_rect)

        # Draw stars
        star_y = panel_y + 130
        star_spacing = 70

        # Draw 3 stars (filled or empty based on animated score)
        for i in range(3):
            star_x = panel_x + panel_width // 2 - star_spacing + i * star_spacing
            if i < self.stars_shown:
                star_image = FILLED_STAR
            else:
                star_image = EMPTY_STAR

            star_rect = star_image.get_rect(center=(star_x, star_y))
            self.screen.blit(star_image, star_rect)

        # Draw star thresholds
        threshold_text = self.small_font.render(
            f"0★: 75-85 | 1★: 86-95 | 2★: 96-105 | 3★: 106+",
            True, BLACK
        )
        threshold_rect = threshold_text.get_rect(center=(panel_x + panel_width // 2, panel_y + 180))
        self.screen.blit(threshold_text, threshold_rect)

        # Draw time
        minutes = int(self.elapsed_time) // 60
        seconds = int(self.elapsed_time) % 60
        time_text = self.font.render(f"Time: {minutes}:{seconds:02d}", True, BLACK)
        time_rect = time_text.get_rect(center=(panel_x + panel_width // 2, panel_y + 220))
        self.screen.blit(time_text, time_rect)

        # Draw restart instruction
        restart_text = self.font.render("Press R to restart", True, BLUE)
        restart_rect = restart_text.get_rect(center=(panel_x + panel_width // 2, panel_y + 260))
        self.screen.blit(restart_text, restart_rect)


# Mock objects for the file to run independently
class MockImage:
    def __init__(self):
        pass
        
ALL_FRUIT_IMAGES = {"apple": MockImage(), "orange": MockImage(), "banana": MockImage()}

# Mock functions
def calculate_angle(start_pos, end_pos):
    return 0

# Mock images
MOUSE_IMAGE = None
KITTY_IMAGE = None
ARROW_IMAGE = None
EMPTY_STAR = None
FILLED_STAR = None
