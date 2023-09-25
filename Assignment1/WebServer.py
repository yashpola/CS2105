import sys
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
        print(f"The given message is {message}")
        methodEnd = 0
        for i in range(8):
            if message[i] == 32:
                methodEnd = i
                break
        method = message[0:methodEnd].decode().upper()
        print(f"Method: {method}")
        this.keyOrCounter = (
            "key"
            if message[methodEnd + 2] == 107 or message[methodEnd + 2] == 75
            else "counter"
        )
        print(f"keyOrCounter: {this.keyOrCounter}")
        keyNameStart = methodEnd + 6 if this.keyOrCounter == "key" else methodEnd + 10
        keyNameEnd = 0
        for i in range(keyNameStart, len(message)):
            if message[i] == 32:
                keyNameEnd = i
                break
        this.keyName = message[keyNameStart:keyNameEnd].decode()
        print(f"keyName: {this.keyName}")
        this.message = (
            message[keyNameEnd + 1 :] if method == "POST" else message[keyNameEnd + 2 :]
        )
        print(f"The message right now is: {this.message}")

        if method == "POST":
            this.post()
        elif method == "GET":
            this.get()
        else:
            this.delete()

    def post(this):
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
        contentLength = int(this.message[j + 8 : k].decode())
        z = 0
        for i in range(k, len(this.message) - 1):
            if this.message[i] + this.message[i + 1] == 64:
                z = i
                break
        content = this.message[z + 2 :]
        excess = content[contentLength:]
        content = content[0:contentLength]
        print(
            f"Content: {content} of length {len(content)}, Excess: {excess} of {len(excess)}"
        )
        batchedRequest = False
        if len(excess) != 0:
            batchedRequest = True
        if this.keyOrCounter == "key":
            if (this.keyName in Protocol.counterStore) and Protocol.counterStore[
                this.keyName
            ][1] > 0:
                print("sending 405")
                this.connectionSocket.send(b"405 MethodNotAllowed  ")
            else:
                Protocol.keyStore[f"{this.keyName}"] = [contentLength, content]
                print("sending 200")
                print(
                    f"Counter Store: {Protocol.counterStore}, Key Store: {Protocol.keyStore}"
                )
                this.connectionSocket.send(b"200 OK  ")
            if batchedRequest:
                print(f"Carrying on excess of: {excess}")
                this.parse(excess, this.connectionSocket)
        elif this.keyOrCounter == "counter":
            if this.keyName not in Protocol.keyStore:
                print("sending 405")
                this.connectionSocket.send(b"405 MethodNotAllowed  ")
            elif this.keyName in Protocol.counterStore:
                Protocol.counterStore[this.keyName][1] += int(content)
            else:
                Protocol.counterStore[f"{this.keyName}"] = [contentLength, int(content)]
                print(
                    f"Counter Store: {Protocol.counterStore}, Key Store: {Protocol.keyStore}"
                )
            print("sending 200")
            this.connectionSocket.send(b"200 OK  ")
            if batchedRequest:
                print(f"Carrying on excess of: {excess}")
                this.parse(excess, this.connectionSocket)
        print(f"Counter Store: {Protocol.counterStore}, Key Store: {Protocol.keyStore}")

    def get(this):
        print(f"Fetching: {this.keyOrCounter}, {this.keyName}")
        if this.keyOrCounter == "key":
            if this.keyName in Protocol.keyStore:
                contentLength = Protocol.keyStore[this.keyName][0]
                content = Protocol.keyStore[this.keyName][1]
                contentResponse = (
                    b"200 OK Content-Length "
                    + str(contentLength).encode()
                    + b"  "
                    + content
                )
                if (this.keyName in Protocol.counterStore) and Protocol.counterStore[
                    this.keyName
                ][1] > 0:
                    print("sending 200")
                    this.connectionSocket.send(contentResponse)
                    Protocol.counterStore[this.keyName][1] -= 1
                    if Protocol.counterStore[this.keyName][1] == 0:
                        Protocol.counterStore.pop(this.keyName)
                        Protocol.keyStore.pop(this.keyName)
                    print(
                        f"Counter Store: {Protocol.counterStore}, Key Store: {Protocol.keyStore}"
                    )
                else:
                    print("sending 200")
                    this.connectionSocket.send(contentResponse)
                if not len(this.message) <= 14:
                    print(f"Carrying on excess of: {this.message}")
                    this.parse(this.message, this.connectionSocket)
            else:
                print("sending 404")
                this.connectionSocket.send(b"404 NotFound  ")
        elif this.keyOrCounter == "counter":
            if (
                this.keyName not in Protocol.counterStore
                and this.keyName not in Protocol.keyStore
            ):
                print("sending 404")
                this.connectionSocket.send(b"404 NotFound  ")
                return
            if this.keyName in Protocol.counterStore:
                contentLength = str(Protocol.counterStore[this.keyName][0])
                content = str(Protocol.counterStore[this.keyName][1])
                contentResponse = (
                    b"200 OK Content-Length "
                    + contentLength.encode()
                    + b"  "
                    + content.encode()
                )
                print("sending 200")
                this.connectionSocket.send(contentResponse)
            else:
                contentResponse = b"200 OK Content-Length 8  Infinity"
                print("sending 200")
                this.connectionSocket.send(contentResponse)
        if not len(this.message) <= 14:
            print(f"Carrying on excess of: {this.message}")
            this.parse(this.message, this.connectionSocket)
        print(f"Counter Store: {Protocol.counterStore}, Key Store: {Protocol.keyStore}")

    def delete(this):
        print(f"Deleting: {this.keyOrCounter}, {this.keyName}")
        if this.keyOrCounter == "key":
            if this.keyName not in Protocol.keyStore:
                print("sending 404")
                this.connectionSocket.send(b"404 NotFound  ")
            elif (
                this.keyName in Protocol.keyStore
                and this.keyName in Protocol.counterStore
                and Protocol.counterStore[this.keyName][1] > 0
            ):
                print("sending 405")
                this.connectionSocket.send(b"405 MethodNotAllowed  ")
            else:
                contentLength = str(Protocol.keyStore[this.keyName][0])
                content = Protocol.keyStore[this.keyName][1]
                contentResponse = (
                    b"200 OK Content-Length " + contentLength.encode() + b"  " + content
                )
                print("sending 200")
                Protocol.keyStore.pop(this.keyName)
                print(
                    f"Counter Store: {Protocol.counterStore}, Key Store: {Protocol.keyStore}"
                )
                this.connectionSocket.send(contentResponse)
            if not len(this.message) <= 14:
                print(f"Carrying on excess of: {this.message}")
                this.parse(this.message, this.connectionSocket)
        elif this.keyOrCounter == "counter":
            if this.keyName not in Protocol.counterStore:
                this.connectionSocket.send(b"404 NotFound  ")
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
                print(
                    f"Counter Store: {Protocol.counterStore}, Key Store: {Protocol.keyStore}"
                )
                print("sending 200")
                this.connectionSocket.send(contentResponse)
            if not len(this.message) <= 14:
                print(f"Carrying on excess of: {this.message}")
                this.parse(this.message, this.connectionSocket)
        print(f"Counter Store: {Protocol.counterStore}, Key Store: {Protocol.keyStore}")


def main():
    serverSocket = echoServer()
    serverSocket.listen()
    while True:
        connectionSocket, clientAddr = serverSocket.accept()
        while True:
            message = connectionSocket.recv(2048)
            print(f"Message Received Length: {len(message)}")
            if len(message) == 0:
                connectionSocket.close()
                break
            Protocol(message, connectionSocket)


if __name__ == "__main__":
    main()
