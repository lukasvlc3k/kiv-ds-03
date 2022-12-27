from flask import request
from pydantic import BaseModel, Field
from kazoo.client import KazooClient
from flask_openapi3 import OpenAPI, Info
import os
import time
import threading
import requests
import queue
import logging
logging.basicConfig(level=logging.DEBUG)

DEFAULT_PORT = 5000

ZK_ROOT_NAME = 'root'
ZK_CHILD_NAME = 'child'

SLEEP_TIME = 30


class Settings(BaseModel):
    zk_ip: str
    api_port: int
    node_ip: str
    this_is_root: bool


def get_settings() -> Settings:
    ip = os.environ['ZOOKEEPER_IP']
    port = int(os.environ['PORT']
               ) if 'PORT' in os.environ.keys() else DEFAULT_PORT
    node_ip = os.environ['NODE_IP']
    is_root = os.environ['IS_ROOT'].lower() == "true"

    return Settings(zk_ip=ip, api_port=port, node_ip=node_ip, this_is_root=is_root)


settings = get_settings()
storage = {}
this_node_path = None


# ================ utils ================


def log(message: str):
    f = open('log.txt', 'a', encoding='utf-8')
    print(f'[{settings.node_ip}:{settings.api_port}] {message}',
          file=f, flush=True)

    print(message)

# ================ zookeeper ================


def zk_init():
    zk = KazooClient(hosts=f'{settings.zk_ip}:2181')
    zk.start()
    register_in_hierarchy(zk)

    log("ZK init done")
    return zk


def wait_for_root_node(zk: KazooClient):
    while True:
        if zk.exists(path=ZK_ROOT_NAME) is None:
            time.sleep(SLEEP_TIME)
            log("Root node not found, waiting...")
        else:
            log("Root node found")
            break


def register_in_hierarchy(zk: KazooClient):
    global this_node_path

    if settings.this_is_root:
        zk.create(path=ZK_ROOT_NAME, value=f'{settings.node_ip}:{settings.api_port}'.encode(
            'utf-8'), makepath=True)
        this_node_path = ZK_ROOT_NAME
        log('registered as a root node')
    else:
        wait_for_root_node(zk)

        # now it is ensured that the root node is online. We can find a place to register this new node
        # we can find a node that has less then 2 children (as we want a binary tree to be built), using BFS algorithm
        # (other algorithm could be used, but BFS is easy to implement and does its job well here)

        q = queue.Queue()
        q.put(ZK_ROOT_NAME)
        while not q.empty():
            node = q.get()

            children = zk.get_children(node)

            if len(children) < 2:
                # there is a space, we can insert the node as a child
                this_node_path = zk.create(path=f'{node}/{ZK_CHILD_NAME}', value=f'{settings.node_ip}:{settings.api_port}'.encode('utf-8'),
                                           makepath=True, sequence=True)
                log(f'node registered {this_node_path}')
                break
            else:
                # go deeper
                for child in children:
                    q.put(f'{node}/{child}')


def get_parent_endpoint(zk: KazooClient, key: str) -> str:
    parent_path = this_node_path.rsplit("/", 1)[0]
    ip = zk.get(path=parent_path)[0]
    if key is None:
        address = f'http://{ip.decode("utf-8")}'
    else:
        address = f'http://{ip.decode("utf-8")}/key/{key}'

    return address


# ================ API ================

app = OpenAPI(__name__, info=Info(title='DS-03', version='0.1.0'))


def send_http_req(method: str, body, url: str) -> dict:
    method = method.lower()
    if method == 'delete':
        response = requests.delete(url, data=body)
    elif method == 'get':
        response = requests.get(url, data=body)
    else:
        response = requests.put(url, data=body)

    return response.json()


def send_http_req_async(method: str, body, url: str) -> None:
    # there is no easy way for asyncrhonous requests using library Requests. This is
    # quite easy workaround that ensures that request will be processed in other thread -> will not block current thread
    thr = threading.Thread(target=send_http_req, args=[method, body, url])
    thr.start()


class PutBody(BaseModel):
    value: str

    def to_dict(self):
        return {"value": self.value}


class GetResponse(BaseModel):
    key: str
    value: str
    code: int


class BasicResponse(BaseModel):
    code: int


class KeyPath(BaseModel):
    key: str = Field(..., description='key')


@app.get('/key/<string:key>', responses={"200": GetResponse, "404": BasicResponse})
def get_request(path: KeyPath):
    global zk
    key = path.key

    if key in storage.keys():
        # key is in a local key-value storage -> simple return the value
        log(f'GET {key} found in a local storage, returning (200)')
        return GetResponse(key=key, value=storage[key], code=200).json(), 200
    else:
        if settings.this_is_root:
            log(f'GET {key} - not found locally and this is root -> returning 404 NOT FOUND')
            # if we don't and we are root, just send 404
            return BasicResponse(code=404).json(), 404
        else:
            # not found locally and not root, so delegate to higher layer
            log(f'GET {key}, delegating to {get_parent_endpoint(zk, key)}')
            response = send_http_req(
                'get', None, get_parent_endpoint(zk, key))
            if response['code'] == 404:
                log(
                    f'GET {key} - not found in parent -> returning 404')
                return BasicResponse(code=404).json(), 404
            else:
                log(
                    f'GET {key} - found in parent, saving to local cache, returning 200')
                storage[response['key']] = response['value']
                return GetResponse(key=response['key'], value=response['value'], code=200).json(), 200


@app.put('/key/<string:key>', responses={"200": BasicResponse, "201": BasicResponse})
def put_key(path: KeyPath, body: PutBody):
    global zk
    key = path.key

    value = body.value

    was_before = key in storage.keys()
    storage[key] = value

    if was_before:
        log(f'PUT {key}, updated existing value, returning 200')
        code = 200
    else:
        log(f'PUT {key}, created a new result, 201')
        code = 201

    # propagate the change to upper layers
    if not settings.this_is_root:
        log(f'Propagating change (key: {key}) to: {get_parent_endpoint(zk, key)}')
        send_http_req_async('put', body.to_dict(),
                            get_parent_endpoint(zk, key))

    return BasicResponse(code=code).json(), code


@app.delete('/key/<string:key>', responses={"200": BasicResponse})
def delete_key(path: KeyPath):
    global zk
    key = path.key

    if key not in storage.keys():
        log(f'DELETE {key} - not found locally')
        code = 201
    else:
        storage.pop(key)
        log(f'DELETE {key} - found locally, deleted')
        code = 200

    # propagate the change to upper layers
    if not settings.this_is_root:
        log(f'Propagating deletion of key: {key} to: {get_parent_endpoint(zk, key)}')
        send_http_req_async('delete', None, get_parent_endpoint(zk, key))

    return BasicResponse(code=code).json(), code


# ================ main (running the app) ================


def main():
    global zk
    print("Starting...")
    zk = zk_init()
    app.run(host='0.0.0.0', port=settings.api_port)


if __name__ == "__main__":
    main()
