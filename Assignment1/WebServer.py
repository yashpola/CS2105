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
    # class fields: key-value and counter store
    keyStore = {}
    counterStore = {}

    def __init__(this, message, connectionSocket):
        this.message = message
        this.connectionSocket = connectionSocket
        this.parse(this.message, this.connectionSocket)

    def parse(this, message, connectionSocket):
        this.connectionSocket = connectionSocket
        this.message = message
        # POST /key/key content-length 7  abcdefg
        this.parsedMessage = this.message.split(" ")
        print(f"The given message is {this.message}")
        print(f"The parsed message is {this.parsedMessage}")
        method = this.parsedMessage[0].upper()
        path = this.parsedMessage[1]
        pathParts = path.split("/")
        this.keyOrCounter = pathParts[1].lower()
        this.keyName = pathParts[2]
        this.newParsedMessage = this.parsedMessage[2:]
        print(this.newParsedMessage)

        if method == "POST":
            this.post()
        elif method == "GET":
            this.get()
        else:
            this.delete()

    def post(this):
        j = 0
        for i in range(len(this.newParsedMessage)):
            if this.newParsedMessage[i].lower() == "content-length":
                j = i
                break
        this.newParsedMessage = this.newParsedMessage[j:]
        print(this.newParsedMessage)
        # headerIndex = this.parsedMessage.index("content-length")
        # this.parsedMessage = this.parsedMessage[headerIndex:]
        # print(this.parsedMessage)
        contentLength = int(this.newParsedMessage[1])
        for i in range(len(this.newParsedMessage)):
            if this.newParsedMessage[i] == "":
                j = i + 1
                break
        this.newParsedMessage = this.newParsedMessage[j:]
        print(this.newParsedMessage)
        # contentLength = int(this.parsedMessage[3])
        # for i in range(2, len(this.parsedMessage)):
        # if this.parsedMessage[i] == "":
        # break
        # else:
        # this.parsedMessage.remove(this.parsedMessage[i])
        # print(this.parsedMessage)
        # content = this.parsedMessage[5]
        content = ""
        for i in range(len(this.newParsedMessage)):
            content += this.newParsedMessage[i] + " "
        print(content)
        excess = content[contentLength:-1]
        content = content[0:contentLength]
        print(content, len(content), excess, len(excess))
        numFiller = 28 if this.keyOrCounter == "key" else 32
        batchedRequest = False
        endIndex = 0
        if excess != "":
            batchedRequest = True
            # endIndex = (
            #    numFiller + len(this.keyName) + len(str(contentLength)) + contentLength
            # )
            # content = content[0:contentLength]
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
                this.parse(excess, this.connectionSocket)
        print(f"Counter Store: {Protocol.counterStore}, Key Store: {Protocol.keyStore}")

    def get(this):
        counter = 0
        for i in range(len(this.message)):
            if this.message[i] == " ":
                counter += 1
        if this.keyOrCounter == "key":
            if this.keyName in Protocol.keyStore:
                contentLength = Protocol.keyStore[this.keyName][0]
                content = Protocol.keyStore[this.keyName][1]
                numFiller = 11
                contentResponse = (
                    "200 OK Content-Length " + str(contentLength) + "  " + content
                )
                if (this.keyName in Protocol.counterStore) and Protocol.counterStore[
                    this.keyName
                ][1] > 0:
                    print("sending 200")
                    this.connectionSocket.send(contentResponse.encode())
                    Protocol.counterStore[this.keyName][1] -= 1
                    if Protocol.counterStore[this.keyName][1] == 0:
                        Protocol.counterStore.pop(this.keyName)
                        Protocol.keyStore.pop(this.keyName)
                    print(
                        f"Counter Store: {Protocol.counterStore}, Key Store: {Protocol.keyStore}"
                    )
                else:
                    print("sending 200")
                    this.connectionSocket.send(contentResponse.encode())
                if this.message[-1] != " " or counter > 3:
                    endIndex = numFiller + len(this.keyName)
                    this.parse(this.message[endIndex:], this.connectionSocket)
            else:
                print("sending 404")
                this.connectionSocket.send(b"404 NotFound  ")
        elif this.keyOrCounter == "counter":
            numFiller = 15
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
                    "200 OK Content-Length " + contentLength + "  " + content
                )
                print("sending 200")
                this.connectionSocket.send(contentResponse.encode())
            else:
                contentResponse = "200 OK Content-Length 8  Infinity"
                print("sending 200")
                this.connectionSocket.send(contentResponse.encode())
        if this.message[-1] != " " or counter > 3:
            endIndex = numFiller + len(this.keyName)
            print("im recursing")
            this.parse(this.message[endIndex:], this.connectionSocket)
        print(f"Counter Store: {Protocol.counterStore}, Key Store: {Protocol.keyStore}")

    def delete(this):
        counter = 0
        for i in range(len(this.message)):
            if this.message[i] == " ":
                counter += 1
        if this.keyOrCounter == "key":
            numFiller = 14 + len(this.keyName)
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
                    "200 OK Content-Length " + contentLength + "  " + content
                )
                print("sending 200")
                Protocol.keyStore.pop(this.keyName)
                print(
                    f"Counter Store: {Protocol.counterStore}, Key Store: {Protocol.keyStore}"
                )
                this.connectionSocket.send(contentResponse.encode())
            if this.message[-1] != " " or counter > 3:
                endIndex = numFiller
                this.parse(this.message[endIndex:], this.connectionSocket)
        elif this.keyOrCounter == "counter":
            numFiller = 18 + len(this.keyName)
            if this.keyName not in Protocol.counterStore:
                this.connectionSocket.send(b"404 NotFound  ")
            else:
                contentLength = str(Protocol.counterStore[this.keyName][0])
                content = str(Protocol.counterStore[this.keyName][1])
                contentResponse = (
                    "200 OK Content-Length " + contentLength + "  " + content
                )
                Protocol.counterStore.pop(this.keyName)
                print(
                    f"Counter Store: {Protocol.counterStore}, Key Store: {Protocol.keyStore}"
                )
                print("sending 200")
                this.connectionSocket.send(contentResponse.encode())
            if this.message[-1] != " " or counter > 3:
                endIndex = numFiller
                this.parse(this.message[endIndex:], this.connectionSocket)
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
            Protocol(message.decode(), connectionSocket)


if __name__ == "__main__":
    main()
