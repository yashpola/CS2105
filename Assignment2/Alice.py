import sys
from socket import *
from zlib import crc32


def main():
    serverPort = int(sys.argv[1])
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(("", serverPort))
    while True:
        segment, clientAddress = serverSocket.recvfrom(63)
        expectedChecksum = int.from_bytes(segment[:4], byteorder=sys.byteorder)
        actualChecksum = crc32(segment[4:])
        if expectedChecksum != actualChecksum:
            serverSocket.sendto(b"Packet corrupted", clientAddress)
            continue
        sys.stdout.write(segment[4:].decode())
        sys.stdout.flush()
        serverSocket.sendto(b"Packet ok", clientAddress)


if __name__ == "__main__":
    main()
