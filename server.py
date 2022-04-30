import socket
import signal
import re
import os
import sys

encoding='utf-8'
server = socket.gethostbyname(socket.gethostname())
port = 9000

def client_handler(connection, address):
	print(f'Connection -> {address}')

	file = connection.makefile(mode='rw', encoding=encoding)

	while True:
		pass
		data = file.readline()
		if not data:
			break
		data = data.rstrip()

		msg = connection.rect(1024).decode(encoding)

	connection.close()

def start_server():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	sock.bind(('', port))

	print(f'listening on {server}:{port}')

	sock.listen(5)

	while True:
		print('stuck')
		connection, address = sock.accept()
		pid_chld = os.fork()
		print(pid_chld)
		if pid_chld == 0:
			print(f'I am child {os.getpid()}')
			#sock.close()
			client_handler(connection, address)
			break
		else:
			print(f'I am parent {os.getpid()}')



if __name__ == '__main__':
	print(f'Server starting.')
	#sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	#sock.bind(('', port))

	start_server()
