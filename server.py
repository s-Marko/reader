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
        data = file.readline()
        if not data:
            break
        data = data.rstrip()

        msg = connection.rect(1024).decode(encoding)
        
        

    connection.close()

def start_server(sock):
    print(f'Listening on {server}')
    sock.listen(5)

    while True:
        connection, address = sock.accept()
        thread = threading.Thread(target=client_handler, args=(connection, adress))
        thread.start()
        print(f'connections {threading.activeCount() - 1}')
        


if __name__ == '__main__':   
    print(f'Server starting.') 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))

    start_server(sock)
