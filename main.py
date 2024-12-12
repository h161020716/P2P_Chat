import threading
from multiprocessing import Pipe
from back.NewClient import ChatClient
from back.NerServer import ChatServer
from front.app import ChatApp
import tkinter as tk
import socket
import time

if __name__ == "__main__":
    # Server <-> Client
    client_to_server, server_from_client = Pipe()
    server_to_client, client_from_server = Pipe()

    app_to_client, client_from_app = Pipe()
    client_to_app, app_from_client = Pipe()

    server_HOST = socket.gethostname() 
    server_PORT = 8080
    server_ENCRYPTION_KEY = "SJWKOJM<ASDFASD-"
    root = tk.Tk()

    server = ChatServer(server_HOST, server_PORT, server_ENCRYPTION_KEY, server_to_client, server_from_client)
    client = ChatClient(client_to_server, client_from_server, client_to_app, client_from_app)
    app = ChatApp(root, app_to_client, app_from_client)

    server_thread = threading.Thread(target=server.start, daemon=True)
    client_thread = threading.Thread(target=client.run, daemon=True)

    app.setup_login_ui()
    server_thread.start()
    client_thread.start()

    root.mainloop()
    print("Main thread exiting...")
