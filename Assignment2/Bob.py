import sys
from socket import *
from zlib import crc32


def main():
    serverName = ""
    serverPort = sys.argv[1]
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    fullMessage = ""
    while True:
        message = sys.stdin.read(59)
        if len(message) == 0:
            clientSocket.close()
            break
        checksum = crc32(message.encode())
        segment = checksum.to_bytes(4, byteorder=sys.byteorder) + message.encode()
        clientSocket.sendto(segment, (serverName, int(serverPort)))
        modifiedMessage, serverAddress = clientSocket.recvfrom(64)
        while modifiedMessage.decode() != "Packet ok":
            clientSocket.sendto(segment, (serverName, int(serverPort)))
            modifiedMessage, serverAddress = clientSocket.recvfrom(64)


if __name__ == "__main__":
    main()
