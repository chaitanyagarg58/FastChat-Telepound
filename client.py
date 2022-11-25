import socket
import select
import sys
import psycopg2
from clientHelper import *

HOST = '127.0.0.1'
PORT = int(sys.argv[1])
ADDR = (HOST, PORT)

balancer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    balancer.connect((HOST, PORT))
except socket.error as e:
    print(str(e))

myClient = Client(balancer)

while True:
    readSocket, x, errorSocket = select.select(myClient.sockets,[],myClient.sockets)
    for inputSocket in readSocket:
        if inputSocket == sys.stdin:
            myClient.sendMessage(inputSocket)
        else:
            msgHeader = inputSocket.recv(HEADER_LENGTH)
            if not msgHeader:
                myClient.sockets = []
                break
            myClient.recvMessage(int(msgHeader.decode('utf-8')), inputSocket)

    if myClient.sockets == []:
        break
conn.close()
for server in myClient.sockets:
    if server != sys.stdin:
        server.close()