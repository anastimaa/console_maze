import socket
import pickle
import threading
import random
from dfsmaze import dfsmaze_generate

HOST = '0.0.0.0'
PORT = 65434
lock = threading.Lock()

game_state = {
    "maze": None,
    "players": {
        1: {"x": 1, "y": 1, "lives": 3, "keys": 0, "gems": 0},
        2: {"x": 1, "y": 1, "lives": 3, "keys": 0, "gems": 0}
    },
    "items": [],
    "mobs": None,
    "level": 0,
    "codegame": 0,
    "message": ""
}

connections = {}


def generate_maze(level):
    """
    Создает лабиринт для указанного уровня сложности.
    В лабиринт входят: расстановка мобов, ключей, алмазов,
    стартовая позиция игроков, выход и двери.

    :param level: Уровень сложности (1, 2 или 3)
    :type level: int
    :return: Лабиринт в виде двумерного списка
    :rtype: list[list[str]]
    :raises ValueError: Если передан неверный уровень сложности (не 1, 2 или 3)
    """
    if level not in [1, 2, 3]:
        raise ValueError(f"Invalid level {level}. Valid levels are 1, 2 or 3.")

    if level == 1:
        width, height = 15, 10
        mobs = 2
    elif level == 2:
        width, height = 20, 15
        mobs = 4
    else:
        width, height = 30, 20
        mobs = 6

    maze = dfsmaze_generate(width, height)

    maze[1][1] = "S"
    maze[2][1] = " "
    maze[1][2] = " "
    maze[2][2] = " "

    maze[height - 2][width - 2] = "E"
    maze[height - 3][width - 3] = " "
    maze[height - 2][width - 3] = " "
    maze[height - 3][width - 2] = " "

    with lock:
        m = []
        for _ in range(mobs):
            m.append({
                "x": random.randint(2, width - 3),
                "y": random.randint(2, height - 3),
                "d": random.randint(-1, 1) or 1
            })
        game_state["mobs"] = m

        for mb in game_state["mobs"]:
            maze[mb["y"]][mb["x"]] = "M"

        num_keys = random.randint(3, 5)
        for _ in range(num_keys):
            key_x = random.randint(1, width - 2)
            key_y = random.randint(1, height - 2)
            while maze[key_y][key_x] != " ":
                key_x = random.randint(1, width - 2)
                key_y = random.randint(1, height - 2)
            maze[key_y][key_x] = "K"

        door_positions = [(width - 3, height - 2), (width - 2, height - 3)]
        for dx, dy in door_positions:
            maze[dy][dx] = "\u2591"

        num_gems = random.randint(3, 5)
        for _ in range(num_gems):
            gem_x = random.randint(1, width - 2)
            gem_y = random.randint(1, height - 2)
            while maze[gem_y][gem_x] != " ":
                gem_x = random.randint(1, width - 2)
                gem_y = random.randint(1, height - 2)
            maze[gem_y][gem_x] = "\u25C7"

        game_state["players"][1]["x"] = 1
        game_state["players"][1]["y"] = 1
        game_state["players"][2]["x"] = 2
        game_state["players"][2]["y"] = 1

        game_state["codegame"] = random.randint(1, 20)
        game_state["level"] = level
        print(f'Code the game: {game_state["codegame"]}, level: {game_state["level"]}')

    return maze


