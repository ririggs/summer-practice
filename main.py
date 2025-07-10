import pygame
import sys
import random
import time
from datetime import datetime
import os
import math
import json

# Initialize pygame
pygame.init()
pygame.mixer.init()  # Initialize the mixer module for sound playback

# Constants
GRID_SIZE = 7
CELL_SIZE = 80
MARGIN = 10
SCREEN_WIDTH = GRID_SIZE * CELL_SIZE + (GRID_SIZE + 1) * MARGIN
SCREEN_HEIGHT = GRID_SIZE * CELL_SIZE + (GRID_SIZE + 1) * MARGIN + 100  # Extra space for UI

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
LIGHT_GREEN = (100, 255, 100)
GOLD = (255, 215, 0)
LIGHT_BLUE = (100, 100, 255)
DARK_BLUE = (50, 50, 200)

# Game parameters
MAX_MOVES = 10
FOOD_GOAL = 75
FOOD_ITEMS_PER_GAME = 3  # Number of food types to use in each game
SETTINGS_FILE = "game_settings.json"  # File to store settings
HISTORY_FILE = "game_history.json"   # File to store game history

# Star rating thresholds
STAR_THRESHOLDS = [
    (0, 0),     # 0 stars: 0-74 points
    (75, 1),    # 1 star: 75-95 points
    (96, 2),    # 2 stars: 96-120 points
    (121, 3)    # 3 stars: 121+ points
]

# Default game settings
DEFAULT_SETTINGS = {
    "sound_volume": 70,
    "music_volume": 50,
    "collect_key": pygame.K_SPACE
}

# Load settings from file or use defaults
def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as file:
            data = json.load(file)
            # Convert collect_key back to integer (JSON stores it as string)
            if "collect_key" in data:
                data["collect_key"] = int(data["collect_key"])
            return data
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"Error loading settings: {e}. Using defaults.")
        # Create settings file with defaults if it doesn't exist
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

# Save settings to file
def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as file:
            # Convert settings to JSON-compatible format
            json_settings = settings.copy()
            # Store collect_key as string (JSON can't store pygame key constants)
            json_settings["collect_key"] = str(settings["collect_key"])
            json.dump(json_settings, file, indent=4)
            print("Settings saved successfully")
    except Exception as e:
        print(f"Error saving settings: {e}")

