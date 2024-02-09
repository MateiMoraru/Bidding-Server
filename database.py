import hashlib
import pymongo
from typing import List
from bson import json_util
from datetime import datetime

class Mongo:
    def __init__(self, addr:str="mongodb://localhost:27017/"):
        try:
            self.client = pymongo.MongoClient(addr)
            self.client.server_info()
            log(f"Connected to database successfully")
        except pymongo.errors.ServerSelectionTimeoutError as err:
            print(err)

        self.users = self.client["Bidding-Server"]["Clients"]
        self.listings = self.client["Bidding-Server"]["Listings"]


    def add_user(self, name: str, password: str):
        data = {
            "name": name, 
            "password": password, 
            "balance": 0,
            "transactions": [],
            "requests": [],
            "notifications": []
            }
        self.users.insert_one(data)
        log(f"New user added: \n\t{parse_json(data)}")


    def add_item_listing(self, name: str, item_name: str, smallest_bid: int):
        listing = {
            "seller": name,
            "product_name": item_name,
            "smallest_bid": smallest_bid,
            "highest_bid": smallest_bid,
            "tags": [],
            "status": 0
        }

        self.listings.insert_one(listing)
        log(f"New listing added: \n\t{parse_json(listing)}")
    

    def add_tag(self, item: pymongo.CursorType, tag: str):
        self.listings.find_one_and_update({"seller": item["seller"]}, {"$push": {"tags": tag}})


    def request(self, name: str, target: str, value: int, message: str=None):
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
            log(f"Unable to find user: {name}", True)
        
        if find != None:
            return find[field]
        return None
    

    def get_listings(self):
        listings = []
        for el in self.listings.find({}):
            listings.append(el)

        return listings


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
        log(f"Found user {name} &cursor {find}")
        return find != None
    
    
    def search_name_pwd(self, name:str, pwd:str):
        find = self.users.find_one({'name': name, 'password': pwd})
        log(f"Found user matching password {name} &cursor {find}")
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


def log(message: str, error: bool=False):
    t = datetime.now()
    if not error:
        msg = f"[INFO {t.hour}:{t.minute}:{t.second}] {message}"
    else:
        msg = f"[ERROR]: {message}"
    print(msg)


def parse_json(data):
    return json_util.dumps(data)