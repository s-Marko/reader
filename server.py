import socket
import signal
import re
import os
import sys

encoding='utf-8'
server = socket.gethostbyname(socket.gethostname())
server = 'localhost'
port = 9998

OK = 100
BAD_REQUEST = 200
OUT_OF_BOUNDS = 201
NO_FILE = 202
READ_ERR = 203
UNKNOWN_METHOD = 204

status = {
	OK: '100 OK',
	BAD_REQUEST: '200 Bad Request',
	OUT_OF_BOUNDS: '201 Bad line number',
	NO_FILE: '202 No such file',
	READ_ERR: '203 Read error',
	UNKNOWN_METHOD: '204 Unknown method'
}


class OutOfBoundsError(Exception):
	pass
class IllegalCharacterError(Exception):
	pass


class Request():
	def __init__(self, method, data):
		self.method = ''
		self.header = {}

		self.method = method
		for line in data:
			line = line.rstrip()
			if ':' in line:
				name, value = line.split(':')
				self.header[name] = value
			if not line:
				break


def getBounds(header):
	try:
		from_ = int(header['From'])
	except (ValueError, TypeError):
		return 0
	except KeyError:
		from_ = 0

	try:
		to_ = int(header['To'])
	except (ValueError, TypeError):
		return 0
	except KeyError:
		to_ = None

	return (from_, to_)


class Server():
	def __init__(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		self.start_server()


	# request methods
	def LS(self):
		return (OK, os.listdir('data'))


	def LENGTH(self, request):
		try:
			lines = 0
			file = request.header['File']
			if '\\.' in file:
				raise IllegalCharacterError

			with open(f'data/{file}') as f:
				for line in f:
					lines += 1
			return (OK, [str(lines)])

		except (KeyError, IllegalCharacterError):
			return (BAD_REQUEST, [])

		except FileNotFoundError:
			return (NO_FILE, [])

		except OSError:
			return (READ_ERR, [])


	def READ(self, request):
		try:
			data = []

			bounds = getBounds(request.header)
			if bounds[0] < 0 or bounds[1] is not None and bounds[0] > bounds[1]:
				raise IndexError


			file = request.header['File']
			if '\\.' in file:
				raise IllegalCharacterError

			with open(f'data/{file}') as f:
				file_len = sum(1 for line in f)
				if bounds[1] is not None and file_len < bounds[1]:
					raise OutOfBoundsError

				f.seek(0)
				for i, line in enumerate(f):
					if bounds[1] is None:
						if i >= bounds[0]:
							data.append(line.rstrip())
					else:
						if i >= bounds[0] and i < bounds[1]:
							data.append(line.rstrip())
			return (OK, data)

		except FileNotFoundError:
			return (NO_FILE, [])

		except OutOfBoundsError:
			return (OUT_OF_BOUNDS, [])

		except (IndexError, IllegalCharacterError, KeyError):
			return (BAD_REQUEST, [])

		except OSError:
			return (READ_ERR, [])


	def request_handler(self, request):
		if request.method == 'LS' and not request.header:
			return self.LS()
		elif request.method == 'LENGTH':
			return self.LENGTH(request)
		elif request.method == 'READ':
			return self.READ(request)
		else:
			return (UNKNOWN_METHOD, [])

	def construct_response(self, stat, payload):
		length = len(payload)
		if payload:
			payload = '\n'.join(payload)
			return f'{status[stat]}\nLines:{length}\n\n{payload}\n'
		else:
			return f'{status[stat]}\n'


	def client_handler(self, connection, address):
		print(f'[New connection] {address}')
		while True:
			client_file = connection.makefile(mode = 'rw')
			method = client_file.readline().rstrip()
			if method:
				request = Request(method, client_file)

				print(f'[New request] {request.method} from {address}')

				payload = self.request_handler(request)

				status, content = payload
				response_data = self.construct_response(status, content)

				client_file.write(response_data)
				client_file.flush()

				if status == UNKNOWN_METHOD:
					break

		print(f'[Connection severed] {address}')
		connection.close()


	def start_server(self):
		self.sock.bind((server, port))

		self.sock.listen(5)

		print(f'[Starting] {server}:{port}')
		while True:
			connection, address = self.sock.accept()
			pid_chld = os.fork()
			if pid_chld == 0:
				self.sock.close()
				self.client_handler(connection, address)

				break
			else:
				pass

if __name__ == '__main__':
	Server()
