import socket
import select
import sys
import psycopg2
from clientHelper import *

HEADER_LENGTH = 10
BUFFER_LENGTH = 4096
FILE_BUFFER = 117

conn = psycopg2.connect(database="postgres", user='client', password='telepoundClient', host='127.0.0.1', port= '5432')
conn.autocommit = True
cursor = conn.cursor()

HOST = '127.0.0.1'
PORT = 5000
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