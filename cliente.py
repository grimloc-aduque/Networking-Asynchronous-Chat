import socket
import time
import datetime
import os
import base64
import math
from cryptography.fernet import Fernet
import collections
import pandas as pd


class Client:
    _socket = None
    name = None
    connected = False
    fernet = None
    gui = None

    def __init__(self, ip, port):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connect_to_server(ip, port)
        self._load_key()
        os.system('mkdir -p ./chats')

    # Private
    def _connect_to_server(self, ip, port):
        self._socket.connect((ip, port))
        self.connected = True

    def _load_key(self):
        file = open('./.key.key', 'rb')
        key = file.read()
        file.close()
        self.fernet = Fernet(key)

    def _read_socket(self) -> str:
        # Desencriptar con clave privada
        incoming_msg = None
        while incoming_msg is None:
            incoming_msg = self._socket.recv(1024)
        incoming_msg = incoming_msg.decode('ASCII')
        return incoming_msg

    def _write_socket(self, msg: str):
        # Encriptar con clave publica
        self._socket.sendall(msg.encode('ASCII'))

    def _close_socket(self):
        self._socket.close()

    def _encrypt_message(self, Message):
        Message = Message.encode("ASCII")
        Message = self.fernet.encrypt(Message)
        Message = Message.decode("ASCII")
        return Message

    def _decrypt_message(self, Message):
        Message = Message.encode("ASCII")
        Message = self.fernet.decrypt(Message)
        Message = Message.decode("ASCII")
        return Message

    # Public
    def link_gui(self, gui):
        self.gui = gui

    def set_name(self, name) -> bool:
        self._write_socket(f'CONNECT|{name}')
        Status = self._read_socket().split('|')[2]
        if Status == 'Ok':
            self.name = name
            return True
        else:
            return False

    # Send messages to server

    def send_list(self):
        while self.connected:
            self._write_socket('LIST')
            time.sleep(5)

    def send_chat(self, SendTo, Message):
        self._append_to_chats(SendTo, 'Sent', Message)
        Message = self._encrypt_message(Message)
        self._write_socket(f'CHAT|{SendTo}|{Message}')


    def send_file(self, SendTo, file_path):
        print(f'Upload file: {file_path}')
        FileName = file_path.split('/')[-1]
        startMsg = f'FILE|Start|{SendTo}|{FileName}'
        self._write_socket(startMsg)
        time.sleep(1)
        file = open(file_path, "rb")
        bin_file = file.read()
        base64_file = base64.b64encode(bin_file)
        ascii_file = base64_file.decode('ASCII')
        PartSize = 900
        TotalParts = math.ceil(len(base64_file)/PartSize)
        for i in range(TotalParts):
            IDPart = i
            FilePart = ascii_file[i*PartSize:(i+1)*PartSize]
            filePartMsg = f'FILE|Upload|{SendTo}|{FileName}|{IDPart}|{FilePart}'
            self._write_socket(filePartMsg)
            time.sleep(1)

        endMsg = f'FILE|End|{SendTo}|{FileName}|{TotalParts}'
        self._write_socket(endMsg)
        file.close()

    def send_disconnect(self):
        self._write_socket('DISCONNECT')
        self.connected = False


    # Listen to messages from server

    def listen_to_server(self):
        while self.connected:
            incoming_msg = self._read_socket()
            print(incoming_msg)
            Fields = incoming_msg.split('|')
            CMD = Fields[0]
            if CMD == 'LIST':
                Names = Fields[1:]
                self.build_folder_structure(Names)
                self.gui.on_list_received(Names)
            if CMD == 'DISCONNECT':
                self._close_socket()
                break
            if CMD == 'CHAT':
                CMD, From, Message = Fields
                Message = self._decrypt_message(Message)
                self._append_to_chats(From, 'Received', Message)
                self.gui.on_chat_received(From)
            if CMD == 'FILE':
                Status = Fields[1]
                if Status == 'Ok':
                    continue
                Type, Status, From, FileName = Fields[0:4]
                if Status == 'Start':
                    FileParts = {}
                if Status == 'Download':
                    IDPart, Part = Fields[4:6]
                    FileParts[int(IDPart)] = Part
                if Status == 'End':
                    TotalParts = int(Fields[4])
                    FileParts = collections.OrderedDict(sorted(FileParts.items()))
                    if TotalParts == len(FileParts):
                        file = open(f'./chats/{From}/{FileName}', 'wb+')
                        base64_file = ""
                        for i in range(TotalParts):
                            FilePart = FileParts[i]
                            base64_file = base64_file + FilePart
                        print(base64_file)
                        bin_file = base64.b64decode(base64_file)
                        file.write(bin_file)
                        file.close()
                        self._append_to_files(From, FileName)
                        self.gui.on_file_received(From)

    # Local Storage
    @staticmethod
    def build_folder_structure(clients):
        for i in range(len(clients)):
            os.system(f'mkdir -p ./chats/{clients[i]}')
            os.system(f'touch ./chats/{clients[i]}/msgs.csv')
            os.system(f'touch ./chats/{clients[i]}/files.csv')

    @staticmethod
    def _append_to_chats(ChattingTo, Direction, Msg):
        time_stamp = time.time()
        str_time_stamp = datetime.datetime.fromtimestamp(time_stamp).strftime('%Y-%m-%d %H:%M:%S')
        os.system(f'echo \"{str_time_stamp},{Direction},{Msg}\" >> ./chats/{ChattingTo}/msgs.csv')

    @staticmethod
    def _append_to_files(ChattingTo, fileName):
        os.system(f'echo \"{fileName}\" >> ./chats/{ChattingTo}/files.csv')

    def load_msgs(self, ChattingTo):
        chat_df = pd.read_csv(f'./chats/{ChattingTo}/msgs.csv', header=None, names=['Time', 'Direction', 'Message'])
        messages = []
        for i in range(len(chat_df)):
            chat = chat_df.loc[i]
            if chat['Direction'] == 'Sent':
                msg = f'{self.name}: {chat["Message"]}'
            else:
                msg = f'{ChattingTo}: {chat["Message"]}'
            messages.append(msg)
        return messages

    @staticmethod
    def load_files(From):
        files_df = pd.read_csv(f'./chats/{From}/files.csv', header=None, names=['Files'])
        files = list(files_df['Files'])
        return files
