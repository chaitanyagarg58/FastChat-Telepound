import socket
import select
import json
import sys
import time
from serverHelper import *

HOST = '127.0.0.1'
PORT = int(sys.argv[1])
balancer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
balancer.connect((HOST, PORT))

serverSideSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSideSocket.bind((HOST, 0))
ADDR = serverSideSocket.getsockname()
print('Server is Online')
serverSideSocket.listen()
info = json.dumps({"type": "connectionServer", "ip": ADDR[0], "port": ADDR[1], "time": time.time()})
info = f'{len(info):<{HEADER_LENGTH}}'+ info
balancer.send(info.encode('utf-8'))

sockets = [serverSideSocket]

while True:
    activeSockets, x, errorSockets = select.select(sockets, [], sockets)
    for checkSocket in activeSockets:
        if checkSocket == serverSideSocket:
            newClient, addr = serverSideSocket.accept()
            sockets.append(newClient)
        else:
            try:
                msgHeader = checkSocket.recv(BUFFER_LENGTH)
            except:
                pass

            if not msgHeader:
                print (f"Connection Closed from: Username = '{clientBySockets[checkSocket]}' at {checkSocket.getpeername()}")
                sockets.remove(checkSocket)
                del clientByUsername[clientBySockets[checkSocket]]
                del clientBySockets[checkSocket]
                break
            
            msg = msgHeader
            msgLength = int(msgHeader[:HEADER_LENGTH])
            while len(msg) < HEADER_LENGTH + msgLength:
                if len(msg) + BUFFER_LENGTH > HEADER_LENGTH + msgLength:
                    msg = msg + checkSocket.recv(HEADER_LENGTH + msgLength - len(msg))
                    break
                msg = msg + checkSocket.recv(BUFFER_LENGTH)

            msgJson = json.loads(msg[HEADER_LENGTH:])
            if msgJson["type"] == "connect":
                newConnection(msgJson, checkSocket)
            
            elif msgJson["type"] == "newGroup":
                newGroup(msgJson, checkSocket)

            elif msgJson["type"] == "addMember":
                addMember(msgJson, checkSocket)
            
            elif msgJson["type"] == "removeMember" or msgJson["type"] == "leaveGroup":
                removeMember(msgJson, checkSocket)

            elif msgJson["to"] in clientByUsername and clientByUsername[msgJson["to"]] != checkSocket:
                sendMsg(msgJson, checkSocket, msg)
            
            elif msgJson["to"] not in clientByUsername:
                storeMsg(msgJson, checkSocket, msg)

    if serverSideSocket in errorSockets:
        conn.close()
        balancer.close()
        quit()

    for checkSocket in errorSockets:
        sockets.remove(checkSocket)
        del clientByUsername[clientBySockets[checkSocket]]
        del clientBySockets[checkSocket]
