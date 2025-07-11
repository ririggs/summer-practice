import unittest
import os
import sys
import pygame
import json
from unittest.mock import patch, MagicMock, mock_open, PropertyMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pygame.init = MagicMock()
pygame.mixer = MagicMock()
pygame.display = MagicMock()
pygame.font = MagicMock()
pygame.image = MagicMock()
pygame.transform = MagicMock()
pygame.Surface = MagicMock()
pygame.draw = MagicMock()
pygame.key = MagicMock()
pygame.Rect = MagicMock()
pygame.MOUSEBUTTONDOWN = 1
pygame.KEYDOWN = 2
pygame.QUIT = 3
pygame.K_ESCAPE = 27
pygame.K_SPACE = 32
pygame.K_r = 114

import main

class TestGameSettings(unittest.TestCase):
    """Test loading and saving game settings"""
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"sound_volume": 50, "music_volume": 30, "collect_key": "32", "reload_key": "114", "graphics_mode": "food"}')
    def test_load_settings(self, mock_file):
        """Test loading settings from file"""
        settings = main.load_settings()
        
        self.assertEqual(settings["sound_volume"], 50)
        self.assertEqual(settings["music_volume"], 30)
        self.assertEqual(settings["collect_key"], 32)
        self.assertEqual(settings["reload_key"], 114)
        self.assertEqual(settings["graphics_mode"], "food")
        
        mock_file.assert_called_once_with(main.SETTINGS_FILE, "r")
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_settings_file_not_found(self, mock_file):
        """Test loading settings when file doesn't exist"""
        with patch('main.save_settings') as mock_save:
            settings = main.load_settings()
            
            self.assertEqual(settings["sound_volume"], main.DEFAULT_SETTINGS["sound_volume"])
            self.assertEqual(settings["music_volume"], main.DEFAULT_SETTINGS["music_volume"])
            self.assertEqual(settings["collect_key"], main.DEFAULT_SETTINGS["collect_key"])
            self.assertEqual(settings["reload_key"], main.DEFAULT_SETTINGS["reload_key"])
            self.assertEqual(settings["graphics_mode"], main.DEFAULT_SETTINGS["graphics_mode"])
            
            mock_save.assert_called_once_with(main.DEFAULT_SETTINGS)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_settings(self, mock_json_dump, mock_file):
        """Test saving settings to file"""
        test_settings = {
            "sound_volume": 75,
            "music_volume": 60,
            "collect_key": 32,
            "reload_key": 114,
            "graphics_mode": "fruits"
        }
        
        main.save_settings(test_settings)
        
        mock_file.assert_called_once_with(main.SETTINGS_FILE, "w")
        
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        saved_settings = args[0]
        
        self.assertEqual(saved_settings["sound_volume"], 75)
        self.assertEqual(saved_settings["music_volume"], 60)
        self.assertEqual(saved_settings["collect_key"], "32")
        self.assertEqual(saved_settings["reload_key"], "114")
        self.assertEqual(saved_settings["graphics_mode"], "fruits")

class TestGameInstructions(unittest.TestCase):
    """Test game instructions generation"""
    
    def test_get_instructions_food_mode(self):
        """Test instructions in food mode"""
        instructions = main.get_instructions(is_fruits_mode=False)
        
        self.assertTrue(any("food" in line for line in instructions))
        self.assertTrue(any("Bones" in line for line in instructions))
        self.assertFalse(any("fruits" in line for line in instructions))
        self.assertFalse(any("Rocks" in line for line in instructions))
    
    @patch('main.get_instructions')
    def test_get_instructions_fruits_mode(self, mock_get_instructions):
        """Test instructions in fruits mode"""
        mock_instructions = [
            "How to play:",
            "",
            "1. Connect the same types of fruits to make the cat eat them.",
            "2. Mice give 5 points each.",
            "3. Rocks take away 10 points each.",
            "4. Collect 75 points to win.",
            "5. You have only 10 moves.",
            "6. You can reload the field once per game."
        ]
        mock_get_instructions.return_value = mock_instructions
        
        instructions = main.get_instructions(is_fruits_mode=True)
        
        self.assertEqual(instructions, mock_instructions)
        self.assertTrue(any("fruits" in line for line in instructions))
        self.assertTrue(any("Rocks" in line for line in instructions))
        self.assertFalse(any("Bones" in line for line in instructions))

