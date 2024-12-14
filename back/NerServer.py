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
        self.connect_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
    
    def calculate_checksum(self, filepath, algorithm='md5'):
        hash_func = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(4096):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def send_message(self, message:str, encrypted=True, target=None):
        if encrypted:
            message = f"1{self.encryption.encrypt(message)}" 
        else:
            message = f"0{message}"  
        
        target.send(message.encode())
    #我去主动连接别的server
    def connect_server(self, host, port):
        port = int(port)
        self.connect_socket.connect((host, port)) # 连接
        self.send_message(f"CONN:{self.host};{self.port};{self.client_username}", target=self.connect_socket) # 发送连接消息
        if self.running:
            try:
                data = self.connect_socket.recv(1024)

                if data[0:1] == b'0':
                    data = data[1:].decode()
                elif data[0:1] == b'1':
                    data = self.encryption.decrypt(data[1:].decode())
                
                print(f"连接时接收到的返回数据: {data}")

                if data.startswith("CONN_SUCCESS"):
                    to_host, to_port, nickname = data.split(":")[1].split(";",2)
                    to_port = to_port
                    if to_host == self.host and str(to_port) == str(self.port):
                        self.servers[nickname] = (host, port)
                        print(f"已连接到服务器 {nickname}")

            except Exception as e:
                print(f"Error connect_server: {e}")

    def send_file(self, file_path, target_name):
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_checksum = self.calculate_checksum(file_path, "md5")

            file_info = {
                "file_name": file_name,
                "file_size": file_size,
                "file_checksum": file_checksum
            }
            
            file_info = json.dumps(file_info)
            self.send_message(f"FILE|{self.client_username};{file_info}", target=self.connect_socket)
            time.sleep(0.1)

            with open(file_path, "rb") as file:
                    while chunk := file.read(4096):
                        encoded_chunk = b64encode(chunk).decode()  # Base64 编码
                        self.connect_socket.sendall(encoded_chunk.encode())
                
            print(f"File '{file_name}' sent to {target_name}")
        except Exception as e:
            print(f"Error send_file: {e}")

    def send_image(self, image_path, target_name):
        try:
            image_name = os.path.basename(image_path)
            image_size = os.path.getsize(image_path)

            image_info = {
                "image_name": image_name,
                "image_size": image_size
            }

            image_info = json.dumps(image_info)
            self.send_message(f"IMAGE|{self.client_username};{image_info}", target=self.connect_socket)
            time.sleep(0.1)

            with open(image_path, "rb") as file:
                image_data = file.read()
                self.connect_socket.sendall(image_data)

        except Exception as e:
            print(f"Error send_image: {e}")

    def receive_file(self, client_socket, file_info:dict, username:str):
        try:
            file_name = file_info['file_name']
            file_size = file_info['file_size']
            file_checksum = file_info['file_checksum']

            file_path = os.path.join(self.upload_path, file_name)
            print(f"Receiving file '{file_name}' ({file_size} bytes) from {client_socket}...")

            received_size = 0
            with open(file_path, "wb") as file:
                while received_size < file_size:
                    encrypted_chunk = client_socket.recv(8192).decode()
                    if not encrypted_chunk:  # 防止空数据情况
                        break
                    file_content = b64decode(encrypted_chunk)
                    file.write(file_content)
                    received_size += len(file_content)

            file_checksum_received = self.calculate_checksum(file_path, "md5")
            if file_checksum_received == file_checksum:
                self.conn_to_client.send(f"FILE|{username};{file_path}")
                print("接受完文件了")
            else:
                print(f"File '{file_name}' received but checksum mismatch!")
        except Exception as e:
            print(f"Error receive_file: {e}")

    def receive_image(self, client_socket, image_info:dict, username:str):
        try:
            image_name = image_info['image_name']
            image_size = image_info['image_size']

            image_path = os.path.join(self.upload_path, image_name)
            print(f"接受图片 '{image_name}' ({image_size} bytes) from {client_socket}...")

            received_size = 0
            with open(image_path, "wb") as file:
                while received_size < image_size:
                    image_data = client_socket.recv(8192)
                    if not image_data:
                        break
                    file.write(image_data)
                    received_size += len(image_data)

            self.conn_to_client.send(f"IMAGE|{username};{image_path}")
        except Exception as e:
            print(f"Error receive_image {e}")

    # 通过socket处理与其他server的通信
    def handle_server(self, conn):
        
        while self.running:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                    
                if data[0:1] == b'0':
                    data = data[1:].decode()
                elif data[0:1] == b'1':
                    data = self.encryption.decrypt(data[1:].decode())

                print(f"服务器接受到消息: {data}")
                if data.startswith("CONN:"):
                    try:
                        host, port, nickname = data.split(":")[1].split(";", 2)
                        port = eval(port)
                        self.send_message(f"CONN_SUCCESS:{self.host};{self.port};{self.client_username}", target=conn)
                        self.servers[nickname] = (host, port)
                        self.conn_to_client.send(f"CONN_SUCCESS:{nickname};{host};{port}")
                        print(f"已向管道发送消息")
                    except Exception as e:
                        self.send_message(f"CONN ERROR: {e}", target=conn)
                elif data.startswith("MSG:"):
                    try:
                        message, from_user = data.split(":")[1].split(";", 1)
                        self.conn_to_client.send(f"MSG:{from_user};{message}")
                        # self.connect_socket = conn
                    except Exception as e:
                        self.send_message(f"MSG ERROR: {e}", target=conn)
                elif data.startswith("FILE|"):
                    try:
                        username, file_info = data.split("|")[1].split(";", 1)
                        self.receive_file(conn, json.loads(file_info), username)
                    except Exception as e:
                        print(f"FILE RECEIVE ERROR: {e}")
                elif data.startswith("IMAGE|"):
                    try:
                        username, image_info = data.split("|")[1].split(";", 1)
                        self.receive_image(conn, json.loads(image_info), username)
                    except Exception as e:
                        print(f"IMAGE RECEIVE ERROR: {e}")
                else:
                    print(f"Handle Server received message: {data}")
 
            except Exception as e:
                print(f"Error handle_server: {e}")
                break

    def accept_clients(self):
        while True:
            client_socket, client_address = self.listen_socket.accept()
            print(f"Client connected: {client_address}")
            threading.Thread(target=self.handle_server, args=(client_socket,), daemon=True).start()

    # 通过管道处理与client的通信你
    def start(self,):
        self.listen_socket.bind((self.host, self.port))
        self.listen_socket.listen(2)
        print(f"Server started on {self.host}:{self.port}")
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
                            self.conn_to_client.send("LOGIN_SUCCESS")
                            threading.Thread(target=self.accept_clients, daemon=True).start()
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
                        self.send_message(message=f"MSG:{message};{self.client_username}", target=self.connect_socket)
                        # self.conn_to_client.send("MSG:Sent")
                    except Exception as e:
                        self.conn_to_client.send(f"MSG ERROR: {e}")
                elif msg.startswith("FILE|"):
                    try:
                        target_Name, file_Path = msg.split("|")[1].split(";", 1)
                        self.send_file(file_Path, target_Name)
                    except Exception as e:
                        self.conn_to_client.send(f"FILE ERROR: {e}")
                elif msg.startswith("IMAGE|"):
                    try:
                        target_Name, image_Path = msg.split("|")[1].split(";", 1)
                        self.send_image(image_Path, target_Name)
                    except Exception as e:
                        self.conn_to_client.send(f"IMAGE ERROR: {e}")
                else:
                    print(f"Server received message: {msg}")
            else:
                time.sleep(0.1)
                
                
