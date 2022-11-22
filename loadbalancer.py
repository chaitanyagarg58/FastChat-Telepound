import socket
import select
import json
import sys
import time
import psycopg2
import heapdict


HEADER_LENGTH = 10
BUFFER_LENGTH = 4096

conn = psycopg2.connect(database="postgres", user='postgres', password='telepoundServer', host='127.0.0.1', port='5432')
conn.autocommit = True
cursor = conn.cursor()

HOST = '127.0.0.1'
PORT = int(sys.argv[1])
balancer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
balancer.bind((HOST, PORT))
print('Balancer is Online')
balancer.listen()

serverSockets = []
serverIP = []
serverPort = []
serverLoad = heapdict.heapdict()
clientToServer = {}
clientSockets = []
clientBySockets = {}
clientByUsername = {}

sockets = [balancer]


def packJSONConnClient(type, fromUser, to, serverIP, serverPort):
    package = {
        "type": type,
        "from": fromUser,
        "to": to,
        "serverIP": serverIP,
        "serverPort": serverPort,
        "time": time.time()
        }
    packString = json.dumps(package)
    packString = f'{len(packString):<{HEADER_LENGTH}}' + packString
    return packString.encode('utf-8')


def unpackJSON(packString):
        return json.loads(packString.decode('utf-8'))


def newClientConn(msgJson, client):
    clientSockets.append(client)
    username = msgJson['username']
    addr = client.getpeername()
    clientBySockets[client] = username
    clientByUsername[username] = client
    if msgJson['action'] == 'signup':
        cursor.execute("INSERT INTO clientinfo (username, status, ip, port, password, public_n, public_e, private_d, private_p, private_q, salt) VALUES ('%s', '%s', '%s', %s, '%s', '%s', '%s', '%s', '%s', '%s', $t1$%s$t1$)"% (username, True, addr[0], addr[1], msgJson["password"], str(msgJson["public_n"]), str(msgJson["public_e"]), str(msgJson["private_d"]), str(msgJson["private_p"]), str(msgJson["private_q"]), msgJson["salt"]))
        print (f"New User signup at Connection from: Username = {username} at {addr}")
    elif msgJson['action'] == 'login':
        cursor.execute("UPDATE clientinfo SET status = 'True' WHERE ip = '%s' AND port = '%s'"% (addr[0], addr[1]))
        print (f"Old User login at Connection from: Username = {username} at {addr}")

    serverAssign(username, client)
    serverAll = packJSONConnClient("servers", None, username, serverIP, serverPort)
    client.send(serverAll)
    

def serverAssign(username, client):
    if client in clientToServer.keys():
        serverLoad[clientToServer[client]] -= 1
    pickedServer = serverLoad.popitem()
    serverLoad[pickedServer[0]] = pickedServer[1] + 1
    clientToServer[client] = pickedServer[0]
    index = serverSockets.index(pickedServer[0])
    serverAssigned = packJSONConnClient("serverAssigned", None, username, serverIP[index], serverPort[index])
    client.send(serverAssigned)


def newServerConn(msgJson, server):
    serverSockets.append(server)
    serverLoad[server] = 0
    serverIP.append(msgJson["ip"])
    serverPort.append(msgJson["port"])
    print (f"New Server listening at {addr}")



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
                    cursor.execute("UPDATE clientinfo SET status = 'False' WHERE ip = '%s' AND port = '%s'"% (checkSocket.getpeername()[0], checkSocket.getpeername()[1]))
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
                newServerConn(msgJson, checkSocket)
                
            elif msgJson['type'] == 'connectionClient':
                newClientConn(msgJson, checkSocket)

            elif msgJson['type'] == 'clientReassign':
                serverAssign(msgJson['username'], checkSocket)
        
    if balancer in errorSockets:
        conn.close()
    
    for client in errorSockets:
        sockets.remove(client)
        if client in clientSockets:
            clientSockets.remove(client)
            del clientByUsername[clientBySockets[client]]
            del clientBySockets[client]
        elif client in serverSockets:
            serverSockets.remove(client)
            addr = client.getpeername()
            serverIP.remove(addr[0])
            serverPort.remove(addr[1])
            del serverLoad[client]
