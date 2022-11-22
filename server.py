import socket
import select
import json
import sys
import time
import psycopg2

HEADER_LENGTH = 10
BUFFER_LENGTH = 4096

conn = psycopg2.connect(database="postgres", user='postgres', password='telepoundServer', host='127.0.0.1', port='5432')
conn.autocommit = True
cursor = conn.cursor()


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
clientBySockets = {}
clientByUsername = {}

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
                cursor.execute("UPDATE clientinfo SET status = 'False' WHERE ip = '%s' AND port = '%s'"% (checkSocket.getpeername()[0], checkSocket.getpeername()[1]))
                sockets.remove(checkSocket)
                del clientByUsername[clientBySockets[checkSocket]]
                del clientBySockets[checkSocket]
                break
            
            msg = msgHeader
            msgLength = int(msgHeader[:HEADER_LENGTH])
            while len(msg) < HEADER_LENGTH + msgLength:
                msg = msg + checkSocket.recv(BUFFER_LENGTH)

            msgJson = json.loads(msg[HEADER_LENGTH:])
            if msgJson["type"] == "connect":
                username = msgJson["username"]
                clientByUsername[username] = checkSocket
                clientBySockets[checkSocket] = username
            if msgJson["to"] in clientByUsername and clientByUsername[msgJson["to"]] != checkSocket:
                clientByUsername[msgJson["to"]].send(msg)
                readReceipt = json.dumps({"type": "text", "from": None, "message": "Message Delivered", "time": time.time()})
                readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
                checkSocket.send(readReceipt.encode('utf-8'))
            # else:
            #     readReceipt = json.dumps({"type": "text", "from": None, "message": "User Not Found", "time": time.time()})
            #     readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
            #     checkSocket.send(readReceipt.encode('utf-8'))

    if serverSideSocket in errorSockets:
        conn.close()
        balancer.close()

    for checkSocket in errorSockets:
        sockets.remove(checkSocket)
        del clientByUsername[clientBySockets[checkSocket]]
        del clientBySockets[checkSocket]
