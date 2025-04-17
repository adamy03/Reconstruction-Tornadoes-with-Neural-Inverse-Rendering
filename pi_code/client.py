import socket
import sys

# def get_raspberry_pi_ip():
    
num_pis = 9
num_seconds = int(sys.argv[1])
print(f"Recording for {num_seconds} seconds...")
# Set up the client (PC)

# server_ip = ip_address
server_port = 12345                 # Same port as the server
client_sockets = [None] * num_pis
pi_ids = [1, 2, 3, 6, 7, 8, 9]

for i in pi_ids:
    hostname = f"rpitest{i}.local"
    while True:
        try:
            # Get the IP address of the Raspberry Pi
            ip_address = socket.gethostbyname(hostname)
            print(f"Raspberry Pi{i} IP address: {ip_address}")

            # Create a socket object
            client_sockets[i-1] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Connect to the server
            client_sockets[i-1].connect((ip_address, server_port))
            break

        except socket.gaierror:
            print(f"Could not resolve Raspberry Pi hostname{i} for {hostname}")


# Send a message to the server
message = str(num_seconds)

for j in pi_ids:
    print(f"CMessage sent to rpi{j}")
    client_sockets[j-1].send(message.encode('utf-8'))

for k in pi_ids:
    # Receive a response from the server
    print(client_sockets[k-1])
    with open(f"test_rpi{k}.mp4", 'wb') as f:
        print("Receiving the file...")
        try:
            while True:
                data = client_sockets[k-1].recv(1024)  # Receive data in chunks of 1024 bytes
                if not data:
                    break  # If no data is received, the transfer is complete
                f.write(data)  # Write the received data to the file
        except:
            print("Error receiving data pi '{k}' from the server.")
            break

    # response = client_sockets[k].recv(1024).decode('utf-8')
    print(f"Received response from rpi{k}")
    
    # Close the connection
    client_sockets[k-1].close()

