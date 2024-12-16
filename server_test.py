import pytest
import pickle
from unittest.mock import Mock, patch, call
from server import (
    generate_maze,
    game_state,
    checkstep,
    process_player_move,
    broadcast_game_state,
    handle_client,
    connections,
    main,
)
import socket


# Тестирование функции checkstep
@pytest.fixture
def fix_game():
    game_state["maze"] = [
        ["\u2588", "\u2588", "\u2588", "\u2588"],
        ["\u2588", " ", " ", "\u2588"],
        ["\u2588", "K", "\u2591", "\u2588"],
        ["\u2588", "\u2588", "\u2588", "\u2588"]
    ]
    game_state["players"] = {
        1: {"x": 1, "y": 1, "lives": 3, "keys": 1, "gems": 0},
        2: {"x": 1, "y": 1, "lives": 3, "keys": 0, "gems": 0},
    }


def test_checkstep_positive_empty_cell(fix_game):
    assert checkstep(2, 1, 1) is True


def test_checkstep_cell_with_key(fix_game):
    assert checkstep(1, 2, 2) is True


def test_checkstep_open_door_with_key(fix_game):
    assert checkstep(2, 2, 1) is True  
    assert game_state["players"][1]["keys"] == 0


def test_checkstep_into_wall(fix_game):
    assert checkstep(0, 0, 1) is False


def test_checkstep_open_door_without_key(fix_game):
    assert checkstep(2, 2, 2) is False


def test_checkstep_invalid_coordinates(fix_game):
    with pytest.raises(IndexError):
        checkstep(-1, 0, 1)  

    with pytest.raises(IndexError):
        checkstep(10, 10, 1)  


def test_checkstep_invalid_player_id(fix_game):
    with pytest.raises(KeyError):
        checkstep(1, 1, 3)


# Тестирование функции process_player_move
@pytest.fixture
def fixed_game():
    game_state["maze"] = [
        ["\u2588", "\u2588", "\u2588", "\u2588"],
        ["\u2588", " ", "K", "\u2588"],
        ["\u2588", "M", "E", "\u2588"],
        ["\u2588", "\u2588", "\u2588", "\u2588"]
    ]
    game_state["players"] = {
        1: {"x": 1, "y": 1, "lives": 3, "keys": 0, "gems": 0},
    }
    game_state["mobs"] = [{"x": 1, "y": 2, "d": 1}]
    game_state["message"] = ""


def test_player_pick_key(fixed_game):
    process_player_move(1, "right")  
    assert game_state["players"][1]["keys"] == 1
    assert game_state["message"] == "!Player 1 picked up a key! Total keys: 1"


def test_player_hits_mob(fixed_game):
    process_player_move(1, "down")  
    assert game_state["players"][1]["lives"] == 2
    assert game_state["players"][1]["x"] == 1  
    assert game_state["players"][1]["y"] == 1
    assert game_state["message"] == "!Player 1 hit a mob! Lives left: 2"


def test_player_opens_door_without_key(fixed_game):
    with pytest.raises(ValueError):
        process_player_move(1, "diagonally")
        

@pytest.fixture
def mock_socket():
    mock_conn = Mock()
    mock_conn.recv = Mock()
    mock_conn.sendall = Mock()
    mock_conn.close = Mock()
    return mock_conn


@pytest.fixture
def reset_game_state():
    game_state["maze"] = None
    game_state["players"] = {
        1: {"x": 1, "y": 1, "lives": 3, "keys": 0, "gems": 0},
        2: {"x": 1, "y": 1, "lives": 3, "keys": 0, "gems": 0}
    }
    game_state["items"] = []
    game_state["mobs"] = None
    game_state["level"] = 0
    game_state["codegame"] = 0
    game_state["message"] = ""


@pytest.fixture
def mock_connections(reset_game_state):
    connections.clear()
    yield
    connections.clear()


# Тестирование функции handle_client
@pytest.mark.parametrize("player_id", [1, 2])
def test_initial_game_state_sent(mock_socket, reset_game_state, mock_connections, player_id):
    mock_socket.recv.return_value = b''
    connections[player_id] = mock_socket
    handle_client(mock_socket, ('0.0.0.0', 65434), player_id)
    mock_socket.sendall.assert_called_once_with(pickle.dumps(game_state))
    mock_socket.close.assert_called_once()


