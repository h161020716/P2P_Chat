import socket
import threading
import os
import time
import json
import hashlib
from base64 import b64decode, b64encode
from utils.encryption import Encryption


class ChatServer:
    def __init__(self, host, port, encryption_key):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}  # {phone: (socket, address)}
        self.peer_servers = {}  # 其他服务器的连接
        self.encryption = Encryption(encryption_key)
        self.upload_path = "ServerUpload"
        self.download_path = "ServerDownload"
        self.logged_in = False
        self.client_phone = None

        if not os.path.exists(self.upload_path):
            os.makedirs(self.upload_path, exist_ok=True)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path, exist_ok=True)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        threading.Thread(target=self.accept_clients, daemon=True).start()

    def accept_clients(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Client connected: {client_address}")
            threading.Thread(target=self.authenticate_client, args=(client_socket, client_address), daemon=True).start()
    
    def authenticate_client(self, client_socket, client_address):
        try:
            received_data = client_socket.recv(1024).decode()
            
            if received_data.startswith("0"):
                received_data = received_data[1:]
            elif received_data.startswith("1"):
                received_data = self.encryption.decrypt(received_data[1:])
            else:
                self.send_message("LOGIN_FAILED:Invalid format", encrypted=False, target=client_socket)
                return
            
            if not received_data.startswith("LOGIN:"):
                self.send_message("LOGIN_FAILED:Invalid format", encrypted=False, target=client_socket)
                return

            print(f"Received login data from {client_address}: {received_data}")
            login_info = received_data[6:]  
            username, password = login_info.split(";")
            self.client_phone = username
            if self.validate_user(username, password):
                self.clients[username] = (client_socket, client_address) # 维护用户的连接信息
                self.send_message(message="LOGIN_SUCCESS",encrypted=False, target=client_socket)
                print(f"{username} has joined the chat.")
                threading.Thread(target=self.handle_client, args=(client_socket, username), daemon=True).start()
            else:
                self.send_message("LOGIN_FAILED:Invalid credentials", encrypted=False, target=client_socket)
                print(f"Invalid login attempt from {client_address}")
        except Exception as e:
            print(f"Error during client initialization: {e}")
            client_socket.close()

    
    def validate_user(self, username, password):
        return True
    
    def send_message(self, message:str, encrypted=True, target=None):
        if encrypted:
            message = f"1{self.encryption.encrypt(message)}" 
        else:
            message = f"0{message}"  
        
        target.send(message.encode())

    def send_to_target(self, target_username, message, from_username):
        if target_username in self.clients:
            target_socket, _ = self.clients[target_username]
            try:
                self.send_message(f"FROM:{from_username};{message}", encrypted=True, target=target_socket)
                print(f"Message sent to {target_username}")
            except Exception as e:
                print(f"Error sending message to {target_username}: {e}")
        else:
            print(f"User {target_username} not found.")
            sender_socket, _ = self.clients[from_username]
            self.send_message(f"User {target_username} not found.", encrypted=False, target=sender_socket)

    def push_file(self, to_username, file_info, file_path):
        """将文件转发给指定用户"""
        if to_username in self.clients:
            target_socket, _ = self.clients[to_username]
            try:
                self.send_to_target(to_username, f"FILE_FROM:{json.dumps(file_info)};{self.client_phone}", to_username)
                
                print(f"File '{file_info['filename']}' sent to {to_username}")
                time.sleep(0.5)

                with open(file_path, "rb") as file:
                    while chunk := file.read(4096):
                        encoded_chunk = b64encode(chunk).decode()  # Base64 编码
                        target_socket.sendall(encoded_chunk.encode())

                print(f"File sent to {to_username} successfully.")
            except Exception as e:
                print(f"Error sending file to {to_username}: {e}")


    def broadcast(self, message:str, exclude=None):
        """广播消息到所有客户端"""
        for client_socket, _ in self.clients.values():
            if client_socket != exclude:
                try:
                    self.send_message(message, encrypted=True, target=client_socket)
                except Exception as e:
                    print(f"Error broadcasting message: {e}")

    def disconnect_client(self, username):
        """处理客户端断开连接"""
        if username in self.clients:
            client_socket, _ = self.clients[username]
            client_socket.close()
            del self.clients[username]
            print(f"{username} has disconnected.")
            # self.broadcast(f"{username} has left the chat.")

    def calculate_checksum(self, filepath, algorithm='md5'):
        """计算文件的校验值"""
        hash_func = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(4096):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    
    def receive_file(self, client_socket, file_info: dict):
        try:
            filename = file_info["filename"]
            filesize = file_info["filesize"]
            checksum = file_info["checksum"]

            print(f"Receiving file '{filename}' ({filesize} bytes)...")
            # client_socket.sendall("READY".encode())  # 通知客户端准备接收

            received_size = 0
            with open(f"{self.upload_path}/{filename}", "wb") as file:
                while received_size < filesize:
                    encrypted_chunk = client_socket.recv(8192).decode()
                    if not encrypted_chunk:  # 防止空数据情况
                        break
                    # decoded_chunk = self.decryption.decrypt(encrypted_chunk)
                    file_content = b64decode(encrypted_chunk)
                    file.write(file_content)
                    received_size += len(file_content)

            # 校验文件完整性
            server_checksum = self.calculate_checksum(f"{self.upload_path}/{filename}", "md5")
            if server_checksum == checksum:
                self.send_message(message="RECEIVED_FILE", encrypted=False, target=client_socket)
                print(f"File '{filename}' received successfully.")
            else:
                self.send_message(message="CHECKSUM_MISMATCH", encrypted=False, target=client_socket)
                print(f"Checksum mismatch for file '{filename}'.")
        except Exception as e:
            print(f"Error receiving file: {e}")
        
    def connect_to_server(self, server_host, server_port, phone, password):
        """连接到其他服务器"""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((server_host, server_port))
            self.send_message(f"SERVER_LOGIN:{phone};{password}", target=server_socket)
        except Exception as e:
            print(f"Error connecting to server {server_host}:{server_port}: {e}")
    
    def receive_server_login(self, server_socket, nickname):
        self.peer_servers[nickname] = server_socket
        self.send_message(message="LOGIN_SUCCESS",target=server_socket)

    def handle_client(self, client_socket, username):
        while True:
            try:
                data = client_socket.recv(4096) # 接收数据
                if not data:
                    break

                if data[0:1] == b'0':
                    data = data[1:].decode()
                elif data[0:1] == b'1':
                    data = self.encryption.decrypt(data[1:].decode())
                 
                print(self.clients)
                # 处理不同类型的消息
                if data.startswith("CHAT:"):
                    # 广播消息
                    message = data[5:]
                    self.broadcast(f"FROM:{username};{message}", exclude=client_socket)
                elif data.startswith("FILETO:"):
                    # 定向文件发送
                    file_info, file_path, target_client = data[7:].split(";", 2)
                    file_info = json.loads(file_info)
                    self.push_file(target_client, file_info, file_path)
                elif data.startswith("SENDTO:"):
                    # 定向消息
                    target_username, message = data[7:].split(";", 1)
                    self.send_to_target(target_username, message, username)
                elif data.startswith("CONN:"):
                    server_host, server_port, phone, password = data[5:].split(";", 3)
                    self.connect_to_server(server_host, int(server_port), phone, password)

# 上面是接受客户端发送的消息，下面是接受服务器消息
                
                elif data.startswith("FILE_FROM:"):
                    file_info, source_client = data[9:].split(";", 1)
                    file_info = json.dumps(file_info)
                    self.receive_file(source_client, json.loads(file_info))
                    self.send_message("NEW_FILE:{file_info};{source_client}",
                                       encrypted=False, target=self.clients[self.client_phone][0])
                elif data.startswith("SERVER_LOGIN:"):
                    phone, password = data[13:].split(";", 1)
                    self.receive_server_login(client_socket, phone, password)
                elif data.startswith("LOGIN_SUCCESS"):
                    print("Login successful! Welcome to the chat.")
                    self.logged_in = True
                elif data.startswith("LOGIN_FAILED"):
                    print("Login failed! Please check your phone number and password.")
                elif data.startswith("EXIT"):
                    break
            except Exception as e:
                print(f"Error with {username}: {e}")
                break

        self.disconnect_client(username)


if __name__ == "__main__":
    HOST = "0.0.0.0"
    PORT = 8080
    ENCRYPTION_KEY = "SJWKOJM<ASDFASD-"

    server = ChatServer(HOST, PORT, ENCRYPTION_KEY)
    server.start()

    while True:
        try:
            command = input("Server Command> ")
            if command.lower() == "exit":
                print("Shutting down server...")
                break
        except KeyboardInterrupt:
            print("Shutting down server...")
            break
