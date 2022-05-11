import socket
import signal
import os
import sys

encoding='utf-8'
server = socket.gethostbyname(socket.gethostname())
server = 'localhost'
port = 9999

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
		self.method = method
		self.header = {}

		for line in data:
			line = line.rstrip()
			if ':' in line:
				name, value = line.split(':')
				self.header[name] = value
			if not line:
				break


def getBounds(header):
	try:
		lower = int(header['From'])
	except KeyError:
		lower = 0

	try:
		upper = int(header['To'])
	except KeyError:
		upper = None

	return lower, upper


class Server():
	def __init__(self):
		self.methods = {
			'LS': self.LS,
			'LENGTH': self.LENGTH,
			'READ': self.READ,
			'SEARCH': self.SEARCH,
			'SELECT': self.SELECT
		}

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		self.start_server()

	# request methods
	def LS(self, request):
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
			lower, upper = getBounds(request.header)

			if lower < 0 or upper is not None and lower > upper:
				raise IndexError

			file = request.header['File']
			if '\\.' in file:
				raise IllegalCharacterError

			with open(f'data/{file}') as f:
				file_len = sum(1 for line in f)
				if lower is not None and file_len < upper:
					raise OutOfBoundsError

				f.seek(0)
				for i, line in enumerate(f):
					if upper is None:
						if i >= lower:
							data.append(line.rstrip())
					else:
						if i >= lower and i < upper:
							data.append(line.rstrip())
			return (OK, data)

		except FileNotFoundError:
			return (NO_FILE, [])

		except OutOfBoundsError:
			return (OUT_OF_BOUNDS, [])

		except (IndexError, IllegalCharacterError, KeyError, ValueError, TypeError):
			return (BAD_REQUEST, [])

		except OSError:
			return (READ_ERR, [])

	def __keyword_search(self, keyword, path = ''):
		if not keyword.startswith('\"') or not keyword.endswith('\"'):
			raise IllegalCharacterError

		result = {}
		keyword = keyword.replace('\"', '')
		if not path:
			files = [f for f in os.listdir('data') if f.endswith('.txt')]
		else:
			files = [path]
		for file in files:
			try:
				result[file] = []
				with open(f'data/{file}') as f:
					for line in f:
						if keyword in line:
							result[file].append(line.rstrip())
			except (FileNotFoundError, OSError) as e:
				# skarede
				if path:
					raise e
		return result

	def SEARCH(self, request):
		try:
			result = self.__keyword_search(request.header['String'])
		except (KeyError, IllegalCharacterError):
			return (BAD_REQUEST, [])

		data = []
		for key, value in result.items():
			print(key, value)
			if value:
				data.append(key)
		return (OK, data)

	def SELECT(self, request):
		try:
			result = self.__keyword_search(request.header['String'], request.header['File'])
		except (KeyError, IllegalCharacterError):
			return (BAD_REQUEST, [])
		except FileNotFoundError:
			return (NO_FILE , [])
		except OSError:
			return (READ_ERR, [])

		data = []
		for key, value in result.items():
			if value:
				data.extend(value)
		return (OK, data)

	def request_handler(self, request):
		self.methods[request.method](request)
		try:
			# toto by ma vobec nenapadlo spravit
			# asi mam este traumu z C-ckovych function pointerov :)
			return self.methods[request.method](request)
		except:
			return (UNKNOWN_METHOD, [])

	def construct_response(self, stat, payload):
		length = len(payload)
		if payload:
			payload = '\n'.join(payload)
			return f'{status[stat]}\nLines:{length}\n\n{payload}\n'
		else:
			return f'{status[stat]}\n\n'


	def client_handler(self, connection, address):
		print(f'[New connection] {address}')
		while True:
			client_file = connection.makefile(mode = 'rw')
			method = client_file.readline().rstrip()

			if method:
				# new request received
				request = Request(method, client_file)
				print(f'[New request] {request.method} from {address}')

				status, content = self.request_handler(request)
				response_data = self.construct_response(status, content)

				# sending response to client
				client_file.write(response_data)
				client_file.flush()

				# sever connection on unknown method
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