def checkstep(x, y, player_id):
    """
    Проверяет возможность хода игрока.

    :param x: Координата x
    :type x: int
    :param y: Координата y
    :type y: int
    :param player_id: Номер игрока
    :type player_id: int
    :return: True, если игрок может пройти на указанную клетку; иначе False
    :rtype: bool
    :raises IndexError: Если координаты x или y находятся вне границ лабиринта.
    :raises KeyError: Если указанного игрока (player_id) нет в текущем состоянии игры.
    """
    if x < 0 or y < 0 or x >= len(game_state["maze"][0]) or y >= len(game_state["maze"]):
        raise IndexError("Coordinates out of bounds of the maze.")

    if player_id not in game_state["players"]:
        raise KeyError(f"Player ID {player_id} not found in the game.")

    if 1 <= x < len(game_state["maze"][0]) - 1 and 1 <= y < len(game_state["maze"]) - 1:
        if game_state["maze"][y][x] == "\u2591" and game_state["players"][player_id]["keys"] > 0:
            game_state["players"][player_id]["keys"] -= 1
            game_state["message"] = f"!Player {player_id} open the door!"
            return True
        elif game_state["maze"][y][x] in [" ", "E", "M", "K", "\u25C7"]:
            return True
    return False


def process_player_move(player_id, move):
    """
    Обрабатывает ход игрока.

    :param player_id: Номер игрока
    :type player_id: int
    :param move: Направление хода ("up", "down", "left", "right")
    :type move: str
    :return: None
    """
    global game_state
    with lock:
        player = game_state["players"][player_id]
        current_x, current_y = player["x"], player["y"]

        if move == "up":
            new_y, new_x = current_y - 1, current_x
        elif move == "down":
            new_y, new_x = current_y + 1, current_x
        elif move == "left":
            new_y, new_x = current_y, current_x - 1
        elif move == "right":
            new_y, new_x = current_y, current_x + 1
        else:
            return False

        game_state["message"] = ""

        if game_state["maze"][new_y][new_x] == "M":
            player["lives"] -= 1
            print(f"Player {player_id} hit a mob! Lives left: {player['lives']}")
            game_state["message"] = f"!Player {player_id} hit a mob! Lives left: {player['lives']}"
            game_state["maze"][current_y][current_x] = " "
            player["x"], player["y"] = 1, 1
            new_y, new_x = 1, 1
            game_state["maze"][1][1] = str(player_id)
            if player["lives"] == 0:
                print(f"Player {player_id} lost! The other player is winner!")
                game_state["message"] = f"@Player {player_id} lost! The other player is winner!"

        if game_state["maze"][new_y][new_x] == "K":
            player["keys"] += 1
            print(f"Player {player_id} picked up a key! Total keys: {player['keys']}")
            game_state["message"] = f"!Player {player_id} picked up a key! Total keys: {player['keys']}"
            game_state["maze"][new_y][new_x] = " "

        if game_state["maze"][new_y][new_x] == "\u25C7":
            player["gems"] += 1
            print(f"Player {player_id} picked up a gem!!!! Total gems: {player['gems']}")
            game_state["message"] = f"!Player {player_id} picked up a gem!!!! Total gems: {player['gems']}"
            game_state["maze"][new_y][new_x] = " "

        if checkstep(new_x, new_y, player_id):
            game_state["maze"][current_y][current_x] = " "
            player["x"], player["y"] = new_x, new_y

            if game_state["maze"][new_y][new_x] != "E":
                game_state["maze"][new_y][new_x] = str(player_id)
            else:
                print(f"Player {player_id} has exited the maze! Game over!")
                game_state["message"] = f"@Player {player_id} has escaped the maze! Game over!"

        for m in range(len(game_state["mobs"])):
            mob = game_state["mobs"][m]
            mob_y, mob_x = mob["y"], mob["x"]

            if 0 <= mob_y < len(game_state["maze"]) and 0 <= mob_x < len(game_state["maze"][0]):
                game_state["maze"][mob_y][mob_x] = " "

            new_mob_x = mob_x + mob["d"]

            if 0 <= mob_y < len(game_state["maze"]) and 0 <= new_mob_x < len(game_state["maze"][0]) and \
                    game_state["maze"][mob_y][new_mob_x] not in ["\u2588", "\u2591", "\u25C7", "K"]:
                mob["x"] = new_mob_x
            else:
                mob["d"] *= -1

            if 0 <= mob_y < len(game_state["maze"]) and 0 <= mob["x"] < len(game_state["maze"][0]):
                game_state["maze"][mob_y][mob["x"]] = "M"


