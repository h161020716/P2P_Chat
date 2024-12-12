

class ChatClient:
    def __init__(self, conn_to_server, conn_from_server, conn_to_app, conn_from_app):
        self.conn_to_server = conn_to_server
        self.conn_from_server = conn_from_server
        self.conn_to_app = conn_to_app
        self.conn_from_app = conn_from_app

        self.NAMES = {}
        self.cur_connect_server = None
        self.running = True
    
    def run(self,):
        print("Client running...")
        while self.running:
            msg_From_app = None
            msg_From_server = None

            #检验来自APP的消息
            if self.conn_from_app.poll(0.1):
                msg_From_app = self.conn_from_app.recv()
                print(f"Client APP: {msg_From_app}")
                if msg_From_app.startswith("LOGIN:"):
                    username, password = msg_From_app.split(":")[1].split(";")
                    self.conn_to_server.send(f"LOGIN:{username};{password}")
                elif msg_From_app.startswith("CONN:"):
                    host, port = msg_From_app.split(":")[1].split(";")
                    self.cur_connect_server = (host, port)
                    self.conn_to_server.send(f"CONN:{host};{port}")
                elif msg_From_app.startswith("MSG:"):
                    target_name, message = msg_From_app.split(":")[1].split(";",1)
                    if self.NAMES[target_name]:
                        self.conn_to_server.send(f"MSG:{target_name};{message}")
                

            #检验来自Server的消息
            if self.conn_from_server.poll(0.1):
                msg_From_server = self.conn_from_server.recv()
                print(f"Server: {msg_From_server}")
                if msg_From_server.startswith("LOGIN_SUCCESS"):
                    self.conn_to_app.send("LOGIN_SUCCESS")
                elif msg_From_server.startswith("CONN_SUCCESS"):
                    nickname = msg_From_server.split(":")[1]
                    self.NAMES[nickname] = self.cur_connect_server
                    self.conn_to_app.send(f"CONN_SUCCESS:{nickname}")
                elif msg_From_server.startswith("MSG:"):
                    if "Sent" in msg_From_server:
                        self.conn_to_app.send("MSG_SENT")
                
                