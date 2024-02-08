import hashlib
import socket
import getpass
import sys
from colorama import *

class Client:
    ENCODING = "UTF-8"
    BUFFER_SIZE = 4096

    def __init__(self, ip: str = "127.0.0.1", port: int = 8080):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        self.server_addr = (ip, port)

        self.name = None
        init() # From colorama

    
    def connect(self):
        self.socket.connect(self.server_addr)
        print(f"Connected to host {self.server_addr}")

        signup = input("Do you want to sign-up?\n>")
        self.send(signup)

        if 'Y' in signup or 'y' in signup:
            self.handle_sign_up()
        else:
            self.handle_log_in()

        
        try:
            self.run()
        except Exception as e:
            print(f"ERROR: {e}")
            self.shutdown()


    def run(self):
        pass

    
    def handle_sign_up(self):
        print()
        name = input("Name: ")
        password = input("Password: ")
        userdata = name + ' ' + password
        print()

        self.send(userdata)

        response = self.recv()
        self.process_recv(response)

        if "ERROR" in response:
            self.handle_sign_up()
        else:
            self.name = name


    def handle_log_in(self):
        print()
        name = input("Name: ")
        password = input("Password: ")
        userdata = name + ' ' + password
        print()

        self.send(userdata)

        response = self.recv()
        self.process_recv(response)

        if "ERROR" in response:
            self.handle_log_in()
        else:
            self.name = name

        
    def shutdown(self):
        print("Shutting down client.")
        self.socket.close()
        sys.exit(0)


    def send(self, message: str):
        bytes_all = message.encode(self.ENCODING)
        bytes_sent = self.socket.send(bytes_all)

        if bytes_all != bytes_sent:
            return False
        return True
    

    def process_recv(self, response:str):
        if '\n' in response:
            responses = response.split('\n')
            for resp in responses:
                self.process_recv(resp + '-w')
            return
        resp_arr = response.split(' ')
        if 'Bank' in response:
            response = response.replace('Bank', Fore.YELLOW + "Bank" + Fore.RESET)
        if '-RED-' in response:
            response = response.replace('-RED-', Fore.RED)
        if '-GREEN-' in response:
            response = response.replace('-GREEN-', Fore.GREEN)
        if '-BLUE-' in response:
            response = response.replace('-BLUE-', Fore.LIGHTBLUE_EX)
        if '-RESET-' in response:
            response = response.replace('-RESET-', Fore.RESET)
        if '-w' in response:
            response = response.replace('-w', Fore.RESET)
            print(response)


    def recv(self):
        try:
            message = self.socket.recv(self.BUFFER_SIZE).decode(self.ENCODING)
            return message
        except TimeoutError as e:
            print("Timed out.")
            self.send("shutdown")


    def hash(self, message: str):
        obj = hashlib.md5(message.encode('utf-8'))
        return obj.hexdigest()

if __name__ == "__main__":
    client = Client("127.0.0.1", 8080)
    client.connect()


    def run(self):
        while True:
            print()
            data = input(">")
            self.send(data)
            resp = self.recv()
            self.process_recv(resp)

            if "Do you want to add the difference to your debt" in resp:
                self.handle_add_to_debt(self)
            elif "Signup?" in resp:
                self.handle_log_out()
            elif "password: " in resp:
                self.handle_get_password(resp)