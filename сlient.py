import socket
import pickle
import threading

# Кроссплатформенная функция
def get_char():
    '''
    Заимствовано.
    Функция для получения одного символа, введенного пользователем с клавиатуры.

    :return: None
    '''

    try:
        import msvcrt
        return msvcrt.getch()
    except ImportError:
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def clear():
    '''
    Заимствовано.
    Очищает экран терминала/консоли.

    '''

    print("\033[H\033[J", end = "")


HOST = "127.0.0.1"
PORT = 65434


game_state = {
    "maze": None, 
    "players": {1: {"x": 1, "y": 1, "lives": 3, "keys": 0,"gems": 0}, 2: {"x": 1, "y": 1, "lives": 3,"keys": 0,"gems": 0}},  # Позиции игроков
    "items": [],  #
    "mobs": None,   
    "level": 0,
    "codegame": 0,
    "message": ""
}


def game_menu():
    '''
    Отображает главное меню игры и обрабатывает выбор пользователя.

    Эта функция предоставляет игроку возможность выбрать один из двух вариантов:
    - Создать новую игру (выбрав "N").
    - Присоединиться к существующей игре (выбрав "J").

    В зависимости от выбора пользователя, функция:
    - Если выбран вариант "N", запрашивает уровень игры (1, 2 или 3) и сохраняет его в глобальном состоянии игры.
    - Если выбран вариант "J", запрашивает код игры и сохраняет его в глобальном состоянии игры.
    - Если ввод пользователя неверный, выводится соответствующее сообщение об ошибке, и программа завершает выполнение.

    Глобальная переменная:
        game_state (dict): Словарь, хранящий состояние игры. После вызова функции:
        - Ключ "codegame" будет содержать выбор пользователя ("N" или "J").
        - Ключ "level" будет содержать уровень игры (если был выбран вариант "N").

    Исключения:
        В случае неверного ввода (некорректные команды или код игры), программа завершает выполнение через sys.exit().
    '''

    global game_state
    clear()
    print("    --- Menu ---")
    print(" N) Create new game")
    print(" J) Join existing game")
    choice = input("\n    Insert command (N/J): ").strip().upper()
    game_state["codegame"] = choice
    if choice == "N":
        level = input("\n    Insert level game (1,2,3): ").strip()
        if level in ["1", "2", "3"]:
            game_state["level"] = int(level)
            return game_state["level"]
        else:
            raise ValueError("Invalid level. Please enter 1, 2, or 3.")
    elif choice == "J":
        game_state["codegame"] = input("\n    Insert code game: ").strip()
        if not (game_state["codegame"]).isdigit():
            print("Invalid code! Please restart the game.")
    else:
        raise ValueError("Invalid choice. Please restart the game.")


def print_game_state(state):
    '''
    Отображает текущее состояние игры, включая лабиринт, позиции игроков,
    код игры и сообщение.
    Функция очищает экран и выводит на экран следующие данные:
    - Лабиринт игры, представленный в виде двумерного списка строк.
    - Позиции игроков в формате "Player <ID>: <Position>".
    - Код игры, если он не равен 0.
    - Сообщение, если оно есть.

    :param state: dict
    :return: None
    '''
    clear()
    print("\n--- Current state game ---")
    if state["maze"]:
        for row in state["maze"]:
            print("".join(row))
    print("\nPlayers:")
    for player_id, pos in state["players"].items():
        print(f"Player {player_id}: {pos}")
    print("-----------------------------")
    if game_state["codegame"] != 0:
        print(f'Code the game: {state["codegame"]}')
    if state["message"] != "":
        print(state["message"][1:])

# Поток для приема данных с сервера
def receive_data(sock):
    '''
    Функция для приема данных с сервера
    1. Получает данные от сервера через сокет.
    2. Десериализирует эти данные с помощью pickle.
    3. Обновляет глобальное состояние игры.

    :param sock: Соединение с сервером, через которое получаются данные
    :type sock: socket.socket
    :return: None
    :raises Exception: Если возникает ошибка при получении или обработке данных от клиента.
    '''
    global game_state
    while True:
        try:
            raw_data = sock.recv(4096)
            if not raw_data:
                print("Disconnected from server.")
                break
            state = pickle.loads(raw_data)
            game_state = state
            print_game_state(state)
            if state["codegame"] in ["N", "J"] and state["codegame"] != 0:
                print("Game is starting!")
            if game_state["message"][0:1] == "@": # @ - признак конца игры - отключение от сервера
                break
        except Exception as e:
            print(f"Error receiving data: {e}")
            break

def main():
    '''
    Основная функция игры, которая управляет подключением клиента к серверу,
    отправкой команд игрока и обработкой данных от сервера.

    Функция выполняет следующие действия:
    1. Выводит меню с помощью функции `game_menu()`.
    2. Подключается к серверу по указанному адресу и порту.
    3. Отправляет начальное состояние игры на сервер.
    4. Создаёт поток для получения данных от сервера с помощью функции `receive_data`.
    5. Запускает игровой цикл, в котором:
    - Читает нажатия клавиш для управления персонажем (влево, вправо, вверх, вниз).
    - Отправляет команды серверу в виде сериализованных строк.
    - Проверяет сигнал о завершении игры на основе сообщения от сервера.

    :return: None
    :raises Exception: Если возникает ошибка при получении к серверу.
    '''
    global game_state
    #делаем установки в меню
    game_menu()

    #подключаемся к серверу
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            print("Connected to server successfully. Waiting for game setup...")
        except Exception as e:
            print(f"Error connecting to server: {e}")
            exit()

        s.sendall(pickle.dumps(game_state))

        recv_thread = threading.Thread(target = receive_data, args = (s,))
        recv_thread.start()

        while True:
            try:
              
                press = get_char()
                if press in [b'a', b'A']:
                    s.sendall(pickle.dumps("left"))
                elif press in [b'd', b'D']:
                    s.sendall(pickle.dumps("right"))
                elif press in [b'w', b'W']:
                    s.sendall(pickle.dumps("up"))
                elif press in [b's', b'S']:
                    s.sendall(pickle.dumps("down"))
                elif press.lower() == b"q":
                    print("Quitting game.")
                    break
                else:
                    continue
            except Exception as e:
                print(f"Error in game loop: {e}")
                break

            if game_state["message"][0:1] == "@":
                break
    print(f"Game over!")

if __name__ == "__main__":
    main()
