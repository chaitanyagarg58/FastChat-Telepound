import socket
import os
from _thread import *

ServerSideSocket = socket.socket()
host = '127.0.0.1'
port = 5000
ThreadCount = 0
try:
    ServerSideSocket.bind((host, port))
except socket.error as e:
    print(str(e))
print('Socket is listening..')
ServerSideSocket.listen(5)

def multi_threaded_client(connection):
    connection.send(str.encode('Server is working:'))
    while True:
        data = connection.recv(2048)
        print(data)
        response = 'Server message: ' + data.decode('utf-8')
        if not data:
            break
        connection.sendall(str.encode(response))
    connection.close()


while True:
    Client, address = ServerSideSocket.accept()
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(multi_threaded_client, (Client, ))
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount))
ServerSideSocket.close()








# import socket
# import sys
# import json

# # Server name and port
# host = 'local host'
# port = int(sys.argv[1])

# #Create a socket at server
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind(('',port))

# # Maximum 100 clients possible
# s.listen(100)

# # Wait for client
# c, addr = s.accept()

# # Display Client address
# print ('CONNECTION FROM:', str(addr))

# # send message to the client after
# # encoding into binary string
# c.send(b"HELLO, How are you? Welcome to Akash hacking World")

# msg = "Bye.........."
# c.send(msg.encode())

# msg = c.recv(1024)
# print (msg)

# c.close()