import sys


def main():
    # wrap whole code in while loop to keep parsing the packets as they come in
    header_size = 6
    max_packet_bytes = 1024 * 1024

    while True:
        header = sys.stdin.buffer.read1(header_size)
        # terminate early if no data
        if len(header) == 0:
            break
        # reconstruct payload size as an integer
        total_payload_size = 0
        while True:
            data = sys.stdin.buffer.read1(1).decode()
            # terminating condition
            if data == "B":
                break
            total_payload_size = (total_payload_size * 10) + int(data)
        # write the necessary data based on our payload size
        while total_payload_size > 0:
            # take min of 1MB and remaining payload size to speed up code
            packetData = sys.stdin.buffer.read1(
                min(total_payload_size, max_packet_bytes)
            )
            # write, flush, "remove" packet from remaining payload size
            sys.stdout.buffer.write(packetData)
            sys.stdout.buffer.flush()
            total_payload_size -= len(packetData)


if __name__ == "__main__":
    main()
