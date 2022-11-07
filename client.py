import socket
import select
import sys

connectionSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '127.0.0.1'
port = 5003
print('Waiting for connection response')
try:
    connectionSocket.connect((host, port))
except socket.error as e:
    print(str(e))
while True:    
    username = input("Enter Username: ")
    connectionSocket.send(username.encode('utf-8'))
    response = (connectionSocket.recv(1024)).decode('utf-8')
    if response == "Connected":
        print (f'Connection Established! Welcome Back, {username}')
        break
    else:
        print ("Username is invalid, try again!")

sockets = [connectionSocket, sys.stdin]

while True:
    readSocket, x, errorSocket = select.select(sockets,[],sockets)
    
    for inputSocket in readSocket:
        if inputSocket == connectionSocket:
            msg = inputSocket.recv(1024)
            print(msg.decode('utf-8'))

            if not msg:
                sockets = []
                break
                
        else:
            try:
                msg = inputSocket.readline()
                connectionSocket.send(msg.encode('utf-8'))
            except:
                pass
            
    if sockets == []:
        break
connectionSocket.close()


        




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
