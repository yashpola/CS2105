import sys
from zlib import crc32


def main():
    with open(sys.argv[1], "rb") as file:
        bytes = file.read()
    checksum = crc32(bytes)
    print(checksum)


if __name__ == "__main__":
    main()
