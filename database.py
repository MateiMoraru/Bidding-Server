import hashlib
import pymongo
from typing import List
from bson import json_util
import datetime

class Mongo:
    def __init__(self, addr:str="mongodb://localhost:27017/"):
        try:
            self.client = pymongo.MongoClient(addr)
            self.client.server_info()
        except pymongo.errors.ServerSelectionTimeoutError as err:
            print(err)

        self.users = self.client["Bidding-Server"]["Client"]


    def add_user(self, name:str, password:str):
        data = {
            "name": name, 
            "password": password, 
            "balance": 0,
            "transactions": [],
            "requests": [],
            "notifications": []
            }
        self.users.insert_one(data)


    def add_credit(self, name:str, value:int):
        self.users.find_one_and_update({"name": name}, {"$inc": {"credit": value}})
    

    def request(self, name:str, target:str, value:int, message=None):
        id = self.transaction_id(date(), name, target, value)
        request = {
            "from": name,
            "to": target,
            "value": value,
            "date": date(),
            "hash": id,
            "message": ''
        }
        if message is not None:
            request["message"] = ''.join(message)
        self.users.find_one_and_update({"name": name}, {"$push": {"requests": request}})

    
    def get(self, name:str, field:str):
        try:
            find = self.users.find_one({"name": name})
        except:
            print(f"Unable to find a user called {name}")
        
        if find != None:
            print(find[field])
            return find[field]
        print(None)
        return None


    def get_user_raw(self, name:str):
        find = self.users.find_one({"name": name})
        return find

    
    def get_user(self, name:str):
        find = self.get_user_raw(name)
        return parse_json(find)
    

    def get_balance(self, name:str):
        return self.get(name, "balance")
    

    def get_requests(self, name:str):
        return self.get(name, "requests")
    

    def search_name(self, name:str):
        find = self.users.find_one({"name": name})
        return find != None
    
    
    def search_name_pwd(self, name:str, pwd:str):
        find = self.users.find_one({'name': name, 'password': pwd})
        print(find)
        return find != None
    

    def pay_request(self, name:str, target:str):
        request = None
        value = -1
        for obj in self.get_requests(name):
            if str(obj["to"]) == target:
                request = obj
                value = int(obj["value"])
        if request is not None:
            balance = self.get_balance(name)
            if balance > value:
                self.send_to(name, target, value)
                self.users.find_one_and_update({"name": name}, {"$pull": {"requests": request}})
                return "Finished transfer!"
            return "Insufficient funds!"
        return f"No request found from {target}!"
        

    def add_debt(self, name:str, value:int):
        self.users.find_one_and_update({"name": name}, {"$inc":{"debt": value * 1.01}})


    def add_savings(self, name:str, value:int):
        self.users.find_one_and_update({"name": name}, {"$inc": {"savings": value * 1.01}})


    def add_transaction(self, name:str, target:str, value:int):
        id = self.transaction_id(date(), name, target, value)
        data_sender = {
            "date": date(),
            "to": target,
            "value": value,
            "hash": id
        }
        data_recv = {
            "date": date(),
            "from": name,
            "value": value,
            "hash": id
        }
        self.users.find_one_and_update({"name": name}, {"$push": {"transactions": data_sender}})
        self.users.find_one_and_update({"name": target}, {"$push": {"transactions": data_recv}})

    
    def clear_database(self):
        self.users.delete_many({})

    
    def transaction_id(self, date:str, name:str, target:str, value:str):
        data = f"{date} {name} {target} {value}"
        hash_object = hashlib.md5(data.encode("utf-8"))
        return hash_object.hexdigest()
    

    def change(self, name:str, operation:str, target_field:str, new_value:str):
        obj = self.get(name, target_field)
        if isinstance(obj, int):
            new_value = int(new_value)

        account = self.users.find_one_and_update({"name": name}, {operation: {target_field: new_value}})

def date():
    return datetime.datetime.today().strftime('%Y-%m-%d')


def parse_json(data):
    return json_util.dumps(data)