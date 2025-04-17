import socket
import os
from picamera2.encoders import H264Encoder, Quality
from picamera2 import Picamera2
from picamera2.outputs import FfmpegOutput
import time


out_name = "test_rpi2.mp4"
# Set up the server (Raspberry Pi)
camera = Picamera2()
#camera.configure(camera.create_still_configuration(main={"size": (3840, 2160)}))
camera.configure(camera.create_video_configuration(main={"size": (1920, 1080)}))
encoder = H264Encoder()

camera.start()
time.sleep(3)

server_ip = '0.0.0.0'  # Accept connections from any IP address
server_port = 12345     # Port to listen on

#while True:
# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind the socket to the server's IP and port
server_socket.bind((server_ip, server_port))

# Start listening for incoming connections
server_socket.listen(1)
print(f"Server listening on {server_ip}:{server_port}...")

# Accept a connection from the client
try:
	client_socket, client_address = server_socket.accept()
	print(f"Connection established with {client_address}")
	#while True:
	# Receive a message from the client
	message = client_socket.recv(1024).decode('utf-8')
	print(f"Received message from client: {message}")
	#camera.capture_file('test.jpg')
	video_out = FfmpegOutput(out_name)
	camera.start_recording(encoder, video_out, quality=Quality.HIGH)
	time.sleep(int(message))
	camera.stop_recording()

	with open(out_name, 'rb') as f:
	    print("Sending the file...")
	    while chunk := f.read(1024):  # Read file in chunks of 1024 bytes
	        client_socket.send(chunk)  # Send the chunk to the client


## Send a response back to the client
#response = f"{client_address} Finished Capture"
#client_socket.send(response.encode('utf-8'))

except Exception as e:
	print(f"An error occurred: {e}")

finally:
	# Close the connection
	camera.stop()
	client_socket.close()
	server_socket.close()
	try:
	    os.remove(out_name)
	    print(f"File {out_name} deleted successfully!")
	except Exception as e:
	    print(f"Error deleting file {out_name}: {e}")
	time.sleep(2)
