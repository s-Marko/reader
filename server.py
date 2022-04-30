import socket
import signal
import re
import os
import sys

encoding='utf-8'
server = socket.gethostbyname(socket.gethostname())
port = 9000

OK = 100
BAD_REQUEST = 200
OUT_OF_BOUNDS = 201
NO_FILE = 202
READ_ERR = 203

status = {
	OK: '100 OK',
	BAD_REQUEST: '200 Bad Request',
	OUT_OF_BOUNDS: '201 Bad line number',
	NO_FILE: '202 No such file',
	READ_ERR: '203 Read error'
}

class OutOfBounds(Exception):
	pass


def LS():
	return os.listdir('data')

def LENGTH(file):
	try:
		lines = 0
		with open(f'data/{file}') as f:
			for line in f:
				lines += 1
		return [lines]
	except FileNotFoundError:
		return NO_FILE
	except OSError:
		return READ_ERR

def READ(file, from_, to_):
	try:
		data = []
		if from_ < 0 or to_ is not None and from_ > to_:
			raise OutOfBounds


		with open(f'data/{file}') as f:
			for i, line in enumerate(f):
				if to_ is None:
					if i >= from_:
						data.append(line.rstrip())
				else:
					if i >= from_ and i < to_:
						data.append(line.rstrip())
		return data
	except FileNotFoundError:
		return NO_FILE
	except OutOfBounds:
		return OUT_OF_BOUNDS
	except OSError:
		return READ_ERR

def construct_response(header, data=[]):
	length = len(data)
	if data:
		data = ''.join(f'{d}\n' for d in data)
		return f'{header}\nLINES:{length}\n\n{data}'
	else:
		return f'{header}'

def request_handler(message):
	message = message.decode(encoding)
	cm = message.splitlines()[0]

	file = re.search('File:(\w+.txt)', message).group(1)
	from_ = re.search('From:(-?\d+)', message)
	to_ = re.search('To:(-?\d+)', message)


	if from_ is not None:
		from_ = int(from_.group(1))
	else:
		from_ = 0

	if to_ is not None:
		to_ = int(to_.group(1))


	if cm == 'LS':
		data = LS()
	if cm == 'LENGTH':
		data = LENGTH(file)
	if cm == 'READ':
		data = READ(file, from_, to_)
	else:
		data = BAD_REQUEST

	if type(data) is not list:
		return construct_response(status[data])
	else:
		return construct_response(status[OK], data)

def client_handler(connection, address):
	#print(f'[Connected] {address}')

	while True:
		msg = connection.recv(1024)
		if msg:
			response = request_handler(msg)
			connection.send(response.encode(encoding))

	connection.close()

def start_server():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	sock.bind(('', port))

	sock.listen(5)

	while True:
		connection, address = sock.accept()
		pid_chld = os.fork()
		if pid_chld == 0:
			sock.close()
			client_handler(connection, address)
			break
		else:
			pass



if __name__ == '__main__':
	print(f'Server starting.')
	#sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	#sock.bind(('', port))

	start_server()
