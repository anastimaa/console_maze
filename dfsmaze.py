import random

WALL = '\u2588'
EMPTY = ' '


def dfsmaze_generate(width, height):
    """
    Генерирует дополнительные промежутки в лабиринте.

    :param width: Ширина лабиринта.
    :type width: int
    :param height: Высота лабиринта.
    :type height: int
    :raises ValueError: Если ширина или высота лабиринта меньше 3.
    :returns: Двумерный список, представляющий сгенерированный лабиринт.
    """
    if width < 3 or height < 3:
        raise ValueError("Maze size must be at least 3x3")

    maze = [[WALL for x in range(width)] for y in range(height)]
    start_x = 1
    start_y = 1
    maze[start_x][start_y] = EMPTY
    dfs(maze, height, width, start_x, start_y)

    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if random.randint(1, 100) >= 90:
                maze[y][x] = EMPTY

    return maze


def dfs(maze, height, width, start_x, start_y):
    """
    Заимствовано.
    Создает лабиринт, начиная с заданной точки.

    :param maze: Список списков, представляющий лабиринт. Каждая ячейка может быть пустой (" "), стеной или другой преградой. 
    :type maze: list[list]
    :param height: Высота лабиринта.
    :type height: int
    :param width: Ширина лабиринта.
    :type width: int
    :param start_x: Начальная строка для начала поиска.
    :type start_x: int
    :param start_y: Начальный столбец для начала поиска.
    :type start_y: int
    :returns: None. Функция изменяет лабиринт in-place, удаляя стены и открывая проходы.
    :raises IndexError: Если начальная точка выходит за пределы лабиринта.
    :raises ValueError: Если начальная точка не является пустой клеткой (" ").
    """
    if not (0 <= start_x < height and 0 <= start_y < width):
        raise IndexError(f"Invalid starting point: ({start_x}, {start_y}) is out of bounds")

    if maze[start_x][start_y] != EMPTY:
        raise ValueError("Start position must be an empty cell")

    directions = [1, 2, 3, 4]
    random.shuffle(directions)

    for direction in directions:
        if direction == 1:
            if start_x - 2 > 0 and maze[start_x - 2][start_y] != EMPTY:
                maze[start_x - 1][start_y] = EMPTY
                maze[start_x - 2][start_y] = EMPTY
                dfs(maze, height, width, start_x - 2, start_y)
        elif direction == 2:
            if start_x + 2 < height - 1 and maze[start_x + 2][start_y] != EMPTY:
                maze[start_x + 1][start_y] = EMPTY
                maze[start_x + 2][start_y] = EMPTY
                dfs(maze, height, width, start_x + 2, start_y)
        elif direction == 3:
            if start_y - 2 > 0 and maze[start_x][start_y - 2] != EMPTY:
                maze[start_x][start_y - 1] = EMPTY
                maze[start_x][start_y - 2] = EMPTY
                dfs(maze, height, width, start_x, start_y - 2)
        elif direction == 4:
            if start_y + 2 < width - 1 and maze[start_x][start_y + 2] != EMPTY:
                maze[start_x][start_y + 1] = EMPTY
                maze[start_x][start_y + 2] = EMPTY
                dfs(maze, height, width, start_x, start_y + 2)
