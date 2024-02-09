from datetime import datetime
import socket
import sys
import threading
from typing import List
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
            self.log("Invalid name", conn, True)
            self.disconnect_conn(conn, addr)
            self.shutdown()
        else:
            self.log(f"{name} connected successfully")
            self.send(conn, "Connected successfully! -w")

        #notifs = self.get_notifications(self, name)
        #printls(notifs)
        #self.sendls(notifs)
            
        self.loop(conn, addr, name)


    def loop(self, conn: socket.socket, addr: str, name: str):
        while True:
            try:
                response = self.recv(conn)
            except KeyboardInterrupt:
                self.log("Keyboard Interrupt, closing server...", conn)
                self.listening = False
                self.disconnect_conn(conn, addr)
                self.shutdown()
                return
            
            print(f"[{name}] {response}")
            
            if ' ' in response:
                argv = response.split(' ')
            else:
                self.send(conn, "OK")
                continue

            match argv[0]:
                case "sell":
                    self.handle_sell_item(conn, name, argv)
                case "get":
                    if argv[1] == "listings":
                        self.handle_get_listings(conn, name, argv)
                    else:
                        pass
                case _:
                    self.log("Unknown command", conn, True)

    
    def handle_sell_item(self, conn: socket.socket, name: str, argv: List[str]):
        try:
            item_name = argv[1]
            smallest_bid = int(argv[2])
        except:
            self.log("Expected: sell <item_name: str> <smallest_bid: int>", conn, True)
            return
    
        self.database.add_item_listing(name, item_name, smallest_bid)
        self.send(conn, "Listing created successfully-w")

    
    def handle_get_listings(self, conn: socket.socket, name: str, argv: List[str]):
        listings = self.database.get_listings()
        self.listings = listings
        message = ""

        for i, el in enumerate(listings):
            product_name = el["product_name"]
            seller = el["seller"]
            smallest_bid = el["smallest_bid"]
            highest_bid = el["highest_bid"]
            msg = ""
            offset = len("{i}.") * ' '
            msg += f"{i}. Item: {product_name}\n"
            msg += f"{offset}Smallest bid: {smallest_bid}\n"
            msg += f"{offset}Highest bid: {highest_bid}"
            message += msg + '\n'
        
        self.send(conn, message)


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
            try:
                self.send(conn, msg + '-w')
            except Exception as e:
                print(conn, "\n", message)

def printls(ls: list):
    for i, el in enumerate(ls):
        print(f"{i}. {el}")



if __name__ == "__main__":
    server = Server()
    server.run()
