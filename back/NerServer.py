import socket
import threading
import os
import time
import json
import hashlib
from base64 import b64decode, b64encode
from back.utils.encryption import Encryption

class ChatServer:
    def __init__(self, host, port, encryption_key, server_to_client, client_to_server):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_username = None
        
        self.encryption = Encryption(encryption_key)
        self.upload_path = "ServerUpload"
        self.download_path = "ServerDownload"

        self.running = True
        self.servers = {}  
        self.conn_to_client = server_to_client
        self.conn_from_client = client_to_server

        if not os.path.exists(self.upload_path):
            os.makedirs(self.upload_path, exist_ok=True)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path, exist_ok=True)
    
    def check_user(self, username, password):
        return True

    def send_message(self, message:str, encrypted=True, target=None):
        if encrypted:
            message = f"1{self.encryption.encrypt(message)}" 
        else:
            message = f"0{message}"  
        
        target.send(message.encode())
    #我去主动连接别的server
    def connect_server(self, host, port):
        port = int(port)
        self.server_socket.connect((host, port)) # 连接
        self.send_message(f"CONN:{self.host};{self.port};{self.client_username}", target=self.server_socket) # 发送连接消息

        while self.running:
            try:
                data = self.server_socket.recv(1024)
                
                if not data:
                    break

                if data[0:1] == b'0':
                    data = data[1:].decode()
                elif data[0:1] == b'1':
                    data = self.encryption.decrypt(data[1:].decode())

                if data.startswith("CONN_SUCCESS"):
                    to_host, to_port, nickname = data.split(":")[1].split(";",2)
                    to_port = to_port
                    if to_host == self.host and to_port == self.port:
                        self.conn_to_client.send(f"CONN_SUCCESS:{nickname}")
                        threading.Thread(target=self.handle_server, args=(self.server_socket, (host, port)), daemon=True).start()
            except Exception as e:
                print(f"Error connect_server: {e}")
                break

    # 通过socket处理与其他server的通信
    def handle_server(self, conn, addr):
        while self.running:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                    
                if data[0:1] == b'0':
                    data = data[1:].decode()
                elif data[0:1] == b'1':
                    data = self.encryption.decrypt(data[1:].decode())

                print(f"Server received message: {data}")
                if data.startswith("CONN:"):
                    try:
                        host, port, nickname = data.split(":")[1].split(";", 2)
                        port = eval(port)
                        self.server_socket.connect((host, port))
                        self.send_message(f"CONN_SUCCESS:{self.host};{self.port};{self.client_username}", target=self.server_socket)
                        self.servers[nickname] = (host, port)
                        self.conn_to_client.send(f"CONN_SUCCESS:{nickname}")
                    except Exception as e:
                        self.send_message(f"CONN ERROR: {e}", target=conn)
                elif data.startswith("MSG:"):
                    try:
                        message, from_user = data.split(":")[1].split(";", 1)
                        self.conn_to_client.send(f"MSG:{from_user};{message}")
                    except Exception as e:
                        self.send_message(f"MSG ERROR: {e}", target=conn)

            except Exception as e:
                print(f"Error handle_server: {e}")
                break
                
    # 通过管道处理与client的通信
    def start(self,):
        print("Server started")
        while self.running: 
            if self.conn_from_client.poll(0.1): 
                msg = self.conn_from_client.recv()
                print(f"Server received message: {msg}")
                if msg == "exit":
                    self.running = False
                    self.conn_to_client.send("ServerClosed")
                elif msg.startswith("LOGIN:"):
                    try:
                        username, password = msg.split(":")[1].split(";")
                        if self.check_user(username, password):
                            self.client_username = username
                            print("123123123")
                            self.conn_to_client.send("LOGIN_SUCCESS")
                        else:
                            self.conn_to_client.send("ERROR: 用户名或密码错误")
                    except Exception as e:
                        self.conn_to_client.send(f"LOGIN ERROR: {e}")
                elif msg.startswith("CONN:"):
                    try:
                        host, port = msg.split(":")[1].split(";")
                        self.connect_server(host, port)
                    except Exception as e:
                        self.conn_to_client.send(f"CONN ERROR: {e}")
                elif msg.startswith("MSG:"):
                    try:
                        target_Name, message = msg.split(":")[1].split(";")
                        self.send_message(message=f"MSG:{message};{self.client_username}", target=self.server_socket)
                        self.conn_to_client.send("MSG:Sent")
                    except Exception as e:
                        self.conn_to_client.send(f"MSG ERROR: {e}")
                