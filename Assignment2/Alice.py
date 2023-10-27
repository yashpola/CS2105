import sys
from socket import *
from zlib import crc32


def main():
    serverName = ""
    serverPort = sys.argv[1]
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    while True:
        message = sys.stdin.read(62)
        if len(message) == 0:
            clientSocket.close()
            break
        clientSocket.sendto(message.encode(), (serverName, int(serverPort)))
        modifiedMessage, serverAddress = clientSocket.recvfrom(62)


if __name__ == "__main__":
    main()
