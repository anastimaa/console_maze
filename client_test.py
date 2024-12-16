import pytest
from unittest.mock import patch
from server import generate_maze, game_state
from dfsmaze import dfsmaze_generate, dfs
from сlient import game_menu, print_game_state, receive_data

# тест функции dfsmaze_generate

def test_dfsmaze_generate_correct():
    maze = dfsmaze_generate(7, 7)

    for row in maze:
        for cell in row:
            assert cell in ["\u2588", " "]

def test_dfsmaze_generate_invalid_size():
    with pytest.raises(ValueError):
        dfsmaze_generate(1, 1)

    with pytest.raises(ValueError):
        dfsmaze_generate(-1, -1)

def test_test_dfsmaze_generate_invalid_wigth():
    with pytest.raises(ValueError):
        dfsmaze_generate(5, 2)

def test_test_dfsmaze_generate_invalid_height():
    with pytest.raises(ValueError):
        dfsmaze_generate(1, 7)

# тест dfs

def test_dfs_invalid_starting_point():
    maze = [["\u2588" for _ in range(5)] for _ in range(5)]
    with pytest.raises(IndexError):
        dfs(maze, 5, 5, -1, -1)

def test_dfs_start_position_not_empty():
    maze = [["\u2588" for _ in range(7)] for _ in range(7)]
    maze[1][1] = "\u2588"
    with pytest.raises(ValueError):
        dfs(maze, 7, 7, 1, 1)

# тест generate_maze

def test_generate_maze_level_1():
    maze = generate_maze(1)
    assert len(maze) == 10
    assert len(maze[0]) == 15
    assert maze[1][1] == "S"
    assert maze[8][13] == "E"

def test_generate_maze_level_2():
    maze = generate_maze(2)
    assert len(maze) == 15
    assert len(maze[0]) == 20
    assert maze[1][1] == "S"
    assert maze[13][18] == "E"

def test_generate_maze_level_3():
    maze = generate_maze(3)
    assert len(maze) == 20
    assert len(maze[0]) == 30
    assert maze[1][1] == "S"
    assert maze[18][28] == "E"

def test_doors_around_exit():
    level = 2
    maze = generate_maze(level)
    exit_x, exit_y = len(maze[0]) - 2, len(maze) - 2
    assert maze[exit_y][exit_x] == "E"
    door_positions = [
        (exit_x - 1, exit_y),
        (exit_x, exit_y - 1)
    ]
    doors_found = 0
    for dx, dy in door_positions:
        if 1 <= dx < len(maze[0]) - 1 and 1 <= dy < len(maze) - 1 and maze[dy][dx] == "\u2591":
            doors_found += 1
    assert doors_found == 2
    assert maze[exit_y][exit_x + 1] != "\u2591"
    assert maze[exit_y + 1][exit_x] != "\u2591"

def test_items_generation():
    maze = generate_maze(1)
    keys = sum(row.count("K") for row in maze)
    gems = sum(row.count("\u25C7") for row in maze)
    assert keys >= 3
    assert gems >= 3


def test_generate_maze_invalid_level_0():
    with pytest.raises(ValueError):
        generate_maze(0)


def test_generate_maze_invalid_level_4():
    with pytest.raises(ValueError):
        generate_maze(4)


def test_generate_maze_invalid_level_negative():
    with pytest.raises(ValueError):
        generate_maze(-5)

# Тесты для клиента
# для game_menu
def test_new_game_invalid_choise():
    with pytest.raises(ValueError): # проверяем, что будет выбрашено исключение ValErr
        with patch('builtins.input', return_value = "a"):
            game_menu()

def test_new_game_invalid_level():
    with pytest.raises(ValueError):
        with patch('builtins.input', side_effect = ["N", "5"]):
            game_menu()


def test_new_game_valid_level():
    with patch('builtins.input', side_effect = ["N", "2"]):
        level = game_menu()
        assert level == 2
