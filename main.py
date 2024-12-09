#!/usr/bin/python3
import socket
import struct
import os

# TFTP OpCodes
OPCODES = {
    'RRQ': 1,  # Read Request
    'WRQ': 2,  # Write Request
    'DATA': 3, # Data Packet
    'ACK': 4,  # Acknowledgment
    'ERROR': 5 # Error Packet
}

# Constants
BUFFER_SIZE = 516  # Maximum TFTP packet size
TIMEOUT = 5         # Socket timeout in seconds

def build_request(opcode, filename, mode="octet"):
    """Creates a request packet (RRQ/WRQ)."""
    return struct.pack(f"!H{len(filename) + 1}s{len(mode) + 1}s", opcode, filename.encode(), mode.encode())

def send_ack(sock, block_number, server_address):
    """Sends an ACK packet."""
    ack_packet = struct.pack("!HH", OPCODES['ACK'], block_number)
    sock.sendto(ack_packet, server_address)

def handle_put(sock, filename, server_address):
    """Handles the PUT operation (uploading files to the server)."""
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' does not exist.")
        return

    with open(filename, 'rb') as file:
        block_number = 0
        while True:
            block_number += 1
            data = file.read(512)
            packet = struct.pack("!HH", OPCODES['DATA'], block_number) + data
            sock.sendto(packet, server_address)

            try:
                response, _ = sock.recvfrom(BUFFER_SIZE)
                opcode, ack_block = struct.unpack("!HH", response[:4])

                if opcode != OPCODES['ACK'] or ack_block != block_number:
                    print("Error: Invalid ACK received.")
                    break

            except socket.timeout:
                print("Error: Timeout waiting for ACK.")
                break

            if len(data) < 512:
                print("Upload successful.")
                break

def handle_get(sock, filename, server_address):
    """Handles the GET operation (downloading files from the server)."""
    with open(filename, 'wb') as file:
        block_number = 0
        while True:
            try:
                response, _ = sock.recvfrom(BUFFER_SIZE)
                opcode, received_block = struct.unpack("!HH", response[:4])

                if opcode != OPCODES['DATA'] or received_block != block_number + 1:
                    print("Error: Invalid DATA packet received.")
                    break

                data = response[4:]
                file.write(data)
                block_number = received_block

                send_ack(sock, block_number, server_address)

                if len(data) < 512:
                    print("Download successful.")
                    break

            except socket.timeout:
                print("Error: Timeout waiting for data.")
                break

def main():
    print("=== Simple TFTP Client ===")

    host = input("Enter server IP: ").strip()
    port = input("Enter server port : ").strip()
    port = int(port) if port else 69

    operation = input("Enter operation (get/put): ").strip().lower()
    filename = input("Enter filename: ").strip()

    server_address = (host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)

    try:
        if operation == 'get':
            print(f"Initiating GET request for '{filename}' from {host}:{port}...")
            request_packet = build_request(OPCODES['RRQ'], filename)
            sock.sendto(request_packet, server_address)
            handle_get(sock, filename, server_address)

        elif operation == 'put':
            print(f"Initiating PUT request for '{filename}' to {host}:{port}...")
            request_packet = build_request(OPCODES['WRQ'], filename)
            sock.sendto(request_packet, server_address)
            handle_put(sock, filename, server_address)

        else:
            print("Error: Invalid operation. Use 'get' or 'put'.")

    finally:
        sock.close()

if __name__ == "__main__":
    main()
