import socket
import sys

# def get_raspberry_pi_ip():
    
num_pis = 9
num_seconds = int(sys.argv[1])
print(f"Recording for {num_seconds} seconds...")
# Set up the client (PC)

# server_ip = ip_address
server_port = 12345                 # Same port as the server
client_sockets = []

for i in range(1,num_pis+1):
    hostname = f"rpitest{i}.local"
    while True:
        try:
            # Get the IP address of the Raspberry Pi
            ip_address = socket.gethostbyname(hostname)
            print(f"Raspberry Pi{i} IP address: {ip_address}")

            # Create a socket object
            client_sockets.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))

            # Connect to the server
            client_sockets[i-1].connect((ip_address, server_port))
            break

        except socket.gaierror:
            print(f"Could not resolve Raspberry Pi hostname{i} for {hostname}")


# Send a message to the server
message = str(num_seconds)

for j in range(num_pis):
    print(f"CMessage sent to rpi{j}")
    client_sockets[j].send(message.encode('utf-8'))

for k in range(num_pis):
    # Receive a response from the server
    with open(f"test_rpi{k+1}.mp4", 'wb') as f:
        print("Receiving the file...")
        while True:
            data = client_sockets[k].recv(1024)  # Receive data in chunks of 1024 bytes
            if not data:
                break  # If no data is received, the transfer is complete
            f.write(data)  # Write the received data to the file


    # response = client_sockets[k].recv(1024).decode('utf-8')
    print(f"Received response from rpi{k+1}")
    
    # Close the connection
    client_sockets[k].close()

