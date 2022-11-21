import socket
import select
import json
import time
import psycopg2

HEADER_LENGTH = 10
BUFFER_LENGTH = 4096

conn = psycopg2.connect(database="postgres", user='postgres', password='telepoundServer', host='127.0.0.1', port= '5432')
conn.autocommit = True
cursor = conn.cursor()


HOST = '127.0.0.1'
PORT = 5000
serverSideSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSideSocket.bind((HOST, PORT))
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
            if msgJson["to"] == None:
                if msgJson["type"] == "signup":
                    username = msgJson["username"]
                    clientByUsername[username] = checkSocket
                    clientBySockets[checkSocket] = username
                    cursor.execute("INSERT INTO clientinfo (username, status, ip, port, password, public_n, public_e, private_d, private_p, private_q, salt) VALUES ('%s', '%s', '%s', %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s')"% (username, True, addr[0], addr[1], msgJson["password"], str(msgJson["public_n"]), str(msgJson["public_e"]), str(msgJson["private_d"]), str(msgJson["private_p"]), str(msgJson["private_q"]), msgJson["salt"]))
                    print (f"New Connection from: Username = {username} at {addr}")
                elif msgJson["type"] == "login":
                    username = msgJson["username"]
                    clientByUsername[username] = checkSocket
                    clientBySockets[checkSocket] = username
                    cursor.execute("UPDATE clientinfo SET status = 'True' WHERE ip = '%s' AND port = '%s'"% (checkSocket.getpeername()[0], checkSocket.getpeername()[1]))
                            
            elif msgJson["to"] in clientByUsername and clientByUsername[msgJson["to"]] != checkSocket:
                clientByUsername[msgJson["to"]].send(msg)
                readReceipt = json.dumps({"type": "text", "from": None, "message": "Message Delivered", "time": time.time()})
                readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
                checkSocket.send(readReceipt.encode('utf-8'))
            else:    
                readReceipt = json.dumps({"type": "text", "from": None, "message": "User Not Found", "time": time.time()})
                readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
                checkSocket.send(readReceipt.encode('utf-8'))

    if serverSideSocket in errorSockets:
        conn.close()

    for checkSocket in errorSockets:
        sockets.remove(checkSocket)
        del clientByUsername[clientBySockets[checkSocket]]
        del clientBySockets[checkSocket]