def test_player_movement(mock_socket, reset_game_state, mock_connections):
    move = "up"
    game_state["maze"] = generate_maze(1)
    game_state["players"][1] = {"x": 1, "y": 2, "lives": 3, "keys": 0, "gems": 0}
    mock_socket.recv.side_effect = [pickle.dumps(move), b'']
    connections[1] = mock_socket
    with patch("server.process_player_move") as mock_process_move:
        handle_client(mock_socket, ('0.0.0.0', 65434), 1)
        mock_process_move.assert_called_once_with(1, move)


def test_client_disconnect(mock_socket, reset_game_state, mock_connections):
    mock_socket.recv.return_value = b''
    connections[1] = mock_socket
    handle_client(mock_socket, ('0.0.0.0', 65434), 1)
    mock_socket.close.assert_called_once()


def test_invalid_game_code(mock_socket, reset_game_state, mock_connections):
    game_state["codegame"] = 21
    invalid_move = {"codegame": 7, "level": 1}
    mock_socket.recv.side_effect = [pickle.dumps(invalid_move), b'']
    connections[1] = mock_socket
    handle_client(mock_socket, ('127.0.0.1', 65434), 1)
    assert "wrong code" in game_state["message"]
    assert "7" in game_state["message"]
    mock_socket.close.assert_called_once()


def test_handle_client_with_unexpected_exception(mock_socket, reset_game_state):
    mock_socket.recv.side_effect = Exception("Unexpected error during receiving data")
    connections[1] = mock_socket
    with pytest.raises(Exception):
        handle_client(mock_socket, ('0.0.0.0', 65434), 1)
    mock_socket.close.assert_called_once()
    assert 1 not in connections


# Тестирование функции broadcast_game_state
def test_broadcast_game_state_no_connections(mock_connections):
    broadcast_game_state()


def test_broadcast_game_state_one_connection(mock_connections, reset_game_state):
    mock_conn = Mock()
    connections[1] = mock_conn
    broadcast_game_state()
    mock_conn.sendall.assert_called_once_with(pickle.dumps(game_state))


def test_broadcast_game_state_multiple_connections(mock_connections, reset_game_state):
    mock_conn1 = Mock()
    mock_conn2 = Mock()
    connections[1] = mock_conn1
    connections[2] = mock_conn2
    broadcast_game_state()
    mock_conn1.sendall.assert_called_once_with(pickle.dumps(game_state))
    mock_conn2.sendall.assert_called_once_with(pickle.dumps(game_state))


def test_broadcast_game_state_connection_error(mock_connections, reset_game_state):
    mock_conn1 = Mock()
    mock_conn2 = Mock()
    mock_conn1.sendall.side_effect = Exception("Connection error")
    connections[1] = mock_conn1
    connections[2] = mock_conn2
    broadcast_game_state()
    mock_conn1.sendall.assert_called_once_with(pickle.dumps(game_state))
    mock_conn2.sendall.assert_called_once_with(pickle.dumps(game_state))
    assert 1 in connections
    assert 2 in connections


# Тестирование функции main
@patch("socket.socket")
@patch("threading.Thread.start")
def test_main_function_successful(mock_thread_start, mock_socket):
    mock_socket_instance = Mock()
    mock_socket_instance.bind = Mock()
    mock_socket_instance.listen = Mock()
    mock_socket_instance.accept = Mock(side_effect=[
        (mock_socket_instance, ('0.0.0.0', 65434)),
        (mock_socket_instance, ('0.0.0.0', 65434))
    ])
    mock_socket_instance.__enter__ = Mock(return_value=mock_socket_instance)
    mock_socket_instance.__exit__ = Mock(return_value=None)
    mock_socket.return_value = mock_socket_instance
    with patch("builtins.print"):
        main()
    mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
    mock_socket_instance.bind.assert_called_once_with(('0.0.0.0', 65434))
    mock_socket_instance.listen.assert_called_once_with(2)
    assert mock_socket_instance.accept.call_count == 2
    assert mock_thread_start.call_count == 2


@patch("socket.socket")
def test_main_function_socket_creation_failure(mock_socket):
    mock_socket.side_effect = socket.error("Failed to create socket")
    with patch("builtins.print") as mock_print:
        main()
        mock_print.assert_called_with("Error: Failed to create socket: Failed to create socket")