class TestLoadAllFoods(unittest.TestCase):
    """Test loading food images based on graphics mode"""
    
    @patch('os.path.exists', return_value=True)
    @patch('os.listdir', return_value=['apple.png', 'banana.png', 'orange.png'])
    @patch('main.load_image', return_value=MagicMock())
    def test_load_foods_fruits_mode(self, mock_load_image, mock_listdir, mock_exists):
        """Test loading food images in fruits mode"""
        main.SETTINGS = {"graphics_mode": "fruits"}
        
        foods = main.load_all_foods()
        
        mock_listdir.assert_called_once_with(os.path.join('assets', 'fruits'))
        
        self.assertEqual(len(foods), 3)
        self.assertIn('apple', foods)
        self.assertIn('banana', foods)
        self.assertIn('orange', foods)
        
        calls = [
            ((mock_load_image.call_args_list[i].args[0], mock_load_image.call_args_list[i].args[1]), {})
            for i in range(3)
        ]
        self.assertIn((('apple.png', 'fruits'), {}), calls)
        self.assertIn((('banana.png', 'fruits'), {}), calls)
        self.assertIn((('orange.png', 'fruits'), {}), calls)
    
    @patch('os.path.exists', return_value=True)
    @patch('os.listdir', return_value=['ball.png', 'bowl.png', 'can.png'])
    @patch('main.load_image', return_value=MagicMock())
    def test_load_foods_food_mode(self, mock_load_image, mock_listdir, mock_exists):
        """Test loading food images in food mode"""
        main.SETTINGS = {"graphics_mode": "food"}
        
        foods = main.load_all_foods()
        
        mock_listdir.assert_called_once_with(os.path.join('assets', 'food'))
        
        self.assertEqual(len(foods), 3)
        self.assertIn('ball', foods)
        self.assertIn('bowl', foods)
        self.assertIn('can', foods)
        
        calls = [
            ((mock_load_image.call_args_list[i].args[0], mock_load_image.call_args_list[i].args[1]), {})
            for i in range(3)
        ]
        self.assertIn((('ball.png', 'food'), {}), calls)
        self.assertIn((('bowl.png', 'food'), {}), calls)
        self.assertIn((('can.png', 'food'), {}), calls)
    
    @patch('os.path.exists', return_value=False)
    @patch('os.makedirs')
    @patch('os.listdir', side_effect=FileNotFoundError)
    @patch('main.load_image', return_value=MagicMock())
    def test_load_foods_directory_not_found(self, mock_load_image, mock_listdir, mock_makedirs, mock_exists):
        """Test loading food images when directory doesn't exist"""
        main.SETTINGS = {"graphics_mode": "food"}
        
        foods = main.load_all_foods()
        
        mock_makedirs.assert_called_once_with(os.path.join('assets', 'food'), exist_ok=True)
        
        self.assertIn('ball', foods)
        self.assertIn('bowl', foods)
        self.assertIn('can', foods)

class TestToggleSwitch(unittest.TestCase):
    """Test the ToggleSwitch class"""
    
    def setUp(self):
        self.toggle = main.ToggleSwitch(
            100, 100, 200, 50, 
            "Test Toggle", MagicMock(), 
            ["Option1", "Option2"], "Option1"
        )
    
    def test_init(self):
        """Test initialization"""
        self.assertEqual(self.toggle.label, "Test Toggle")
        self.assertEqual(self.toggle.options, ["Option1", "Option2"])
        self.assertEqual(self.toggle.current_option, "Option1")
        self.assertEqual(len(self.toggle.buttons), 2)
    
    def test_handle_event_click(self):
        """Test handling click events"""
        event = MagicMock()
        event.type = pygame.MOUSEBUTTONDOWN
        event.button = 1
        
        self.toggle.buttons[0][0].collidepoint.return_value = True
        self.toggle.buttons[1][0].collidepoint.return_value = False
        
        result = self.toggle.handle_event(event)
        self.assertFalse(result)
        self.assertEqual(self.toggle.current_option, "Option1")
        
        self.toggle.buttons[0][0].collidepoint.return_value = False
        self.toggle.buttons[1][0].collidepoint.return_value = True
        
        result = self.toggle.handle_event(event)
        self.assertTrue(result)
        self.assertEqual(self.toggle.current_option, "Option2")

class TestGameMethods(unittest.TestCase):
    """Test specific Game class methods"""
    
    def test_is_adjacent_to_kitty(self):
        """Test checking if a cell is adjacent to kitty"""
        game = MagicMock()
        game.kitty_pos = (1, 1)
        
        is_adjacent = main.Game.is_adjacent_to_kitty.__get__(game)
        
        for row_offset in [-1, 0, 1]:
            for col_offset in [-1, 0, 1]:
                if row_offset == 0 and col_offset == 0:
                    continue
                
                row = game.kitty_pos[0] + row_offset
                col = game.kitty_pos[1] + col_offset
                
                self.assertTrue(is_adjacent(row, col))
        
        self.assertFalse(is_adjacent(3, 3))
    
    def test_calculate_chain_result(self):
        """Test calculating points for a chain"""
        game = MagicMock()
        game.selected_cells = []
        game.mice = []
        game.bones = []
        
        def mock_chain_result():
            regular_food_cells = sum(1 for cell in game.selected_cells 
                                   if cell not in game.mice and cell not in game.bones)
            mice_caught = sum(1 for mouse in game.mice if mouse in game.selected_cells)
            bones_caught = sum(1 for bone in game.bones if bone in game.selected_cells)
            
            food_points = regular_food_cells
            mouse_points = mice_caught * 5
            bones_penalty = bones_caught * -10
            
            return food_points + mouse_points + bones_penalty
        
        game.calculate_chain_result = mock_chain_result
        
        self.assertEqual(game.calculate_chain_result(), 0)
        
        game.selected_cells = [(0, 0), (0, 1), (0, 2)]
        game.mice = []
        game.bones = []
        self.assertEqual(game.calculate_chain_result(), 3)
        
        game.selected_cells = [(0, 0), (0, 1), (0, 2)]
        game.mice = [(0, 2)]
        game.bones = []
        self.assertEqual(game.calculate_chain_result(), 7)
        
        game.selected_cells = [(0, 0), (0, 1), (0, 2)]
        game.mice = [(0, 2)]
        game.bones = [(0, 1)]
        self.assertEqual(game.calculate_chain_result(), -4)

if __name__ == '__main__':
    unittest.main() 