import socket
import select
import sys
import json
import time

HEADER_LENGTH = 10
BUFFER_LENGTH = 4096

host = '127.0.0.1'
port = 5002
serverSideSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSideSocket.bind((host, port))
print('Server is Online')
serverSideSocket.listen()

sockets = [serverSideSocket]
clientBySockets = {}
clientByUsername = {}

while True:
    activeSockets, x, errorSockets = select.select(sockets, [], sockets)
    for checkSocket in activeSockets:

        if checkSocket == serverSideSocket:
            newClient, addr = serverSideSocket.accept()
            sockets.append(newClient)
    
        else:
            msgHeader = checkSocket.recv(BUFFER_LENGTH)

            if not msgHeader:
                print (f"Connection Closed from: Username = '{clientBySockets[checkSocket]}' at {checkSocket.getsockname()}")
                sockets.remove(checkSocket)
                del clientByUsername[clientBySockets[checkSocket]]
                del clientBySockets[checkSocket]
                break
            
            msg = msgHeader
            msgLength = int(msgHeader[:HEADER_LENGTH])
            while len(msg) < HEADER_LENGTH + msgLength:
                msg = msg + checkSocket.recv(BUFFER_LENGTH)

            msgJson = json.loads(msg[HEADER_LENGTH:])
            if msgJson["to"] == None and msgJson["type"] == "signup":
                newUser = msgJson["message"]
                if newUser in clientByUsername:
                    res = json.dumps({"type": "signup", "from": None, "to": newUser, "message": "AlreadyExists", "time": time.time()})
                    res = f'{len(res):<{HEADER_LENGTH}}'+ res
                    checkSocket.send(res.encode('utf-8'))
                else:
                    res = json.dumps({"type": "signup", "from": None, "to": newUser, "message": "Successful", "time": time.time()})
                    checkSocket.send((f'{len(res):<{HEADER_LENGTH}}'+res).encode('utf-8'))
                    clientByUsername[newUser] = checkSocket
                    clientBySockets[newClient] = newUser
                    print (f"Connection from: Username = {newUser} at {addr}")
            
            elif msgJson["to"] in clientByUsername and clientByUsername[msgJson["to"]] != checkSocket:
                clientByUsername[msgJson["to"]].send(msg)
                readReceipt = json.dumps({"type": "text", "from": None, "message": "Message Delivered", "time": time.time()})
                readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
                checkSocket.send(readReceipt.encode('utf-8'))
            else:    
                readReceipt = json.dumps({"type": "text", "from": None, "message": "User Not Found", "time": time.time()})
                readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
                checkSocket.send(readReceipt.encode('utf-8'))


    for checkSocket in errorSockets:
        sockets.remove(checkSocket)
        del clientByUsername[clientBySockets[checkSocket]]
        del clientBySockets[checkSocket]
