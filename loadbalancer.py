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
PORT = 5000
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


def packJSONConnClient(type, to, serverIP, serverPort):
    # '''This method is to create and pack a Json object with the given information, speciaized for use when a client connects.

    # :param type: The type of the message, the key to distinguish different kind of messages.
    # :type type: string

    # :param to: Username of client this message is to be sent to.
    # :type to: string

    # :param serverIP: the IP details of the server(s) we want to send.
    # :type serverIP: string, list

    # :param serverPort: the port details of the server(s) we want to send.
    # :type serverPort: int, list
    # '''
    package = {
        "type": type,
        "from": None,
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
        cursor.execute("INSERT INTO clientinfo (username, password, public_n, public_e, private_d, private_p, private_q, salt) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', $t1$%s$t1$)"% (username, msgJson["password"], str(msgJson["public_n"]), str(msgJson["public_e"]), str(msgJson["private_d"]), str(msgJson["private_p"]), str(msgJson["private_q"]), msgJson["salt"]))
        print (f"New User signup at Connection from: Username = {username} at {addr}")
    elif msgJson['action'] == 'login':
        print (f"Old User login at Connection from: Username = {username} at {addr}")

    serverAssign(username, client)
    serverAll = packJSONConnClient("servers", username, serverIP, serverPort)
    client.send(serverAll)
    

def serverAssign(username, client):
    if client in clientToServer.keys():
        l = serverLoad[clientToServer[client]]
        del serverLoad[clientToServer[client]]
        serverLoad[clientToServer[client]] = l-1
    pickedServer = serverLoad.popitem()
    serverLoad[pickedServer[0]] = pickedServer[1] + 1
    clientToServer[client] = pickedServer[0]
    index = serverSockets.index(pickedServer[0])
    serverAssigned = packJSONConnClient("serverAssigned", username, serverIP[index], serverPort[index])
    client.send(serverAssigned)


def newServerConn(msgJson, server):
    serverSockets.append(server)
    serverLoad[server] = 0
    serverIP.append(msgJson["ip"])
    serverPort.append(msgJson["port"])

    newServer = {"type": "newServer", "serverIP": msgJson["ip"], "serverPort": msgJson["port"]}
    newServer = json.dumps(newServer)
    newServer = f'{len(newServer):<{HEADER_LENGTH}}' + newServer
    for client in clientSockets:
        client.send(newServer.encode('utf-8'))
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