# Load game history from file
def load_game_history():
    try:
        with open(HISTORY_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading game history: {e}. Creating new history.")
        return []

# Save game history to file
def save_game_history(history):
    try:
        with open(HISTORY_FILE, "w") as file:
            json.dump(history, file, indent=4)
            print("Game history saved successfully")
    except Exception as e:
        print(f"Error saving game history: {e}")

# Get best score from history
def get_best_score():
    history = load_game_history()
    if not history:
        return 0, float('inf')
    
    best_score = max([game["score"] for game in history])
    
    # Find best time for winning games
    winning_games = [game for game in history if game["score"] >= FOOD_GOAL]
    best_time = min([game["time"] for game in winning_games]) if winning_games else float('inf')
    
    return best_score, best_time

# Game settings (load from file or use defaults)
SETTINGS = load_settings()

# Game instructions in English
INSTRUCTIONS = [
    "How to play:",
    "",
    "1. Connect the same types of food to make the cat eat them.",
    "2. Mice give 5 points each.",
    "3. Bones take away 10 points each.",
    "4. Collect 75 points to win.",
    "5. You have only 10 moves.",
    "",
    "Control:",
    "- Click on the food to select it.",
    "- Press the 'Collect' button to collect the food.",
    "- Press ESC to return to the menu."
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

# Load all available food images from assets/food directory
def load_all_foods():
    all_foods = {}
    try:
        food_dir = os.path.join('assets', 'food')
        # Create the directory if it doesn't exist
        if not os.path.exists(food_dir):
            print("Food directory not found. Creating it.")
            os.makedirs(food_dir, exist_ok=True)
            
        for filename in os.listdir(food_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                food_name = os.path.splitext(filename)[0]  # Remove extension
                all_foods[food_name] = load_image(filename, 'food')
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error accessing food directory: {e}")
        # Fallback to default foods
        all_foods = {
            'ball': load_image('ball.png'),
            'bowl': load_image('bowl.png'),
            'can': load_image('can.png')
        }
    
    # Ensure we have at least 3 foods
    if len(all_foods) < FOOD_ITEMS_PER_GAME:
        print(f"Not enough food images found. Need at least {FOOD_ITEMS_PER_GAME}.")
        # Create some colored squares as fallback
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        for i in range(FOOD_ITEMS_PER_GAME - len(all_foods)):
            surface = pygame.Surface((CELL_SIZE - 10, CELL_SIZE - 10))
            surface.fill(colors[i % len(colors)])
            all_foods[f'food{i+1}'] = surface
    
    return all_foods

# Load all available foods
ALL_FOOD_IMAGES = load_all_foods()

# Mouse and kitty images
MOUSE_IMAGE = load_image('mouse.png')
KITTY_IMAGE = load_image('kitty.png')
ARROW_IMAGE = load_image('arrow_right.png')
BONES_IMAGE = load_image('bones.png')  # Load bones image

# Load sound effects
def load_sound(filename):
    path = os.path.join('assets', 'sounds', filename)
    try:
        sound = pygame.mixer.Sound(path)
        return sound
    except pygame.error as e:
        print(f"Error loading sound {filename}: {e}")
        return None

# Background music
BACKGROUND_MUSIC = os.path.join('assets', 'sounds', 'background_sound.mp3')
TAP_SOUND = load_sound('tap_sound.mp3')
MEOW_SOUND = load_sound('cat_meow.mp3')
PURR_SOUND = load_sound('cat_purr.mp3')
BONE_SOUND = load_sound('bone_sound.mp3')
MOUSE_SOUND = load_sound('mouse_sound.mp3')

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
        points.append((size/2 + size/2 * math.cos(angle), size/2 + size/2 * math.sin(angle)))
        # Inner point
        angle += math.pi / 5
        points.append((size/2 + size/4 * math.cos(angle), size/2 + size/4 * math.sin(angle)))
    
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

# Button class for menu
class Button:
    def __init__(self, x, y, width, height, text, font, normal_color=BLUE, hover_color=LIGHT_BLUE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.is_hovered = False
        self.text_surf = font.render(text, True, WHITE)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)
        
    def draw(self, screen):
        # Draw button with hover effect
        color = self.hover_color if self.is_hovered else self.normal_color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=10)
        screen.blit(self.text_surf, self.text_rect)
        
    def check_hover(self, pos):
        # Check if mouse is over button and update hover state
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(pos)
        # Return True if hover state changed
        return was_hovered != self.is_hovered
        
    def is_clicked(self, pos, event):
        # Check if button was clicked
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

class CircleButton:
    def __init__(self, x, y, radius, text, font, normal_color=BLUE, hover_color=LIGHT_BLUE, hover_text=""):
        self.x = x
        self.y = y
        self.radius = radius
        self.text = text
        self.font = font
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.is_hovered = False
        self.text_surf = font.render(text, True, WHITE)
        self.text_rect = self.text_surf.get_rect(center=(x, y))
        self.hover_text = hover_text
        self.hover_text_surf = None
        if hover_text:
            small_font = pygame.font.SysFont("Arial", 18)
            self.hover_text_surf = small_font.render(hover_text, True, BLACK, WHITE)
        
    def draw(self, screen):
        # Draw circular button with hover effect
        color = self.hover_color if self.is_hovered else self.normal_color
        pygame.draw.circle(screen, color, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, BLACK, (self.x, self.y), self.radius, 2)
        screen.blit(self.text_surf, self.text_rect)
        
        # Draw hover text if hovered
        if self.is_hovered and self.hover_text_surf:
            hover_rect = self.hover_text_surf.get_rect()
            
            # Position hover text below the button
            hover_rect.midtop = (self.x, self.y + self.radius + 5)
            
            # Make sure it doesn't go off-screen
            if hover_rect.right > SCREEN_WIDTH:
                hover_rect.right = SCREEN_WIDTH - 5
            if hover_rect.bottom > SCREEN_HEIGHT:
                hover_rect.bottom = SCREEN_HEIGHT - 5
                
            # Draw background for better visibility
            padding = 3
            bg_rect = hover_rect.inflate(padding * 2, padding * 2)
            pygame.draw.rect(screen, WHITE, bg_rect)
            pygame.draw.rect(screen, BLACK, bg_rect, 1)
            
            screen.blit(self.hover_text_surf, hover_rect)
        
    def check_hover(self, pos):
        # Check if mouse is over button and update hover state
        was_hovered = self.is_hovered
        distance = math.sqrt((pos[0] - self.x) ** 2 + (pos[1] - self.y) ** 2)
        self.is_hovered = distance <= self.radius
        # Return True if hover state changed
        return was_hovered != self.is_hovered
        
    def is_clicked(self, pos, event):
        # Check if button was clicked
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            distance = math.sqrt((pos[0] - self.x) ** 2 + (pos[1] - self.y) ** 2)
            return distance <= self.radius
        return False

# Slider control for settings
class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, step, initial_val, label, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.value = initial_val
        self.label = label
        self.font = font
        self.is_dragging = False
        
        # Calculate handle position
        self.handle_width = 20
        self.handle_height = height + 10
        self.update_handle_position()
        
    def update_handle_position(self):
        # Calculate handle position based on current value
        value_range = self.max_val - self.min_val
        position_ratio = (self.value - self.min_val) / value_range
        handle_x = self.rect.x + int(position_ratio * self.rect.width) - self.handle_width // 2
        self.handle_rect = pygame.Rect(handle_x, self.rect.y - 5, self.handle_width, self.handle_height)
        
    def draw(self, screen):
        # Draw slider track
        pygame.draw.rect(screen, GRAY, self.rect, border_radius=5)
        
        # Draw handle
        pygame.draw.rect(screen, BLUE, self.handle_rect, border_radius=5)
        pygame.draw.rect(screen, BLACK, self.handle_rect, 2, border_radius=5)
        
        # Draw label and value
        label_text = self.font.render(f"{self.label}: {self.value}", True, BLACK)
        label_rect = label_text.get_rect(bottomleft=(self.rect.x, self.rect.y - 10))
        screen.blit(label_text, label_rect)
        
        # Draw tick marks
        num_ticks = (self.max_val - self.min_val) // self.step + 1
        for i in range(num_ticks):
            tick_x = self.rect.x + (i * self.rect.width) // (num_ticks - 1)
            pygame.draw.line(screen, BLACK, (tick_x, self.rect.y + self.rect.height), 
                            (tick_x, self.rect.y + self.rect.height + 5), 2)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_rect.collidepoint(event.pos):
                self.is_dragging = True
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
        
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            # Calculate new value based on mouse position
            x_pos = max(self.rect.x, min(event.pos[0], self.rect.x + self.rect.width))
            position_ratio = (x_pos - self.rect.x) / self.rect.width
            new_value = self.min_val + position_ratio * (self.max_val - self.min_val)
            
            # Round to nearest step
            self.value = round(new_value / self.step) * self.step
            self.value = max(self.min_val, min(self.max_val, self.value))
            
            # Update handle position
            self.update_handle_position()
            return True
            
        return False

# Key binding control for settings
class KeyBindControl:
    def __init__(self, x, y, width, height, label, font, initial_key):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.font = font
        self.key = initial_key
        self.is_listening = False
        self.key_name = pygame.key.name(initial_key).upper()
        
    def draw(self, screen):
        # Draw background
        color = LIGHT_BLUE if self.is_listening else GRAY
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=5)
        
        # Draw label
        label_text = self.font.render(f"{self.label}:", True, BLACK)
        label_rect = label_text.get_rect(bottomleft=(self.rect.x, self.rect.y - 10))
        screen.blit(label_text, label_rect)
        
        # Draw current key
        key_text = self.font.render(self.key_name, True, BLACK)
        key_rect = key_text.get_rect(center=self.rect.center)
        screen.blit(key_text, key_rect)
        
        # Draw instruction if listening
        if self.is_listening:
            instruction_text = self.font.render("Press any key...", True, RED)
            instruction_rect = instruction_text.get_rect(midtop=(self.rect.centerx, self.rect.bottom + 10))
            screen.blit(instruction_text, instruction_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_listening = not self.is_listening
                return True
                
        elif event.type == pygame.KEYDOWN and self.is_listening:
            # Ignore ESC key as it's used for menu navigation
            if event.key != pygame.K_ESCAPE:
                self.key = event.key
                self.key_name = pygame.key.name(event.key).upper()
                self.is_listening = False
                return True
                
        return False

class Settings:
    def __init__(self, screen):
        self.screen = screen
        self.running = True
        self.font = pygame.font.SysFont("Arial", 24)
        self.title_font = pygame.font.SysFont("Arial", 36)
        
        # Create controls
        slider_width = 300
        slider_height = 20
        control_spacing = 80
        start_y = SCREEN_HEIGHT // 3
        
        self.sound_slider = Slider(
            SCREEN_WIDTH // 2 - slider_width // 2,
            start_y,
            slider_width,
            slider_height,
            0, 100, 10,
            SETTINGS["sound_volume"],
            "Sound Volume",
            self.font
        )
        
        self.music_slider = Slider(
            SCREEN_WIDTH // 2 - slider_width // 2,
            start_y + control_spacing,
            slider_width,
            slider_height,
            0, 100, 10,
            SETTINGS["music_volume"],
            "Music Volume",
            self.font
        )
        
        self.collect_key_control = KeyBindControl(
            SCREEN_WIDTH // 2 - slider_width // 2,
            start_y + 2 * control_spacing,
            slider_width,
            40,
            "Collect Key",
            self.font,
            SETTINGS["collect_key"]
        )
        
        # Create back button
        self.back_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT - 100,
            200,
            50,
            "Back",
            self.font
        )
        
    def run(self):
        clock = pygame.time.Clock()
        
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check for hover state changes
            hover_changed = self.back_button.check_hover(mouse_pos)
            
            # Play sound on hover change
            if hover_changed and TAP_SOUND:
                TAP_SOUND.play()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and not self.collect_key_control.is_listening:
                        self.save_settings()
                        self.running = False
                        return
                        
                # Handle slider and key bind events
                sound_changed = self.sound_slider.handle_event(event)
                music_changed = self.music_slider.handle_event(event)
                self.collect_key_control.handle_event(event)
                
                # Check back button
                if self.back_button.is_clicked(mouse_pos, event):
                    self.save_settings()
                    self.running = False
                    return
                    
                # Apply sound changes in real-time
                if sound_changed:
                    self.apply_sound_settings()
            
            # Update music volume in real-time
            pygame.mixer.music.set_volume(self.music_slider.value / 100)
            
            # Draw the settings screen
            self.screen.fill(WHITE)
            
            # Draw title
            title_text = self.title_font.render("Settings", True, DARK_BLUE)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 6))
            self.screen.blit(title_text, title_rect)
            
            # Draw controls
            self.sound_slider.draw(self.screen)
            self.music_slider.draw(self.screen)
            self.collect_key_control.draw(self.screen)
            self.back_button.draw(self.screen)
            
            pygame.display.flip()
            clock.tick(60)
    
    def apply_sound_settings(self):
        # Apply sound volume to all sound effects
        volume = self.sound_slider.value / 100
        if TAP_SOUND:
            TAP_SOUND.set_volume(volume)
        if MEOW_SOUND:
            MEOW_SOUND.set_volume(volume)
        if PURR_SOUND:
            PURR_SOUND.set_volume(volume)
        if BONE_SOUND:
            BONE_SOUND.set_volume(volume)
        if MOUSE_SOUND:
            MOUSE_SOUND.set_volume(volume)
    
    def save_settings(self):
        # Save settings to global settings dict
        SETTINGS["sound_volume"] = self.sound_slider.value
        SETTINGS["music_volume"] = self.music_slider.value
        SETTINGS["collect_key"] = self.collect_key_control.key
        
        # Apply sound settings
        self.apply_sound_settings()
        
        # Apply music settings
        pygame.mixer.music.set_volume(SETTINGS["music_volume"] / 100)
        
        # Save to file
        save_settings(SETTINGS)

