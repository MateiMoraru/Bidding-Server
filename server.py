from datetime import datetime
import socket
import sys
import threading
import database

class Server:
    BUFFER_SIZE = 4096
    ENCODING = "UTF-8"

    def __init__(self, ip:str="127.0.0.1", port:int=8080):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = (ip, port)
        self.database = database.Mongo()
        self.listening = True
        self.connections = []
        self.user_data = []


    def run(self):
        self.socket.bind(self.addr)
        self.socket.listen()
        self.log(f"Server is listening for connections on {self.addr}.")
        
        while self.listening:
            conn, addr = self.socket.accept()
            self.log(f"Client connected from {addr}")
            self.connections.append(conn)
            #try:    
            client = threading.Thread(target=self.handle_connection, args=[conn, addr])
            client.start()
            #except Exception as e:
            #    print(e)
            #    self.disconnect_conn(conn, addr)

        
    def handle_connection(self, conn: socket.socket, addr: str):
        name = None

        signup = self.recv(conn)
        if 'Y' in signup or 'y' in signup:
            name = self.handle_sign_up(conn)
        else:
            name = self.handle_log_in(conn)

        if name == False:
            self.send(conn, "shutdown")
            self.log("Invalid name error!")
            self.disconnect_conn(conn, addr)
            self.shutdown()
        else:
            self.log(f"{name} connected successfully")
            self.send(conn, "Connected successfully! -w")
            
        #notifs = self.get_notifications(self, name)
        #printls(notifs)
        #self.sendls(notifs)


    def handle_sign_up(self, conn: socket.socket):
        name, pwd = self.recv(conn).split(' ')
        if len(name) < 2:
            self.log("Your name should consist of more than 1 characters", conn, True)
            self.handle_sign_up(conn)
        if len(pwd) < 2:
            self.log("Your password should consist of more than 1 characters", conn, True)
            self.handle_sign_up(conn)

        print(self.database.search_name(name))

        if not self.database.search_name(name):
            self.database.add_user(name, pwd)
            self.send(conn, "Account created successfully-w")
        else:
            self.log("Account with the same username already exists", conn, True)
            self.handle_sign_up(conn)

        return name
    

    def handle_log_in(self, conn: socket.socket):
        name, pwd = self.recv(conn).split(' ')
        if len(name) < 2:
            self.log("Your name should consist of more than 1 characters", conn, True)
            self.handle_log_in(conn)
        if len(pwd) < 2:
            self.log("Your password should consist of more than 1 characters", conn, True)
            self.handle_log_in(conn)

        if self.database.search_name_pwd(name, pwd):
            self.send(conn, "Logged in successfully-w")
        else:
            self.log("Account specified doesn't exist", conn, True)
            self.handle_log_in(conn)

        return name

    
    def get_notifications(self, name): #TODO: Use mongo
        return ["No notifs:("]



    def shutdown(self):
        self.log(f"Shutting down server!")
        self.listening = False
        self.socket.close()
        sys.exit(0)


    def disconnect_conn(self, conn: socket.socket, addr: str): # TODO: Mutex
        self.log(f"Client disconnected {addr}")
        idx = self.connections.index(conn)
        self.connections.pop(idx)
        self.user_data.pop(idx)


    def send(self, conn: socket.socket, message: str):
        bytes_all = message.encode(self.ENCODING)
        bytes_sent = conn.send(bytes_all)

        if bytes_all != bytes_sent:
            return False
        
        return True
    

    def sendls(self, conn: socket.socket, ls: list):
        message = ""
        for i, el in enumerate(ls):
            message += f"{i}. {el}\n"
        
        self.send(conn, message + '-w')

    
    def recv(self, conn: socket.socket):
        try:
            message = conn.recv(self.BUFFER_SIZE).decode(self.ENCODING)
            return message
        except Exception as e:
            print(e)
            self.disconnect_conn(conn, None)


    def log(self, message: str, conn: socket.socket=None, error: bool=False):
        t = datetime.now()
        if not error:
            msg = f"[INFO {t.hour}:{t.minute}:{t.second}] {message}"
        else:
            msg = f"[ERROR]: {message}"
        print(msg)

        if conn is not None:
            self.send(conn, msg + '-w')
        

def printls(ls: list):
    for i, el in enumerate(ls):
        print(f"{i}. {el}")



if __name__ == "__main__":
    server = Server()
    server.run()
