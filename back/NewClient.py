import threading
import time 

class ChatClient:
    def __init__(self, conn_to_server, conn_from_server, conn_to_app, conn_from_app):
        self.conn_to_server = conn_to_server
        self.conn_from_server = conn_from_server
        self.conn_to_app = conn_to_app
        self.conn_from_app = conn_from_app

        self.NAMES = {}
        self.cur_connect_server = None
        self.running = True

    def solve_server(self,):
        msg_From_server = None
        while self.running:
            #检验来自Server的消息
            if self.conn_from_server.poll():
                msg_From_server = self.conn_from_server.recv()

                print(f"Client Server: {msg_From_server}")

                if msg_From_server.startswith("LOGIN_SUCCESS"):
                    self.conn_to_app.send("LOGIN_SUCCESS")

                elif msg_From_server.startswith("CONN_SUCCESS:"):
                    nickname, host, port = msg_From_server.split(":")[1].split(";",2)
                    self.NAMES[nickname] = (host, port)
                    self.conn_to_app.send(f"CONN_SUCCESS:{nickname};{host};{port}")

                elif msg_From_server.startswith("MSG:"): 
                    from_user, message = msg_From_server.split(":")[1].split(";",1)
                    self.conn_to_app.send(f"MSG:{from_user};{message}")
                    print("消息已发送")

                elif msg_From_server.startswith("FILE|"):
                    username, file_path = msg_From_server.split("|")[1].split(";",1)
                    self.conn_to_app.send(f"FILE|{username};{file_path}")
                
                elif msg_From_server.startswith("IMAGE|"):
                    username, image_path = msg_From_server.split("|")[1].split(";",1)
                    self.conn_to_app.send(f"IMAGE|{username};{image_path}")

                else:
                    print(f"Client received message: {msg_From_server}")
            else:
                time.sleep(0.1)

    
    def run(self,):
        print("Client running...")
        threading.Thread(target=self.solve_server, daemon=True).start()
        while self.running:
            msg_From_app = None
            
            #检验来自APP的消息
            if self.conn_from_app.poll():
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
                    self.conn_to_server.send(f"MSG:{target_name};{message}")
                elif msg_From_app.startswith("FILE|"):
                    target_name, file_path = msg_From_app.split("|")[1].split(";",1)
                    self.conn_to_server.send(f"FILE|{target_name};{file_path}")
                elif msg_From_app.startswith("IMAGE|"):
                    target_name, image_path = msg_From_app.split("|")[1].split(";",1)
                    self.conn_to_server.send(f"IMAGE|{target_name};{image_path}")
                