import sys
from socket import *
from zlib import crc32


def main():
    serverPort = int(sys.argv[1])
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(("", serverPort))
    lastReceivedSequenceNumber = -1
    while True:
        segment, clientAddress = serverSocket.recvfrom(64)
        expectedChecksum = int.from_bytes(segment[:4], byteorder=sys.byteorder)
        actualChecksum = crc32(segment[4:])
        if expectedChecksum != actualChecksum:
            serverSocket.sendto(b"Packet corrupted", clientAddress)
            continue
        sequenceNumber = int.from_bytes(segment[4:5], byteorder=sys.byteorder)
        if sequenceNumber != lastReceivedSequenceNumber + 1:
            if sequenceNumber < lastReceivedSequenceNumber + 1:
                responseMessage = "Packet " + str(sequenceNumber) + " received ok"
                serverSocket.sendto(responseMessage.encode(), clientAddress)
            else:
                responseMessage = (
                    "Expected Packet "
                    + str(lastReceivedSequenceNumber + 1)
                    + ". Got Packet "
                    + str(sequenceNumber)
                )
                serverSocket.sendto(responseMessage.encode(), clientAddress)
            continue
        lastReceivedSequenceNumber += 1
        sys.stdout.write(segment[5:].decode())
        sys.stdout.flush()
        responseMessage = "Packet " + str(sequenceNumber) + " received ok"
        serverSocket.sendto(responseMessage.encode(), clientAddress)


if __name__ == "__main__":
    main()
