import sys
from socket import *
from zlib import crc32


def main():
    serverPort = int(sys.argv[1])
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(("", serverPort))
    while True:
        message, clientAddress = serverSocket.recvfrom(62)
        receivedMessage = message.decode()
        sys.stdout.write(receivedMessage)
        sys.stdout.flush()
        serverSocket.sendto(receivedMessage.encode(), clientAddress)


if __name__ == "__main__":
    main()
