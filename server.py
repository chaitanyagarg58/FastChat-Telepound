import socket
import select
import sys
import json
import time

HEADER_LENGTH = 10
BUFFER_LENGTH = 4096

host = '127.0.0.1'
port = 5003
serverSideSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSideSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
            while True:
                userHeader = newClient.recv(BUFFER_LENGTH)
                user = userHeader[HEADER_LENGTH:]
                userLength = int(userHeader[:HEADER_LENGTH])
                while len(user) < userLength:
                    user = user + newClient.recv(BUFFER_LENGTH)
                userJson = json.loads(user)
                username = userJson["user"]
                if username in clientByUsername:
                    res = json.dumps({"message":"AlreadyExists"})
                    newClient.send((f'{len(res):<{HEADER_LENGTH}}'+res).encode('utf-8'))
                else:
                    res = json.dumps({"message":"Connected"})
                    newClient.send((f'{len(res):<{HEADER_LENGTH}}'+res).encode('utf-8'))
                    clientByUsername[username] = newClient
                    clientBySockets[newClient] = username
                    sockets.append(newClient)
                    print (f"Connection from: Username = {username} at {addr}")
                    break
                
        else:        
            msgHeader = checkSocket.recv(BUFFER_LENGTH)

            if not msgHeader:
                print (f"Connection Closed from: Username = '{username}' at {addr}")
                sockets.remove(checkSocket)
                del clientByUsername[clientBySockets[checkSocket]]
                del clientBySockets[checkSocket]
                break
            
            msg = msgHeader
            msgLength = int(msgHeader[:HEADER_LENGTH])
            while len(msg) < HEADER_LENGTH + msgLength:
                msg = msg + checkSocket.recv(BUFFER_LENGTH)
 
            readReceipt = json.dumps({"from":"server", "message":"Message Delivered", "time":time.time()})
            readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
            checkSocket.send(readReceipt.encode('utf-8'))

            msgJson = json.loads(msg[HEADER_LENGTH:])
            if msgJson["to"] in clientByUsername and clientByUsername[msgJson["to"]] != checkSocket:
                clientByUsername[msgJson["to"]].send(msg)
    
    for checkSocket in errorSockets:
        sockets.remove(checkSocket)
        del clientByUsername[clientBySockets[checkSocket]]
        del clientBySockets[checkSocket]
