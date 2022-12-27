from argparse import ArgumentParser
from generated import Client
from generated.api.default.get_key_key import sync as get_key_sync
from generated.api.default.put_key_key import sync as put_key_sync
from generated.api.default.delete_key_key import sync as delete_key_sync

from pydantic import BaseModel
class PutBody(BaseModel):
    value: str

    def to_dict(self):
        return {"value": self.value}

def get_key(spl: list):
    if len(spl) != 2:
        print(
            "Invalid parameters - GET command requires a key. Enter for example: GET test")
        return

    response = get_key_sync(client=api_client, key=spl[1])
    if response is None:
        print("response is none")
        return
        
    if response.code == 200:
        print(f'key: {response.key}\t -> \t value: {response.value}')
    elif response.code == 404:
        print(f'key {spl[1]} not found')
    else:
        print(f'err: {response.code}')


def put_key(spl: list):
    if len(spl) != 3:
        print("Invalid parameters - PUT command requires a key and a value. For example: PUT test ahoj")
        return

    
    response = put_key_sync(client=api_client, json_body=PutBody(value=spl[2]), key=spl[1])
    if response is None:
        print("response is none")
        return

    if response.code == 201:
        print(f'key {spl[1]} created, set to: {spl[2]}')
    elif response.code == 201:
        print(f'key {spl[1]} found, overwritten to {spl[2]}')
    else:
        print(f'err: {response.code}')


def delete_key(spl: list):
    if len(spl) != 2:
        print(
            "Invalid parameters - DELETE command requires a key. For example: DELETE test")
        return

    response = delete_key_sync(client=api_client, key=spl[1])
    if response is None:
        print("response is none")
        return

    if response.code == 200:
        print(f'key: {spl[1]} successfully deleted')
    elif response.code == 201:
        print(f'key {spl[1]} not found locally')
    else:
        print(f'err: {response.code}')


def print_help():
    print("GET <key> (for example GET test)")
    print("PUT <key> <value> (for example PUT test ahoj)")
    print("DELETE <key> (for example DELETE test)")
    print("\n")


def main():
    while True:
        print('Zadejte příkaz (včetně parametrů, zadejte Help pro nápovědu): ')
        inp = input()
        split = inp.split()

        command = split[0].lower()

        if command == "help":
            print_help()
        elif command == "get":
            get_key(split)
        elif command == "put":
            put_key(split)
        elif command == "delete":
            delete_key(split)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--endpoint', required=True, type=str)

    config = vars(parser.parse_args())
    api_client = Client(
        base_url=config['endpoint'], timeout=5, verify_ssl=False)

    main()
