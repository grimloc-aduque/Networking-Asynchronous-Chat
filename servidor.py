import socket
import os
from threading import Thread


class Server:
    class ClientInServer:
        _socket = None
        name = None

        def __init__(self, s):
            self._socket = s

        def read_socket(self) -> str:
            incoming_msg = None
            while incoming_msg is None:
                incoming_msg = self._socket.recv(1024)
            incoming_msg = incoming_msg.decode('ASCII')
            return incoming_msg

        def write_socket(self, msg: str):
            self._socket.sendall(msg.encode('ASCII'))

        def close_socket(self):
            self._socket.close()

    clients: dict[str:ClientInServer] = {}
    _bindsocket: socket = None

    def __init__(self, port: int):
        self._bindsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._bindsocket.bind(('', port))
        self._bindsocket.listen()
        print("Server listening at port: " + str(port))

    def close_socket(self):
        self._bindsocket.close()

    def wait_connection(self):
        print('Waiting for connection in main thread...')
        sock, fromaddr = self._bindsocket.accept()
        client = self.ClientInServer(sock)
        connection_thread = Thread(target=self.listento_client, args=[client])
        connection_thread.start()

    def set_client_name(self, client: ClientInServer):
        # Recibir nombre del cliente
        while True:
            Connect,Name = client.read_socket().split('|')
            if Name in self.clients:
                client.write_socket(f'CONNECT|{Name}|ERROR|Name already taken')
            else:
                break
        client.write_socket(f'CONNECT|{Name}|Ok')
        client.name = Name
        self.clients[Name] = client
        print(f'Connections updated: {list(self.clients.keys())}')

    def listento_client(self, client: ClientInServer):
        try:
            self.set_client_name(client)
            # Bucle de escucha de mensajes del cliente
            while True:
                incoming_msg = client.read_socket()
                print(f'Command received from {client.name}: "{incoming_msg}" ')
                Fields = incoming_msg.split('|')
                CMD = Fields[0]

                if CMD == 'LIST':
                    outgoing_msg = f'LIST|{"|".join(list(self.clients.keys()))}'
                    client.write_socket(outgoing_msg)
                    continue

                if CMD == 'DISCONNECT':
                    self.clients.pop(client.name)
                    client.write_socket('DISCONNECT')
                    client.close_socket()
                    server.clients.pop(client.name, None)
                    break

                # CHAT|SendTo|Mensaje
                if CMD == 'CHAT':
                    Type, SendTo, Message = Fields
                    if SendTo not in self.clients:
                        client.write_socket('CHAT|ERROR|Client not found')
                        continue
                    client_to_send = self.clients[SendTo]
                    outgoing_msg = f'CHAT|{client.name}|{Message}'
                    client_to_send.write_socket(outgoing_msg)
                    continue

                # FILETRANSFER|Status|TransferTo|Filename
                if CMD == 'FILE':
                    Type, Status, TransferTo, FileName = Fields[0:4]
                    if Status == 'Start':
                        if TransferTo not in self.clients:
                            client.write_socket('FILE|ERROR|Client not found')
                            continue
                        client_to_transfer = self.clients[TransferTo]
                        client.write_socket(f'FILE|Ok')
                        client_to_transfer.write_socket(f'FILE|Start|{client.name}|{FileName}')
                        continue

                    if Status == 'Upload':
                        IDPart, Part = Fields[4:6]
                        client_to_transfer = self.clients[TransferTo]
                        client.write_socket(f'FILE|Ok')
                        client_to_transfer.write_socket(f'FILE|Download|{client.name}|{FileName}|{IDPart}|{Part}')
                        continue

                    if Status == 'End':
                        TotalParts = Fields[4]
                        client_to_transfer = self.clients[TransferTo]
                        client.write_socket(f'FILE|Ok')
                        client_to_transfer.write_socket(f'FILE|End|{client.name}|{FileName}|{TotalParts}')
                        continue

                client.write_socket('CMD|ERROR|Wrong command')

        except:
            client.close_socket()
            server.clients.pop(client.name, None)


if __name__ == "__main__":
    server = Server(port=10024)
    while True:
        try:
            server.wait_connection()
        except:
            break

    server.close_socket()
