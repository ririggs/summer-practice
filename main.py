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


# Calculate angle between two points
def calculate_angle(start_pos, end_pos):
    dx = end_pos[1] - start_pos[1]  # Column difference (x)
    dy = end_pos[0] - start_pos[0]  # Row difference (y)
    angle = math.degrees(math.atan2(dy, dx))
    return angle


# Add constants needed for this file
FRUITS_PER_GAME = 3

# Load all available fruits
ALL_FRUIT_IMAGES = load_all_fruits()

# Mouse and kitty images
MOUSE_IMAGE = load_image('mouse.png')
KITTY_IMAGE = load_image('kitty.png')
ARROW_IMAGE = load_image('arrow_right.png')

# Star images
EMPTY_STAR = create_star_image(filled=False)
FILLED_STAR = create_star_image(filled=True)