def handle_client(conn, addr, player_id):
    """
    Обрабатывает подключение клиента, получает от него данные, обновляет состояние игры и отправляет обновленные данные всем игрокам.
    Эта функция запускается в отдельном потоке для каждого подключившегося клиента. Она выполняет следующие шаги:
    1. Отправляет начальное состояние игры клиенту.
    2. Получает данные от клиента (например, ход игрока или другие команды).
    3. Обрабатывает полученный ход игрока с помощью функции 'process_player_move'.
    4. Генерирует лабиринт для первого подключившегося игрока, если это необходимо.
    5. Проверяет правильность кода игры, и если код неправильный, завершает игру и выводит сообщение.
    6. Рассылает обновленное состояние игры всем клиентам с помощью функции 'broadcast_game_state'.
    7. При завершении игры или отключении клиента очищает соединение и удаляет игрока из списка подключений.

    :param conn: Сетевое соединение с клиентом, через которое происходит обмен данными.
    :type conn: socket.socket
    :param addr: Адрес клиента, с которым установлено соединение.
    :type addr: tuple
    :param player_id: Уникальный идентификатор игрока, назначаемый при подключении.
    :type player_id: int
    :return: None
    :raises Exception: Если возникает ошибка при получении или обработке данных от клиента.
    """
    global game_state
    print(f"Player {player_id} connected from {addr}")
    try:
        conn.sendall(pickle.dumps(game_state))
        while True:
            raw_data = conn.recv(4096)
            if not raw_data:
                print(f"Player {player_id} disconnected.")
                break

            move = pickle.loads(raw_data)

            if game_state["maze"] is None and game_state["codegame"] == 0:
                game_state["maze"] = generate_maze(move["level"])
            elif not isinstance(move, str) and int(game_state["codegame"]) != int(move["codegame"]):
                print(f"Received wrong code the game {player_id}")
                game_state["message"] = f'@Player {player_id} inserted wrong code:{move["codegame"]}, the game closed!'
                break

            print(f"Received move from Player {player_id}: {move}")
            process_player_move(player_id, move)
            broadcast_game_state()

    except Exception as e:
        print(f"Error with Player {player_id}: {e}")

    finally:
        conn.close()
        with lock:
            del connections[player_id]
            print(f"Player {player_id} removed.")


def broadcast_game_state():
    """
    Отправляет обновленное состояние игры всем подключенным игрокам.
    Если клиент отключен или возникает ошибка, сервер логирует событие.

    :return: None
    :raises Exception: Ошибка отправки данных клиенту.
    """
    with lock:
        data = pickle.dumps(game_state)
        for player_id, conn in connections.items():
            try:
                conn.sendall(data)
            except Exception as e:
                print(f"Error sending to Player {player_id}: {e}")


def main():
    """
    Основная функция для запуска сервера игры. Она:
    1. Инициализирует сокет для приема TCP-соединений.
    2. Прослушивает указанный адрес (HOST) и порт (PORT).
    3. Ждет подключения двух игроков.
    4. Запускает обработку каждого игрока в отдельном потоке.
    5. Завершает ожидание после подключения двух игроков и стартует игровой процесс.

    :return: None
    :raises socket.error: Если не удалось создать сокет или привязать его к указанному адресу и порту.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen(2)
            print(f"Server listening on {HOST}:{PORT}")

            player_id = 1
            while player_id <= 2:
                conn, addr = s.accept()
                connections[player_id] = conn
                thread = threading.Thread(target=handle_client, args=(conn, addr, player_id))
                thread.start()
                player_id += 1

            print("Both players connected. Game is starting...")
    except socket.error as e:
        print(f"Error: Failed to create socket: {e}")


if __name__ == "__main__":
    main()
