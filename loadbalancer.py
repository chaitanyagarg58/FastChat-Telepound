import socket
import select
import json
import sys
import time
import psycopg2
import heapdict
from balancerHelper import *


HOST = '127.0.0.1'
PORT = int(sys.argv[1])
balancer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
balancer.bind((HOST, PORT))
print('Balancer is Online')
balancer.listen()


sockets = [balancer]


while True:
    activeSockets, x, errorSockets = select.select(sockets, [], sockets)
    for checkSocket in activeSockets:
        if checkSocket == balancer:
            newClient, addr = balancer.accept()
            sockets.append(newClient)
        else:
            msgHeader = checkSocket.recv(HEADER_LENGTH)

            if not msgHeader:
                if checkSocket in clientSockets:
                    print (f"Connection Closed from: Username = '{clientBySockets[checkSocket]}' at {checkSocket.getpeername()}")
                    clientSockets.remove(checkSocket)
                    del clientByUsername[clientBySockets[checkSocket]]
                    del clientBySockets[checkSocket]
                elif checkSocket in serverSockets:
                    index = serverSockets.index(checkSocket)
                    addr = (serverIP[index], serverPort[index])
                    print (f"Connection lost from Server listening at address = {addr}")
                    serverSockets.remove(checkSocket)
                    serverIP.remove(addr[0])
                    serverPort.remove(addr[1])
                    del serverLoad[checkSocket]
                sockets.remove(checkSocket)
                break

            msgLength = int(msgHeader)
            msg = b''
            while len(msg) < msgLength:
                msg = msg + checkSocket.recv(BUFFER_LENGTH)
            
            msgJson = unpackJSON(msg)
            if msgJson['type'] == 'connectionServer':
                newServerConn(msgJson, checkSocket, addr)
                
            elif msgJson['type'] == 'connectionClient':
                newClientConn(msgJson, checkSocket)

            elif msgJson['type'] == 'clientReassign':
                serverAssign(msgJson['username'], checkSocket)
        
    if balancer in errorSockets:
        conn.close()
    
    for client in errorSockets:
        sockets.remove(client)
        if client in clientSockets:
            serverLoad[clientToServer[client]] -= 1
            clientSockets.remove(client)
            del clientByUsername[clientBySockets[client]]
            del clientBySockets[client]
        elif client in serverSockets:
            serverSockets.remove(client)
            addr = client.getpeername()
            serverIP.remove(addr[0])
            serverPort.remove(addr[1])
            del serverLoad[client]
