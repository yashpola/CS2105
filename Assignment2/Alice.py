import sys
from socket import *
from zlib import crc32


def main():
    serverName = ""
    serverPort = sys.argv[1]
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    clientSocket.settimeout(0.05)
    lastSequenceNumber = 0
    while True:
        message = sys.stdin.read(59)
        if len(message) == 0:
            clientSocket.close()
            break
        thisSequenceNumber = lastSequenceNumber.to_bytes(1, byteorder=sys.byteorder)
        data = thisSequenceNumber + message.encode()
        checksum = crc32(data).to_bytes(4, byteorder=sys.byteorder)
        segment = checksum + data
        modifiedMessage = b""
        while True:
            try:
                clientSocket.sendto(segment, (serverName, int(serverPort)))
                modifiedMessage, serverAddress = clientSocket.recvfrom(64)
                while (
                    modifiedMessage.decode()
                    != "Packet " + str(lastSequenceNumber) + " received ok"
                ):
                    clientSocket.sendto(segment, (serverName, int(serverPort)))
                    modifiedMessage, serverAddress = clientSocket.recvfrom(64)
                lastSequenceNumber += 1
                break
            except TimeoutError:
                continue


if __name__ == "__main__":
    main()
