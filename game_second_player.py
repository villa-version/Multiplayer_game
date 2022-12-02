import pygame, sys
import config
from socket import socket, AF_INET, SOCK_STREAM
import json
from signal import signal, SIGINT
import select


HOST = config.HOST['Client']
PORT = config.PORT

WIDTH = 1000
HEIGHT = 700
WINDOW_NAME = 'The Second Player'
held_key = []
screen = None
stop_program = False
start_x = WIDTH//2
start_y = HEIGHT//2
diameter = 50
player_color = (0, 0, 0)
player_speed = 1
id_player = 'The second player'
cd_send = True


class Player:

    def __init__(self, x, y, d, col, screen, speed, player_id):
        self.x = x
        self.y = y
        self.d = d
        self.col = col
        self.screen = screen
        self.speed = speed
        self.id_player = player_id

    def draw(self):
        pygame.draw.circle(self.screen, self.col, (self.x, self.y), self.d)


def connect_server():
    global stop_program
    try:
        client = socket(AF_INET, SOCK_STREAM)
        client.connect((HOST, PORT))
        client.setblocking(False)
        return client
    except ConnectionRefusedError:
        print('You were not connected to server.')
        stop_program = True
        return False


class MainController:

    def __init__(self, client):
        global screen
        self.player = Player(start_x, start_y, diameter, player_color, screen, player_speed, id_player)
        self.client = client
        self.other_players = []

    def update(self):
        self.move_player()
        self.draw_objects()
        self.data_operations()

    def draw_objects(self):
        self.player.draw()
        for player in self.other_players:
            player.draw()

    def move_player(self):
        global held_key
        for item in range(len(held_key)):
            if held_key[item] == 'UP':
                self.player.y -= self.player.speed
            if held_key[item] == 'DOWN':
                self.player.y += self.player.speed
            if held_key[item] == 'LEFT':
                self.player.x -= self.player.speed
            if held_key[item] == 'RIGHT':
                self.player.x += self.player.speed

    def append_player(self, data):
        self.other_players.append(Player(data['x'], data['y'], diameter, player_color,
                                         screen, player_speed, data['player_id']))

    def give_data_to_player(self, data):
        global cd_send
        cd_send = True
        for elem in data[:]:
            for player in self.other_players:
                if player.id_player in elem['player_id']:
                    player.x = elem['x']
                    player.y = elem['y']
                    data.remove(elem)
                    break
        for d in data:
            self.append_player(d)

    def send(self, data):
        global cd_send
        if cd_send:
            cd_send = False
            self.client.send(data.encode())

    def accept_data(self):
        global cd_send
        info_player = ''
        while True:
            response = self.client.recv(1).decode()
            if response == '\n':
                return json.loads(info_player)
            info_player += response

    def data_operations(self):
        global stop_program
        try:
            socket_ready_to_read, socket_ready_to_write, _ = select.select([self.client], [self.client], [], 0)
            if self.client in socket_ready_to_write:
                d = {'player_id': self.player.id_player, 'x': self.player.x, 'y': self.player.y}
                self.send(json.dumps(d) + '\n')
            if self.client in socket_ready_to_read:
                self.give_data_to_player(self.accept_data())
        except ConnectionAbortedError:
            self.client.close()
            stop_program = True


def main():
    global held_key, screen, stop_program
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(WINDOW_NAME)
    result = connect_server()
    if result is not False:
        main_controller = MainController(result)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        held_key.append('UP')
                    if event.key == pygame.K_s:
                        held_key.append('DOWN')
                    if event.key == pygame.K_a:
                        held_key.append('LEFT')
                    if event.key == pygame.K_d:
                        held_key.append('RIGHT')
                elif event.type == pygame.KEYUP:
                    held_key.clear()

            screen.fill((255, 255, 255))
            main_controller.update()
            pygame.display.update()

            if stop_program:
                break

        main_controller.client.close()


def signal_handler(_, __):
    global stop_program
    print('Client closing...')
    stop_program = True


if __name__ == '__main__':
    signal(SIGINT, signal_handler)
    main()
