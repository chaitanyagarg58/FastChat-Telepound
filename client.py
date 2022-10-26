import socket
ClientMultiSocket = socket.socket()
host = '127.0.0.1'
port = 5000
print('Waiting for connection response')
try:
    ClientMultiSocket.connect((host, port))
except socket.error as e:
    print(str(e))
res = ClientMultiSocket.recv(1024)
while True:
    Input = input('Hey there: ')
    ClientMultiSocket.send(str.encode(Input))
    res = ClientMultiSocket.recv(1024)
    print(res.decode('utf-8'))
ClientMultiSocket.close()



# import socket
# import sys
# import json

# # take the server name and port name

# host = 'local host'
# port = int(sys.argv[1])

# # create a socket at client side
# # using TCP / IP protocol
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# # connect it to server and port
# # number on local computer.
# s.connect(('127.0.0.1', port))

# # receive message string from
# # server, at a time 1024 B
# msg = s.recv(1024)

# # repeat as long as message
# # string are not empty
# while msg:
#     print('Received:' + msg.decode())
#     msg = s.recv(1024)
#     s.sendall("Hi! Happy to Connect".encode())

# # disconnect the client
# s.close()
