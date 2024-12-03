import threading
from client import ChatClient
from server import ChatServer


def start_server():
    HOST = "127.0.0.1"
    PORT = 12345
    ENCRYPTION_KEY = "1234567890123456"  # Ensure the key length is 16, 24, or 32 bytes

    server = ChatServer(HOST, PORT, ENCRYPTION_KEY)
    server.start()


def start_client():
    client = ChatClient(
        server_host="127.0.0.1",
        server_port=12345,
        encryption_key="1234567890123456",  # Ensure the key length matches the server's key
        upload_path=r"Client1UPLOAD",
        download_path=r"Client1DOWNLOAD"
    )
    client.connect()
    client.start_chat()

# Create and start threads for server and client
server_thread = threading.Thread(target=start_server)
client_thread = threading.Thread(target=start_client)

server_thread.start()
client_thread.start()

# Join threads to wait for their completion
server_thread.join()
client_thread.join()