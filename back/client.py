import socket
import threading
import os
import json
import pyaudio
import time
import hashlib
from utils.encryption import Encryption
from base64 import b64encode, b64decode


class ChatClient:
    def __init__(self, server_host, server_port, encryption_key, upload_path, download_path):
        self.server_host = server_host
        self.server_port = server_port
        self.password = None
        self.phone = None
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.encryption = Encryption(encryption_key)
        self.upload_path = upload_path
        self.download_path = download_path
        self.logged_in = False


    def connect(self):
        """连接到服务器并进行登录验证"""
        try:
            self.client_socket.connect((self.server_host, self.server_port))
            print(f"Connected to server at {self.server_host}:{self.server_port}")
            
            # 用户输入电话号码和密码
            self.phone = input("Enter your phone number: ").strip()
            self.password = input("Enter your password: ").strip()

            time.sleep(1)
            # 发送登录请求
            self.send_message(f"LOGIN:{self.phone};{self.password}")
            
            # 开始接收消息的线程
            threading.Thread(target=self.receive_messages, daemon=True).start()

            while not self.logged_in:
                time.sleep(0.1)
        except Exception as e:
            print(f"Connection error: {e}")
            self.client_socket.close()

    def send_message(self, message, encrypted=True,target_user=None):
        """发送加密消息"""
        if target_user:
            message = f"{message};{target_user}"
        
        if encrypted:
            message = f"1{self.encryption.encrypt(message)}"  # 加密消息，开头加 '1'
        else:
            message = f"0{message}"  # 非加密消息，开头加 '0'
        
        self.client_socket.send(message.encode())

    def calculate_checksum(self, filepath, algorithm='md5'):
        """计算文件的校验值"""
        hash_func = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(4096):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def send_file(self, filepath, target_client=None):
        if not os.path.isfile(filepath):
            print(f"File '{filepath}' not found!")
            return

        try:
            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath)
            checksum = self.calculate_checksum(filepath, "md5")

            # 准备文件信息
            file_info = {
                "filename": filename,
                "filesize": file_size,
                "checksum": checksum
            }
            
            self.send_message(f"FILETO:{json.dumps(file_info)};{filepath}", target_user=target_client)

        except Exception as e:
            print(f"Error sending file: {e}")

    def receive_file(self, file_info, source):
        """接收文件并保存到本地"""
        filename = file_info['filename']
        filesize = file_info['filesize']
        filepath = os.path.join(self.download_path, filename)
        print(f"Receiving file '{filename}' ({filesize} bytes) from {source}...")

        with open(filepath, "wb") as file:
            received_size = 0
            while received_size < filesize:
                data = self.client_socket.recv(4096)
                file.write(data)
                received_size += len(data)

        print(f"File '{filename}' received and saved to {filepath}.")


    def receive_messages(self):
        """接收并处理服务器或其他客户端的消息"""
        while True:
            try:
                received_data = self.client_socket.recv(4096).decode()
                if not received_data:
                    break
                
                if str(received_data[0:1]) == '1' :  # 加密消息
                    try:
                        data = self.encryption.decrypt(received_data[1:])
                    except Exception as e:
                        print(f"Error decrypting message: {e}")
                        continue
                elif str(received_data[0:1]) == '0':  # 非加密消息
                    data = received_data[1:]
                else:
                    print(f"Unknown message: {received_data}")
                    continue
                
                print(f"Received data: {data}")

                if data.startswith("CHAT:"):
                    print(data[5:])
                elif data.startswith("LOGIN_SUCCESS"):
                    print("Login successful! Welcome to the chat.")
                    self.logged_in = True
                elif data.startswith("LOGIN_FAILED"):
                    print("Login failed! Please check your phone number and password.")
                elif data.startswith("FROM:"):
                    source, message = data[5:].split(";", 1)
                    print(f"Message from {source}:{message}")
                elif data.startswith("RECEIVED_FILE:"):
                    print(f"File received successfully by the server.")
                elif data.startswith("CHECKSUM_MISMATCH"):
                    print("Checksum mismatch! Server reported a mismatch.")
                elif data.startswith("NEW_FILE:"):
                    file_info, source = data[9:].split(";", 1)
                    file_info = json.loads(file_info)
                    self.receive_file(file_info, source)
                else:
                    print(f"Unknown message: {data}")
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def start_chat(self):
        """启动聊天"""
        if not self.logged_in:
            print("Cannot start chat: Login failed.")
            return
        
        print("Welcome to the chat client! Type 'exit' to quit.")
        while True:
            command = input(
                "Enter a command (chat, chatto, sendto, get, deliver, deliverto, startaudio): \n"
            ).strip().lower()
            if command == "exit":
                print("Exiting...")
                self.client_socket.close()
                break
            elif command == "chat": # 广播消息
                message = input("Enter your message: ")
                self.send_message(f"CHAT:{message}")
            elif command == "sendto": # 发送消息给指定用户
                target = input("Enter target client: ")
                message = input("Enter your message: ")
                self.send_message(f"SENDTO:{target};{message}")
            elif command == "deliverto":# 上传文件给指定客户端
                target = input("Enter target client: ")
                filename = input("Enter filename to upload: ")
                self.send_file(filename, target_client=target)
            elif command == "conn":
                server_host = input("Enter server host: ")
                server_port = int(input("Enter server port: "))
                self.send_message(f"CONN:{server_host};{server_port};{self.phone};{self.password}")
            elif command == "help":
                print("Commands: chat, chatto, sendto, get, deliver, deliverto, startaudio, exit")
            else:
                print("Unknown command.")
    def start(self,):
        self.connect()
        self.start_chat()

if __name__ == "__main__":
    # Replace 'your_key_here' with your encryption key
    client = ChatClient(
        server_host="127.0.0.1",
        server_port=8080,
        encryption_key="SJWKOJM<ASDFASD-",
        upload_path=r"Client1UPLOAD",
        download_path=r"Client1DOWNLOAD"
    )
    client.start()