class Records:
    def __init__(self, screen):
        self.screen = screen
        self.running = True
        self.font = pygame.font.SysFont("Arial", 24)
        self.title_font = pygame.font.SysFont("Arial", 36)
        self.small_font = pygame.font.SysFont("Arial", 18)
        
        # Create back button
        self.back_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT - 60,
            200,
            40,
            "Back",
            self.font
        )
        
        # Load game history
        self.history = load_game_history()
        
    def run(self):
        clock = pygame.time.Clock()
        
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check for hover state changes
            hover_changed = self.back_button.check_hover(mouse_pos)
            
            # Play sound on hover change
            if hover_changed and TAP_SOUND:
                TAP_SOUND.play()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        return
                        
                # Check back button
                if self.back_button.is_clicked(mouse_pos, event):
                    self.running = False
                    return
            
            # Draw the records screen
            self.screen.fill(WHITE)
            
            # Draw title
            title_text = self.title_font.render("Game Records", True, DARK_BLUE)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 40))
            self.screen.blit(title_text, title_rect)
            
            # Draw top-5 table
            self.draw_top_records()
            
            # Draw bar chart
            self.draw_bar_chart()
            
            # Draw back button
            self.back_button.draw(self.screen)
            
            pygame.display.flip()
            clock.tick(60)
    
    def draw_top_records(self):
        # Draw table header
        table_width = 600
        table_x = (SCREEN_WIDTH - table_width) // 2
        table_y = 100
        row_height = 40
        
        # Draw table background
        table_height = 6 * row_height  # Header + 5 rows
        pygame.draw.rect(self.screen, LIGHT_BLUE, (table_x, table_y, table_width, table_height), border_radius=5)
        pygame.draw.rect(self.screen, BLACK, (table_x, table_y, table_width, table_height), 2, border_radius=5)
        
        # Draw header
        header_y = table_y + 10
        headers = ["Rank", "Date", "Score", "Time", "Stars"]
        col_widths = [0.1, 0.4, 0.2, 0.15, 0.15]  # Proportions of table width
        
        for i, header in enumerate(headers):
            col_x = table_x + sum(col_widths[:i]) * table_width
            col_width = col_widths[i] * table_width
            text = self.font.render(header, True, BLACK)
            text_rect = text.get_rect(center=(col_x + col_width/2, header_y))
            self.screen.blit(text, text_rect)
        
        # Draw separator line
        pygame.draw.line(self.screen, BLACK, (table_x, table_y + row_height), (table_x + table_width, table_y + row_height), 2)
        
        # Sort history by score (descending)
        sorted_history = sorted(self.history, key=lambda x: x["score"], reverse=True)
        
        # Draw top 5 records
        for i in range(min(5, len(sorted_history))):
            record = sorted_history[i]
            row_y = table_y + (i + 1) * row_height + 10
            
            # Rank
            text = self.font.render(f"{i+1}", True, BLACK)
            col_x = table_x + col_widths[0] * table_width / 2
            text_rect = text.get_rect(center=(col_x, row_y))
            self.screen.blit(text, text_rect)
            
            # Date
            date_str = datetime.fromtimestamp(record["timestamp"]).strftime("%Y-%m-%d %H:%M")
            text = self.small_font.render(date_str, True, BLACK)
            col_x = table_x + col_widths[0] * table_width + col_widths[1] * table_width / 2
            text_rect = text.get_rect(center=(col_x, row_y))
            self.screen.blit(text, text_rect)
            
            # Score
            text = self.font.render(f"{record['score']}", True, BLACK)
            col_x = table_x + sum(col_widths[:2]) * table_width + col_widths[2] * table_width / 2
            text_rect = text.get_rect(center=(col_x, row_y))
            self.screen.blit(text, text_rect)
            
            # Time
            minutes = int(record["time"]) // 60
            seconds = int(record["time"]) % 60
            text = self.font.render(f"{minutes}:{seconds:02d}", True, BLACK)
            col_x = table_x + sum(col_widths[:3]) * table_width + col_widths[3] * table_width / 2
            text_rect = text.get_rect(center=(col_x, row_y))
            self.screen.blit(text, text_rect)
            
            # Stars
            stars_x = table_x + sum(col_widths[:4]) * table_width + col_widths[4] * table_width / 2
            self.draw_stars(stars_x, row_y, record["stars"])
    
    def draw_stars(self, x, y, stars_count):
        star_size = 20
        spacing = 5
        total_width = stars_count * star_size + (stars_count - 1) * spacing
        start_x = x - total_width / 2
        
        for i in range(stars_count):
            star_x = start_x + i * (star_size + spacing)
            star_rect = FILLED_STAR.get_rect(topleft=(star_x, y - star_size/2))
            star_image = pygame.transform.scale(FILLED_STAR, (star_size, star_size))
            self.screen.blit(star_image, star_rect)
    
    def draw_bar_chart(self):
        # Draw line graph of last 10 games
        chart_width = 600
        chart_height = 200
        chart_x = (SCREEN_WIDTH - chart_width) // 2
        chart_y = 350
        
        # Draw chart background
        pygame.draw.rect(self.screen, GRAY, (chart_x, chart_y, chart_width, chart_height), border_radius=5)
        pygame.draw.rect(self.screen, BLACK, (chart_x, chart_y, chart_width, chart_height), 2, border_radius=5)
        
        # Draw chart title
        title_text = self.font.render("Score History (Last 10 Games)", True, BLACK)
        title_rect = title_text.get_rect(midtop=(chart_x + chart_width/2, chart_y - 30))
        self.screen.blit(title_text, title_rect)
        
        # Get last 10 games
        recent_games = sorted(self.history, key=lambda x: x["timestamp"])[-10:]
        if not recent_games:
            # Draw "No data" message
            no_data_text = self.font.render("No game history data available", True, BLACK)
            no_data_rect = no_data_text.get_rect(center=(chart_x + chart_width/2, chart_y + chart_height/2))
            self.screen.blit(no_data_text, no_data_rect)
            return
        
        # Find max score for scaling
        max_score = max([game["score"] for game in recent_games])
        max_score = max(max_score, FOOD_GOAL)  # Ensure goal line is visible
        
        # Draw grid lines
        grid_color = (220, 220, 220)  # Light gray
        grid_steps = 5
        for i in range(grid_steps + 1):
            # Horizontal grid lines
            y_pos = chart_y + chart_height - 30 - (i * (chart_height - 50) / grid_steps)
            pygame.draw.line(self.screen, grid_color, (chart_x + 10, y_pos), (chart_x + chart_width - 10, y_pos), 1)
            
            # Draw y-axis labels
            score_value = int((i / grid_steps) * max_score)
            score_label = self.small_font.render(str(score_value), True, BLACK)
            label_rect = score_label.get_rect(midright=(chart_x + 5, y_pos))
            self.screen.blit(score_label, label_rect)
        
        # Calculate positions for dots
        dot_radius = 6
        dot_positions = []
        point_spacing = (chart_width - 40) / (len(recent_games) - 1) if len(recent_games) > 1 else 0
        bar_bottom = chart_y + chart_height - 30
        
        for i, game in enumerate(recent_games):
            # Calculate dot position
            score = game["score"]
            x_pos = chart_x + 20 + (i * point_spacing) if len(recent_games) > 1 else chart_x + chart_width / 2
            y_pos = bar_bottom - (score / max_score) * (chart_height - 50)
            
            dot_positions.append((x_pos, y_pos, score))
            
            # Draw date below x-axis
            date_str = datetime.fromtimestamp(game["timestamp"]).strftime("%m-%d")
            date_text = self.small_font.render(date_str, True, BLACK)
            date_rect = date_text.get_rect(midtop=(x_pos, bar_bottom + 5))
            self.screen.blit(date_text, date_rect)
        
        # Draw connecting lines between dots
        if len(dot_positions) > 1:
            for i in range(len(dot_positions) - 1):
                start_x, start_y, _ = dot_positions[i]
                end_x, end_y, _ = dot_positions[i + 1]
                pygame.draw.line(self.screen, BLUE, (start_x, start_y), (end_x, end_y), 2)
        
        # Draw dots and score labels
        for x_pos, y_pos, score in dot_positions:
            # Draw dot with color based on whether goal was reached
            dot_color = GREEN if score >= FOOD_GOAL else BLUE
            pygame.draw.circle(self.screen, dot_color, (x_pos, y_pos), dot_radius)
            pygame.draw.circle(self.screen, BLACK, (x_pos, y_pos), dot_radius, 1)  # Outline
            
            # Draw score above dot
            score_text = self.small_font.render(str(score), True, BLACK)
            score_rect = score_text.get_rect(midbottom=(x_pos, y_pos - 10))
            
            # Draw white background behind text for better readability
            padding = 2
            bg_rect = score_rect.inflate(padding * 2, padding * 2)
            pygame.draw.rect(self.screen, WHITE, bg_rect)
            pygame.draw.rect(self.screen, BLACK, bg_rect, 1)
            
            self.screen.blit(score_text, score_rect)
        
        # Draw goal line
        goal_y = bar_bottom - (FOOD_GOAL / max_score) * (chart_height - 50)
        pygame.draw.line(self.screen, RED, (chart_x + 10, goal_y), (chart_x + chart_width - 10, goal_y), 2)
        
        # Draw goal label
        goal_text = self.small_font.render(f"Goal: {FOOD_GOAL}", True, RED)
        goal_rect = goal_text.get_rect(midright=(chart_x + chart_width - 15, goal_y - 5))
        self.screen.blit(goal_text, goal_rect)

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.running = True
        self.font = pygame.font.SysFont("Arial", 36)
        self.title_font = pygame.font.SysFont("Arial", 64)
        self.small_font = pygame.font.SysFont("Arial", 18)
        
        # Create buttons
        button_width = 300
        button_height = 60
        button_spacing = 30
        start_y = SCREEN_HEIGHT // 2 - 80  # Moved up to make room for Records button
        
        self.play_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            start_y,
            button_width,
            button_height,
            "Play Game",
            self.font
        )
        
        self.records_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            start_y + button_height + button_spacing,
            button_width,
            button_height,
            "Records",
            self.font
        )
        
        self.settings_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            start_y + 2 * (button_height + button_spacing),
            button_width,
            button_height,
            "Settings",
            self.font
        )
        
        self.quit_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            start_y + 3 * (button_height + button_spacing),
            button_width,
            button_height,
            "Quit",
            self.font
        )
        
        # Create How to Play button (question mark in upper right corner)
        self.help_button = CircleButton(
            SCREEN_WIDTH - 40,
            40,
            25,
            "?",
            self.font,
            normal_color=BLUE,
            hover_color=LIGHT_BLUE,
            hover_text="How to Play"
        )
        
        # Instructions panel state
        self.show_instructions = False
        
    def draw_instructions(self):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))
        
        # Draw instructions panel
        panel_width = 500
        panel_height = 400
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = (SCREEN_HEIGHT - panel_height) // 2
        
        # Draw panel background
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_width, panel_height), border_radius=10)
        pygame.draw.rect(self.screen, BLACK, (panel_x, panel_y, panel_width, panel_height), 2, border_radius=10)
        
        # Draw instructions title
        title_text = self.font.render("Instructions", True, DARK_BLUE)
        title_rect = title_text.get_rect(midtop=(panel_x + panel_width // 2, panel_y + 20))
        self.screen.blit(title_text, title_rect)
        
        # Draw instructions text
        line_height = 24
        for i, line in enumerate(INSTRUCTIONS):
            text = self.small_font.render(line, True, BLACK)
            rect = text.get_rect(topleft=(panel_x + 30, panel_y + 70 + i * line_height))
            self.screen.blit(text, rect)
        
        # Draw close button
        close_text = self.small_font.render("Close (ESC or click)", True, BLUE)
        close_rect = close_text.get_rect(midbottom=(panel_x + panel_width // 2, panel_y + panel_height - 20))
        self.screen.blit(close_text, close_rect)
        
    def run(self):
        # Start background music
        try:
            pygame.mixer.music.load(BACKGROUND_MUSIC)
            pygame.mixer.music.set_volume(SETTINGS["music_volume"] / 100)  # Use settings volume
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
        except pygame.error as e:
            print(f"Error playing background music: {e}")
            
        clock = pygame.time.Clock()
        
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check for hover state changes
            hover_changed = False
            
            if not self.show_instructions:
                hover_changed |= self.play_button.check_hover(mouse_pos)
                hover_changed |= self.records_button.check_hover(mouse_pos)
                hover_changed |= self.settings_button.check_hover(mouse_pos)
                hover_changed |= self.quit_button.check_hover(mouse_pos)
                hover_changed |= self.help_button.check_hover(mouse_pos)
                
                # Play sound on hover change
                if hover_changed and TAP_SOUND:
                    TAP_SOUND.play()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and self.show_instructions:
                        self.show_instructions = False
                    
                # Check button clicks if not showing instructions
                elif not self.show_instructions:
                    if self.play_button.is_clicked(mouse_pos, event):
                        # Start the game
                        game = Game()
                        game.run()
                        # When game exits, we're back at the menu
                    
                    elif self.records_button.is_clicked(mouse_pos, event):
                        # Show records screen
                        records_screen = Records(self.screen)
                        records_screen.run()
                        
                    elif self.settings_button.is_clicked(mouse_pos, event):
                        # Open settings screen
                        settings_screen = Settings(self.screen)
                        settings_screen.run()
                            
                    elif self.help_button.is_clicked(mouse_pos, event):
                        # Show instructions
                        self.show_instructions = True
                        if TAP_SOUND:
                            TAP_SOUND.play()
                        
                    elif self.quit_button.is_clicked(mouse_pos, event):
                        self.running = False
                        pygame.quit()
                        sys.exit()
                
                # Close instructions panel on click
                elif self.show_instructions and event.type == pygame.MOUSEBUTTONDOWN:
                    self.show_instructions = False
            
            # Draw the menu
            self.screen.fill(WHITE)
            
            # Draw title
            title_text = self.title_font.render("Kitty Food Game", True, DARK_BLUE)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
            self.screen.blit(title_text, title_rect)
            
            # Draw buttons if not showing instructions
            if not self.show_instructions:
                self.play_button.draw(self.screen)
                self.records_button.draw(self.screen)
                self.settings_button.draw(self.screen)
                self.quit_button.draw(self.screen)
                self.help_button.draw(self.screen)
            else:
                # Draw instructions panel
                self.draw_instructions()
            
            pygame.display.flip()
            clock.tick(60)

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
        self.best_score, self.best_time = get_best_score()
        
        # Start background music
        self.start_background_music()
        
        self.reset_game()
        
    def start_background_music(self):
        try:
            # If music is already playing, no need to restart it
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.load(BACKGROUND_MUSIC)
                pygame.mixer.music.set_volume(SETTINGS["music_volume"] / 100)  # Use settings volume
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
        except pygame.error as e:
            print(f"Error playing background music: {e}")
        
    def reset_game(self):
        # Select random food types for this game
        self.select_game_foods()
        
        # Initialize game state
        self.board = [[random.choice(self.foods) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.mice = []  # List to store mouse positions [(x, y), ...]
        self.bones = []  # List to store bone positions [(x, y), ...]
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
        self.should_add_bones = False  # Flag to track if we should add bones after animation
        self.chain_result_preview = 0  # Preview of the chain result
        
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
        
        # Remove food from kitty's position
        kitty_row, kitty_col = self.kitty_pos
        self.board[kitty_row][kitty_col] = None
    
    def select_game_foods(self):
        # Select random food types for this game
        all_food_names = list(ALL_FOOD_IMAGES.keys())
        # Ensure we have enough foods to choose from
        if len(all_food_names) <= FOOD_ITEMS_PER_GAME:
            self.foods = all_food_names
        else:
            self.foods = random.sample(all_food_names, FOOD_ITEMS_PER_GAME)
        
        # Create a dictionary of food images for this game
        self.food_images = {food: ALL_FOOD_IMAGES[food] for food in self.foods}
        
        print(f"Selected foods for this game: {self.foods}")
        
    def add_mouse(self):
        # Add a mouse to a random empty cell if there are fewer than 3 mice
        if len(self.mice) < 3:
            empty_cells = [(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE) 
                          if (x, y) not in self.mice and (x, y) not in self.bones and (x, y) != self.kitty_pos]
            if empty_cells:
                pos = random.choice(empty_cells)
                self.mice.append(pos)
                # Remove food under mouse
                row, col = pos
                self.board[row][col] = None
    
    def add_bones(self):
        # Add 2 bones to random empty cells
        for _ in range(2):
            empty_cells = [(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE) 
                          if (x, y) not in self.mice and (x, y) not in self.bones and (x, y) != self.kitty_pos]
            if empty_cells:
                pos = random.choice(empty_cells)
                self.bones.append(pos)
                # Remove food under bone
                row, col = pos
                self.board[row][col] = None

    def is_adjacent_to_kitty(self, row, col):
        # Check if the cell is adjacent to the kitty (including diagonals)
        kitty_row, kitty_col = self.kitty_pos
        return abs(row - kitty_row) <= 1 and abs(col - kitty_col) <= 1 and (row, col) != self.kitty_pos
    
    def calculate_chain_result(self):
        """Calculate the potential result of collecting the current chain"""
        if len(self.selected_cells) < 2:
            return 0
            
        # Count regular food cells (not mice or bones)
        regular_food_cells = sum(1 for cell in self.selected_cells 
                               if cell not in self.mice and cell not in self.bones)
        mice_caught = sum(1 for mouse in self.mice if mouse in self.selected_cells)
        bones_caught = sum(1 for bone in self.bones if bone in self.selected_cells)
        
        food_points = regular_food_cells
        mouse_points = mice_caught * 4
        bones_penalty = bones_caught * -10  # -10 points per bone
        
        return food_points + mouse_points + bones_penalty

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
            # Check if it's a mouse or bone (can always be selected)
            if (row, col) in self.mice or (row, col) in self.bones:
                return (row, col) not in self.selected_cells  # Just make sure we haven't selected it already
                
            # If not a mouse or bone, check if it's the same food type as the first selection
            if (row, col) not in self.selected_cells:  # Make sure it's not already selected
                # Get the first food in the chain (skip mice and bones)
                first_food = None
                for cell_row, cell_col in self.selected_cells:
                    if (cell_row, cell_col) not in self.mice and (cell_row, cell_col) not in self.bones and self.board[cell_row][cell_col] is not None:
                        first_food = self.board[cell_row][cell_col]
                        break
                
                # If we couldn't find a food in the chain yet, this is the first food
                if first_food is None:
                    return True
                    
                current_food = self.board[row][col]
                # Make sure it's the same food type (if it's not None)
                return current_food is None or current_food == first_food
            
        return False
        
    def is_mouse_on_path(self):
        # Check if the selected path goes through any mice
        for mouse in self.mice:
            if mouse in self.selected_cells:
                return True
        return False
        
    def collect_foods(self):
        # Collect selected foods, remove mice on path, and update score
        if len(self.selected_cells) > 1:  # Need at least 2 foods to collect
            # Calculate points to add
            # Count regular food cells (not mice or bones)
            regular_food_cells = sum(1 for cell in self.selected_cells 
                                   if cell not in self.mice and cell not in self.bones)
            mice_caught = sum(1 for mouse in self.mice if mouse in self.selected_cells)
            bones_caught = sum(1 for bone in self.bones if bone in self.selected_cells)
            
            food_points = regular_food_cells
            mouse_points = mice_caught * 4
            bones_penalty = bones_caught * -10  # -10 points per bone
            self.total_points_to_add = food_points + mouse_points + bones_penalty
            
            # Play meow sound at the start of the chain
            if MEOW_SOUND:
                MEOW_SOUND.play()
            
            # Set up score animation
            self.score_animation_active = True
            self.points_added_so_far = 0
            self.displayed_score = self.fruits_collected
            # Show negative points in red if there's a penalty
            if self.total_points_to_add < 0:
                self.points_popup_text = f"{self.total_points_to_add:+d}"  # Use :+d to always show the sign
            else:
                self.points_popup_text = f"+{self.total_points_to_add}"
            self.points_popup_alpha = 255
            self.points_popup_time = time.time()
            
            # Store old kitty position to fill with food later
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
                
                # Store cells that need to be replaced with new foods later
                self.cells_to_replace = self.selected_cells.copy()
            
            # Increment moves
            self.moves += 1
            
            # We'll add a mouse after the animation completes, not here
            # Store if we need to add a mouse
            self.should_add_mouse = (self.moves % 2 == 0)
            
            # Add bones every 2 steps
            self.should_add_bones = (self.moves % 2 == 0)
                
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
        if self.fruits_collected < FOOD_GOAL:
            # Game lost, no stars
            self.stars_earned = 0
        else:
            # Game won, calculate stars based on score
            for threshold, stars in STAR_THRESHOLDS:
                if self.fruits_collected >= threshold:
                    self.stars_earned = stars
        
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
                
                # Draw food image (if there is one and no mouse, bone, or kitty)
                food_type = self.board[row][col]
                if food_type is not None and (row, col) not in self.mice and (row, col) not in self.bones and (row, col) != self.kitty_pos:
                    food_image = self.food_images[food_type]
                    food_rect = food_image.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                    self.screen.blit(food_image, food_rect)
                
                # Draw mouse if present
                if (row, col) in self.mice:
                    mouse_rect = MOUSE_IMAGE.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                    self.screen.blit(MOUSE_IMAGE, mouse_rect)
                
                # Draw bone if present
                if (row, col) in self.bones:
                    bones_rect = BONES_IMAGE.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                    self.screen.blit(BONES_IMAGE, bones_rect)
        
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
        score_text = self.font.render(f"Score: {self.displayed_score}/{FOOD_GOAL}", True, BLACK)
        score_rect = score_text.get_rect(topleft=(20, SCREEN_HEIGHT - 80))
        self.screen.blit(score_text, score_rect)
        
        # Draw points popup if active
        if self.score_animation_active and self.points_popup_alpha > 0:
            popup_font = self.font
            # Use red color for negative points, green for positive
            popup_color = (255, 0, 0) if self.total_points_to_add < 0 else (50, 205, 50)
            popup_text = popup_font.render(self.points_popup_text, True, popup_color)
            popup_text.set_alpha(self.points_popup_alpha)
            # Position next to score
            popup_rect = popup_text.get_rect(left=score_rect.right + 10, centery=score_rect.centery)
            self.screen.blit(popup_text, popup_rect)
            
        # Draw chain result preview if there are selected cells
        elif len(self.selected_cells) >= 2 and not self.kitty_animation_active:
            # Calculate potential result
            chain_result = self.calculate_chain_result()
            
            # Show preview next to score
            preview_color = (255, 0, 0) if chain_result < 0 else (50, 205, 50)
            preview_text = self.font.render(f"({chain_result:+d})", True, preview_color)
            preview_rect = preview_text.get_rect(left=score_rect.right + 10, centery=score_rect.centery)
            self.screen.blit(preview_text, preview_rect)
        
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
    
    def update_animation(self):
        # Update animation values based on time elapsed since animation started
        elapsed = time.time() - self.animation_start_time
        
        # Dim animation duration: 0.7 seconds (30% faster than 1 second)
        dim_duration = 0.7
        # Panel slide animation duration: 1.05 seconds (30% faster than 1.5 seconds), starting after 0.35s (30% faster than 0.5s)
        panel_duration = 1.05
        panel_delay = 0.35
        
        # Update dim alpha
        if elapsed < dim_duration:
            # Gradually increase from 0 to 180
            self.dim_alpha = int(180 * (elapsed / dim_duration))
        else:
            self.dim_alpha = 180
        
        # Update panel position
        if elapsed > panel_delay:
            panel_elapsed = elapsed - panel_delay
            if panel_elapsed < panel_duration:
                # Calculate target y position (centered vertically)
                panel_height = 300
                target_y = (SCREEN_HEIGHT - panel_height) // 2
                
                # Ease-out function for smoother deceleration
                progress = panel_elapsed / panel_duration
                ease_factor = 1 - (1 - progress) * (1 - progress)  # Quadratic ease out
                
                # Interpolate from off-screen to target position
                self.panel_y_offset = -400 + (target_y + 400) * ease_factor
            else:
                # Animation complete
                panel_height = 300
                self.panel_y_offset = (SCREEN_HEIGHT - panel_height) // 2
                self.animation_in_progress = False
                self.show_results = True
                
                # Start counter animation
                if not self.counter_animation_active:
                    self.counter_animation_active = True
                    self.counter_start_time = time.time()
                    self.displayed_score = 0
                    self.stars_shown = 0
    
    def update_counter_animation(self):
        if not self.counter_animation_active:
            return
            
        # Duration for counter animation (2 seconds)
        counter_duration = 2.0
        elapsed = time.time() - self.counter_start_time
        
        if elapsed < counter_duration:
            # Calculate current score to display (with easing)
            progress = elapsed / counter_duration
            ease_factor = 1 - (1 - progress) * (1 - progress)  # Quadratic ease out
            
            # Handle both positive and negative final scores
            start_score = 0  # Always start from 0 in the results screen
            target_score = self.fruits_collected
            
            # Animate from start_score to target_score
            self.displayed_score = int(start_score + (target_score - start_score) * ease_factor)
            
            # Calculate stars to show based on thresholds
            self.stars_shown = 0
            for threshold, stars in STAR_THRESHOLDS:
                if self.displayed_score >= threshold:
                    self.stars_shown = stars
        else:
            # Animation complete
            self.displayed_score = self.fruits_collected
            self.stars_shown = self.stars_earned
            self.counter_animation_active = False
    
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
        if self.fruits_collected >= FOOD_GOAL:
            result_text = self.large_font.render("VICTORY!", True, GREEN)
        else:
            result_text = self.large_font.render("GAME OVER", True, RED)
        
        result_rect = result_text.get_rect(center=(panel_x + panel_width // 2, panel_y + 40))
        self.screen.blit(result_text, result_rect)
        
        # Update counter animation if active
        if self.counter_animation_active:
            self.update_counter_animation()
        
        # Draw score with counter animation
        score_text = self.font.render(f"Food collected: {self.displayed_score}", True, BLACK)
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
                            if score >= FOOD_GOAL and time_val < self.best_time:
                                self.best_time = time_val
                        except (ValueError, IndexError):
                            continue
        except FileNotFoundError:
            pass  # No history file yet
    
    def save_game_history(self):
        # Load existing history
        history = load_game_history()
        
        # Create new game record
        game_record = {
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "score": self.fruits_collected,
            "moves": self.moves,
            "time": self.elapsed_time,
            "stars": self.stars_earned
        }
        
        # Add to history
        history.append(game_record)
        
        # Save updated history
        save_game_history(history)
        
        # Update best score and time
        if self.fruits_collected > self.best_score:
            self.best_score = self.fruits_collected
            
        if self.game_won and self.elapsed_time < self.best_time:
            self.best_time = self.elapsed_time
    
    def update_kitty_animation(self):
        if not self.kitty_animation_active:
            return
            
        # Animation duration for each segment (0.2 seconds per cell)
        animation_duration = 0.2
        elapsed = time.time() - self.kitty_animation_start_time
        
        if elapsed < animation_duration:
            # Calculate progress with easing
            progress = elapsed / animation_duration
            # Use ease-out function for smoother movement
            ease_factor = 1 - (1 - progress) * (1 - progress)  # Quadratic ease out
            
            # Interpolate between start and target positions
            start_row, start_col = self.kitty_start_pos
            target_row, target_col = self.kitty_target_pos
            
            # Update current position (floating point for smooth animation)
            self.kitty_current_pos[0] = start_row + (target_row - start_row) * ease_factor
            self.kitty_current_pos[1] = start_col + (target_col - start_col) * ease_factor
        else:
            # Current segment complete
            
            # Remove food from the cell the kitty just landed on
            cell_pos = self.animation_path[self.current_path_index + 1]  # The cell we just moved to
            row, col = cell_pos
            
            # Only remove food if this is a selected cell (not the kitty's starting position)
            if cell_pos in self.cells_to_replace:
                self.board[row][col] = None
                
                # Check if there's a mouse or bone at this position and remove it
                if cell_pos in self.mice:
                    # Remove the mouse only when the kitty actually reaches it
                    self.mice.remove(cell_pos)
                    points_for_this_cell = 4  # Mouse
                    # Play mouse sound
                    if MOUSE_SOUND:
                        MOUSE_SOUND.play()
                elif cell_pos in self.bones:
                    # Remove the bone when the kitty reaches it
                    self.bones.remove(cell_pos)
                    points_for_this_cell = -10  # Bone penalty
                    # Play bone sound
                    if BONE_SOUND:
                        BONE_SOUND.play()
                else:
                    points_for_this_cell = 1  # Regular food
                    
                # For smoother animation with negative points, use the precalculated total
                # This prevents the score from going up and then suddenly dropping
                if self.total_points_to_add < 0:
                    # Calculate progress through the path (0.0 to 1.0)
                    total_cells = len(self.cells_to_replace)
                    current_cell = self.current_path_index  # How many cells we've processed
                    progress_ratio = current_cell / total_cells
                    
                    # Animate smoothly from the starting score to the final score
                    # This distributes the negative points throughout the animation
                    target_score = self.fruits_collected + self.total_points_to_add
                    start_score = self.fruits_collected
                    self.displayed_score = int(start_score + (target_score - start_score) * progress_ratio)
                else:
                    # For positive scores, just add points as we go
                    self.points_added_so_far += points_for_this_cell
                    self.displayed_score = self.fruits_collected + self.points_added_so_far
            
            self.current_path_index += 1
            
            # Check if we've reached the end of the path
            if self.current_path_index >= len(self.animation_path) - 1:
                # Animation complete - set final position
                self.kitty_pos = self.animation_path[-1]
                self.kitty_animation_active = False
                
                # Start food replacement animation with delay
                self.fruit_replacement_active = True
                self.fruit_replacement_start_time = time.time()
                
                # Update actual score now
                self.fruits_collected += self.total_points_to_add
                self.score += self.total_points_to_add
                
                # Make sure the displayed score matches the actual score
                self.displayed_score = self.fruits_collected
            else:
                # Move to next segment
                self.kitty_start_pos = self.animation_path[self.current_path_index]
                self.kitty_target_pos = self.animation_path[self.current_path_index + 1]
                self.kitty_current_pos = list(self.kitty_start_pos)  # Reset current position
                self.kitty_animation_start_time = time.time()  # Reset timer for next segment
    
    def update_fruit_replacement(self):
        if not self.fruit_replacement_active:
            return
            
        # Wait for 0.5 second after kitty reaches final position before replacing foods
        delay = 0.5
        elapsed = time.time() - self.fruit_replacement_start_time
        
        if elapsed >= delay:
            # Play purr sound when the step is finished
            if PURR_SOUND:
                PURR_SOUND.play()
                
            # Add a mouse if needed (every 2 moves)
            if self.should_add_mouse and not self.game_over:
                self.add_mouse()
                self.should_add_mouse = False
            
            # Add bones if needed (every 2 moves)
            if self.should_add_bones and not self.game_over:
                self.add_bones()
                self.should_add_bones = False
            
            # Replace collected foods with new ones (except kitty's final position)
            for row, col in self.cells_to_replace:
                if (row, col) != self.kitty_pos:  # Don't place food where kitty is
                    self.board[row][col] = random.choice(self.foods)
            
            # Fill the old kitty position with a food (if it's not part of the cells to replace)
            if self.old_kitty_pos and self.old_kitty_pos not in self.cells_to_replace:
                old_row, old_col = self.old_kitty_pos
                self.board[old_row][old_col] = random.choice(self.foods)
            
            # Score is already updated in update_kitty_animation, no need to update it again here
            
            # Check if this was the final move
            if self.final_move:
                # Set game over state
                self.game_over = True
                self.game_won = self.fruits_collected >= FOOD_GOAL
                
                # Calculate stars earned
                self.calculate_stars()
                
                # Start the result animation
                self.animation_start_time = time.time()
                self.animation_in_progress = True
                self.dim_alpha = 0
                self.panel_y_offset = -400
                
                # Save game history with the final score
                self.save_game_history()
            
            # Animation complete
            self.fruit_replacement_active = False
            self.cells_to_replace = []
            self.old_kitty_pos = None
            
            # End score animation after 2 more seconds
            self.points_popup_time = time.time()
    
    def update_score_animation(self):
        if not self.score_animation_active:
            return
            
        # Keep the popup visible for 1.5 seconds after food replacement (50% faster than before)
        if not self.kitty_animation_active and not self.fruit_replacement_active:
            elapsed = time.time() - self.points_popup_time
            if elapsed > 1.0:  # Start fading after 1 second (was 2)
                # Start fading out
                fade_duration = 0.5  # Fade over 0.5 seconds (was 1.0)
                if elapsed < 1.5:  # Complete fade by 1.5 seconds (was 3.0)
                    fade_progress = (elapsed - 1.0) / fade_duration
                    self.points_popup_alpha = int(255 * (1 - fade_progress))
                else:
                    # Animation complete
                    self.score_animation_active = False
                    self.points_popup_alpha = 0
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return  # Return to main menu instead of quitting
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_over:  # Restart game
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:  # Return to main menu
                        running = False
                        return
                    elif event.key == SETTINGS["collect_key"] and not self.game_over:  # Use custom collect key
                        self.collect_foods()
                        
                elif event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    pos = pygame.mouse.get_pos()
                    
                    # Check if collect button was clicked
                    if self.collect_button_rect.collidepoint(pos):
                        self.collect_foods()
                        continue
                        
                    # Convert position to grid coordinates
                    col = (pos[0] - MARGIN) // (CELL_SIZE + MARGIN)
                    row = (pos[1] - MARGIN) // (CELL_SIZE + MARGIN)
                    
                    # Check if click is within the grid
                    if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                        # Check if cell is already selected
                        if (row, col) in self.selected_cells:
                            # Find the index of the clicked cell in the selection
                            index = self.selected_cells.index((row, col))
                            # Remove this cell and all cells after it
                            self.selected_cells = self.selected_cells[:index]
                            # Play tap sound
                            if TAP_SOUND:
                                TAP_SOUND.play()
                        # Otherwise check if it's a valid selection
                        elif self.is_valid_selection(row, col):
                            self.selected_cells.append((row, col))
                            # Play tap sound
                            if TAP_SOUND:
                                TAP_SOUND.play()
            
            # Draw the board
            self.draw_board()
            
            # Update display
            pygame.display.flip()
            
            # Cap the frame rate
            self.clock.tick(60)
        
        # Don't stop music when returning to menu
        # pygame.mixer.music.stop()
        # pygame.quit()
        # sys.exit()

if __name__ == "__main__":
    # Initialize pygame window
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Kitty Food Game")
    
    # Start with main menu
    menu = MainMenu(screen)
    menu.run()
    
    # Clean up
    pygame.quit()
    sys.exit() 