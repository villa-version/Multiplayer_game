import config
import select
from socket import socket, AF_INET, SOCK_STREAM
import json
from signal import signal, SIGINT

HOST = config.HOST['Server']
PORT = config.PORT
stop = False


class Player:
    client = None
    client_ip = None
    data = None


players = []


def read(sockets, host):
    global players
    for s in sockets:
        if s is host:
            player = Player()
            player.client, player.client_ip = s.accept()
            players.append(player)
            print('Client connected ' + player.client_ip[0])
        else:
            for player in players[:]:
                if s is player.client:
                    recv_string = ''
                    while True:
                        recv_byte = player.client.recv(1).decode()
                        if len(recv_byte) == 0:
                            player.client.close()
                            print('Client disconnected ' + player.client_ip[0])
                            players.remove(player)
                            break
                        elif recv_byte == '\n':
                            player_data = json.loads(recv_string)
                            player.data = player_data
                            break
                        recv_string += recv_byte


def write(sockets):
    global players
    for s in sockets:
        senders = players[:]
        data_senders = []
        recipient = None
        for player in players:
            if player.client is s:
                recipient = player
                senders.remove(recipient)
                break
        for sender in senders:
            if sender.data is not None:
                data = sender.data
                data_senders.append(data)
        if len(data_senders) != 0:
            recipient.client.send((json.dumps(data_senders) + '\n').encode())
            data_senders.clear()


def update_data():
    global players
    for player in players:
        if player.data is not None:
            player.data = None


def main():
    global players, stop

    max_player = 2

    server = socket(AF_INET, SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(max_player)
    while True:
        clients = [player.client for player in players]
        sockets_reading, sockets_writing, _ = select.select([server] + clients, clients, [], 1)
        read(sockets_reading, server)
        write(sockets_writing)
        update_data()

        if stop:
            break

    server.close()


def signal_handler(_, __):
    global stop
    print('Server closing...')
    stop = True


if __name__ == '__main__':
    signal(SIGINT, signal_handler)
    main()
