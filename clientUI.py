import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess
import platform
from tkinter import *
from cliente import Client
from threading import Thread



class Gui:

    def __init__(self, client:Client):
        # Inicializamos la ventana del chat y la escondemos con withdraw
        self.client = client
        self.client.link_gui(self)
        self.chattingTo = None
        self.root = Tk()
        self.build_root()

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_click_exit()

    def build_root(self):
        self.root.title(f"Chat Asincrono")
        self.root.resizable = False

        # Margen de la ventana
        rootFrame = Frame(self.root, border=3, relief=tk.GROOVE)
        rootFrame.grid()

        # Mensajes

        msgFrame = Frame(rootFrame, border=1, relief=tk.GROOVE)
        msgFrame.grid(row=0, rowspan=20, column=0, columnspan=2, padx=15, pady=10)

        msgLabel = Label(msgFrame, text="Chat")
        msgLabel.pack(side=TOP, fill=BOTH)
        self.msgLabel = msgLabel

        msgScrollbar = Scrollbar(msgFrame)
        msgScrollbar.pack(side=RIGHT, fill=BOTH)

        msgListbox = Listbox(msgFrame)
        msgListbox.pack(side=LEFT, fill=BOTH)
        msgListbox.config(yscrollcommand=msgScrollbar.set, width=40, height=26)
        self.msgListbox = msgListbox

        inputMsg = Entry(rootFrame)
        inputMsg.grid(row=20, column=0, sticky=E + W, padx=15, pady=10)
        self.inputMsg = inputMsg

        btnSend = Button(rootFrame, text="Send Msg", command=self.on_click_send_msg)
        btnSend.grid(row=20, column=1, sticky=E + W, padx=15, pady=10)

        btnFileUpload = Button(rootFrame, text="Upload File", command=self.on_click_uploadfile)
        btnFileUpload.grid(row=21, column=0, columnspan=2, padx=15, pady=10, sticky=E + W)

        # Conexion

        varName = StringVar()
        varName.set("Name:")
        labelName = Label(rootFrame, textvariable=varName)
        labelName.grid(row=0, column=2, sticky=W, padx=15)
        self.varName = varName

        inputName = Entry(rootFrame, width=18)
        inputName.grid(row=0, column=3, sticky=E, padx=15)
        self.inputName = inputName

        btnConnect = Button(rootFrame, text='Connect', command=self.on_click_connect)
        btnConnect.grid(row=1, column=2, columnspan=2, sticky=E + W, padx=15)
        self.btnConnect = btnConnect

        # Clientes conectados

        clientsFrame = Frame(rootFrame, border=1, relief=tk.GROOVE)
        clientsFrame.grid(row=2, rowspan=10, column=2, columnspan=2, padx=15, pady=10, sticky=N + S + E + W)

        clientsLabel = Label(clientsFrame, text="Clientes Conectados")
        clientsLabel.pack(side=TOP, fill=BOTH)

        clientsListbox = Listbox(clientsFrame)
        clientsListbox.pack(side=LEFT, fill=BOTH)
        clientsListbox.config(width=28, height=10)
        self.clientsListbox = clientsListbox

        btnOpenChat = Button(rootFrame, text='Open Chat', command=self.on_click_openchat)
        btnOpenChat.grid(row=12, column=2, columnspan=2, sticky=E + W, padx=15)

        # Archivos Recibidos

        filesFrame = Frame(rootFrame, border=1, relief=tk.GROOVE)
        filesFrame.grid(row=13, rowspan=8, column=2, columnspan=2, padx=15, pady=10, sticky=N + S + E + W)

        filesLabel = Label(filesFrame, text="Received Files")
        filesLabel.pack(side=TOP, fill=BOTH)

        filesListBox = Listbox(filesFrame)
        filesListBox.pack(side=LEFT, fill=BOTH)
        filesListBox.config(width=28, height=8)
        self.filesListBox = filesListBox

        btnOpenFile = Button(rootFrame, text='Open File', command=self.on_click_openfile)
        btnOpenFile.grid(row=21, column=2, columnspan=2, sticky=E + W, padx=15)

        self.root.protocol("WM_DELETE_WINDOW", self.on_click_exit)

    @staticmethod
    def show_error(error):
        messagebox.showerror('Error', f'Error: {error}!')

    # Socket messages Handlers

    def on_list_received(self, clients):
        self.populate_list(self.clientsListbox, clients)

    def on_chat_received(self, From):
        if self.chattingTo == From:
            self.populate_msglist()

    def on_file_received(self, From):
        if self.chattingTo == From:
            self.populate_filelist()

    # Lists

    @staticmethod
    def get_selection(listBox):
        selection = listBox.curselection()
        selected_item = None
        if len(selection) != 0:
            selected_item = listBox.get(selection[0])
        return selected_item

    def get_selected_client(self):
        return self.get_selection(self.clientsListbox)

    def get_selected_file(self):
        return self.get_selection(self.filesListBox)

    @staticmethod
    def populate_list(listBox, items):
        selected = Gui.get_selection(listBox)
        listBox.delete(0, 'end')
        for i in range(len(items)):
            item = items[i]
            listBox.insert(i, item)
            if item == selected:
                listBox.selection_set(i)
        listBox.see('end')

    def populate_msglist(self):
        messages = self.client.load_msgs(self.chattingTo)
        self.populate_list(self.msgListbox, messages)

    def populate_filelist(self):
        files = self.client.load_files(self.chattingTo)
        self.populate_list(self.filesListBox, files)

    # Click event handlers

    def on_click_connect(self):
        global ServerIP, ServerPort
        name = self.inputName.get()
        valid_name = self.client.set_name(name)
        if not valid_name:
            self.show_error('Nombre ya usado')
            return
        self.inputName.grid_forget()
        self.btnConnect.grid_forget()
        self.varName.set(f"Connected to {ServerIP}:{ServerPort}")
        self.root.title(f"Chat Asincrono - Cliente {client.name}")
        Thread(target=client.listen_to_server).start()
        Thread(target=client.send_list).start()

    def on_click_exit(self):
        self.client.send_disconnect()
        self.root.destroy()

    def on_click_openchat(self):
        selected_client = self.get_selected_client()
        if not selected_client:
            self.show_error('Ningun cliente seleccionado')
            return
        if selected_client == self.client.name:
            self.show_error('No esta permitido chatear contigo mismo')
            return
        self.chattingTo = selected_client
        self.msgLabel.config(text=f'Chatting to {self.chattingTo}')
        self.populate_msglist()
        self.populate_filelist()

    def on_click_send_msg(self):
        SendTo = self.chattingTo
        Message = self.inputMsg.get()
        self.client.send_chat(SendTo, Message)
        self.populate_msglist()

    def on_click_uploadfile(self):
        filename = filedialog.askopenfilename()
        client.send_file(self.chattingTo, filename)

    def on_click_openfile(self):
        filename = self.get_selected_file()
        if not filename:
            self.show_error('Ningun archivo seleccionado')
            return
        filepath = f'./chats/{self.chattingTo}/{filename}'
        if platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':  # Windows
            os.startfile(filepath)
        else:  # linux variants
            subprocess.call(('xdg-open', filepath))


if __name__ == '__main__':
    ServerIP = '127.0.0.1'
    ServerPort = 10024
    try:
        client = Client(ServerIP, ServerPort)
        gui = Gui(client)
    except ConnectionRefusedError as e:
        print(e.strerror)
        exit(1)





