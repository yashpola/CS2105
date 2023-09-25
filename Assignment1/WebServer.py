import sys
import re
from socket import *


def echoServer():
    serverPort = sys.argv[1]
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(("", int(serverPort)))
    return serverSocket


"""Protocol class that encapsulates a message, connectionSocket,
   and insert, update, deletion methods for the key and counter
   stores
"""


class Protocol:
    keyStore = {}
    counterStore = {}

    def __init__(this, message, connectionSocket):
        this.message = message
        this.connectionSocket = connectionSocket
        this.parse(this.message, this.connectionSocket)

    def parse(this, message, connectionSocket):
        this.connectionSocket = connectionSocket
        # isolate method
        methodEnd = 0
        for i in range(8):
            if message[i] == 32:
                methodEnd = i
                break
        method = message[0:methodEnd].decode().upper()
        this.keyOrCounter = (
            "key"
            if message[methodEnd + 2] == 107 or message[methodEnd + 2] == 75
            else "counter"
        )
        # isolate key/keyName
        keyNameStart = methodEnd + 6 if this.keyOrCounter == "key" else methodEnd + 10
        keyNameEnd = 0
        for i in range(keyNameStart, len(message)):
            if message[i] == 32:
                keyNameEnd = i
                break
        this.keyName = message[keyNameStart:keyNameEnd].decode()
        # truncate message to content-length and content body
        this.message = (
            message[keyNameEnd + 1 :] if method == "POST" else message[keyNameEnd + 2 :]
        )

        if method == "POST":
            this.post()
        elif method == "GET":
            this.get()
        else:
            this.delete()

    # get rid of extra headers and isolate relevant info
    def parsePostHeader(this):
        j = 0
        k = 0
        for i in range(len(this.message)):
            if this.message[i] == 45:
                j = i
                break
        for i in range(j + 8, len(this.message)):
            if this.message[i] == 32:
                k = i
                break
        contentLength = this.message[j + 8 : k].decode()
        result = re.search("\D", contentLength)
        if not result is None:
            this.message = this.message[k + 1 :]
            return this.parsePostHeader()
        else:
            contentLength = int(contentLength)
            z = 0
            for i in range(k, len(this.message) - 1):
                if this.message[i] + this.message[i + 1] == 64:
                    z = i
                    break
            content = this.message[z + 2 :]
            excess = content[contentLength:]
            content = content[0:contentLength]
            this.message = this.message[z + 2 :]
            contentExcess = []
            contentExcess.insert(0, contentLength)
            contentExcess.insert(1, content)
            contentExcess.insert(2, excess)
            return contentExcess

    def post(this):
        contentExcess = this.parsePostHeader()
        contentLength = contentExcess[0]
        content = contentExcess[1]
        excess = contentExcess[2]

        batchedRequest = False
        # if there is excess content, flip flag for batchedRequest
        if len(excess) != 0:
            batchedRequest = True
        if this.keyOrCounter == "key":
            # 405 if positive counter
            if (this.keyName in Protocol.counterStore) and Protocol.counterStore[
                this.keyName
            ][1] > 0:
                this.connectionSocket.send(b"405 MethodNotAllowed  ")
            else:
                # 200 if not
                Protocol.keyStore[f"{this.keyName}"] = [contentLength, content]
                this.connectionSocket.send(b"200 OK  ")
                # pass the buck for batched request
            if batchedRequest:
                this.parse(excess, this.connectionSocket)
        elif this.keyOrCounter == "counter":
            # 405 if key nonexistent in key-store
            if this.keyName not in Protocol.keyStore:
                this.connectionSocket.send(b"405 MethodNotAllowed  ")
            # increment remaining counter if key is already in counter-store
            elif this.keyName in Protocol.counterStore:
                Protocol.counterStore[this.keyName][1] += int(content)
            # post counter if not already in counter-store
            else:
                Protocol.counterStore[f"{this.keyName}"] = [contentLength, int(content)]
            this.connectionSocket.send(b"200 OK  ")
            # pass the buck for batched request
            if batchedRequest:
                this.parse(excess, this.connectionSocket)

    def get(this):
        if this.keyOrCounter == "key":
            # build response message
            if this.keyName in Protocol.keyStore:
                contentLength = Protocol.keyStore[this.keyName][0]
                content = Protocol.keyStore[this.keyName][1]
                contentResponse = (
                    b"200 OK Content-Length "
                    + str(contentLength).encode()
                    + b"  "
                    + content
                )
                # decrement remaining counter if key in counter-store, and delete it if counter has reached 0
                if (this.keyName in Protocol.counterStore) and Protocol.counterStore[
                    this.keyName
                ][1] > 0:
                    this.connectionSocket.send(contentResponse)
                    Protocol.counterStore[this.keyName][1] -= 1
                    if Protocol.counterStore[this.keyName][1] == 0:
                        Protocol.counterStore.pop(this.keyName)
                        Protocol.keyStore.pop(this.keyName)
                # 200 if key not in counter-store
                else:
                    this.connectionSocket.send(contentResponse)
                # pass the buck if batched request
                if not len(this.message) <= 14:
                    this.parse(this.message, this.connectionSocket)
            # 404 if key not in key-store
            else:
                this.connectionSocket.send(b"404 NotFound  ")
        elif this.keyOrCounter == "counter":
            # build response message
            if (
                this.keyName not in Protocol.counterStore
                and this.keyName not in Protocol.keyStore
            ):
                this.connectionSocket.send(b"404 NotFound  ")
                return
            # 200 + remaining counter if key in counter-store
            if this.keyName in Protocol.counterStore:
                contentLength = str(Protocol.counterStore[this.keyName][0])
                content = str(Protocol.counterStore[this.keyName][1])
                contentResponse = (
                    b"200 OK Content-Length "
                    + contentLength.encode()
                    + b"  "
                    + content.encode()
                )
                this.connectionSocket.send(contentResponse)
            # 200 infinity if key not in counter-store but in key-store
            else:
                contentResponse = b"200 OK Content-Length 8  Infinity"
                this.connectionSocket.send(contentResponse)
        # pass the buck if batched request
        if not len(this.message) <= 14:
            this.parse(this.message, this.connectionSocket)

    def delete(this):
        if this.keyOrCounter == "key":
            # 404 if key not in key-store
            if this.keyName not in Protocol.keyStore:
                this.connectionSocket.send(b"404 NotFound  ")
            # 405 if positive remaining counter in counter-store
            elif (
                this.keyName in Protocol.keyStore
                and this.keyName in Protocol.counterStore
                and Protocol.counterStore[this.keyName][1] > 0
            ):
                this.connectionSocket.send(b"405 MethodNotAllowed  ")
            # 200 if no more remaining counter in counter-store
            else:
                contentLength = str(Protocol.keyStore[this.keyName][0])
                content = Protocol.keyStore[this.keyName][1]
                contentResponse = (
                    b"200 OK Content-Length " + contentLength.encode() + b"  " + content
                )
                Protocol.keyStore.pop(this.keyName)
                this.connectionSocket.send(contentResponse)
            # pass the buck if batched request
            if not len(this.message) <= 14:
                this.parse(this.message, this.connectionSocket)
        elif this.keyOrCounter == "counter":
            # 404 if key not in counter-store
            if this.keyName not in Protocol.counterStore:
                this.connectionSocket.send(b"404 NotFound  ")
            # 200 if key in counter-store
            else:
                contentLength = str(Protocol.counterStore[this.keyName][0])
                content = str(Protocol.counterStore[this.keyName][1])
                contentResponse = (
                    b"200 OK Content-Length "
                    + contentLength.encode()
                    + b"  "
                    + content.encode()
                )
                Protocol.counterStore.pop(this.keyName)
                this.connectionSocket.send(contentResponse)
            # pass the buck if batched request
            if not len(this.message) <= 14:
                this.parse(this.message, this.connectionSocket)


def main():
    serverSocket = echoServer()
    serverSocket.listen()
    while True:
        connectionSocket, clientAddr = serverSocket.accept()
        while True:
            message = connectionSocket.recv(2048)
            if len(message) == 0:
                connectionSocket.close()
                break
            Protocol(message, connectionSocket)


if __name__ == "__main__":
    main()
