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


serverSockets = []
serverIP = []
serverPort = []
serverLoad = heapdict.heapdict()
clientToServer = {}
clientSockets = []
clientBySockets = {}
clientByUsername = {}


def packJSONConnClient(type, to, serverIP, serverPort):
    '''This method is to create and pack a Json object with the given information, speciaized for use when a client connects.

    :param type: The type of the message, the key to distinguish different kind of messages.
    :type type: string

    :param to: Username of client this message is to be sent to.
    :type to: string

    :param serverIP: the IP details of the server(s) we want to send.
    :type serverIP: string, list

    :param serverPort: the port details of the server(s) we want to send.
    :type serverPort: int, list
    '''
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
    '''This message unpacks any json strings and returns the json object.

    :param packString: The string to be unpacked.
    :type packString: string
    '''
    return json.loads(packString.decode('utf-8'))


def newClientConn(msgJson, client):
    '''This method handles all the changes to be made if a new Client logins or signs up.
    
    :param msgJson: The msg received as login/signup request from user.
    :type msgJson: dict

    :param client: The client where login/signup occured.
    :type client: socket.socket
    '''
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
    '''This method assigns the sever, with least load factor, to the given cient.

    :param username: The username of client which requested to assign server.
    :type username: string

    :param client: The client to assign server to.
    :type client: socket.socket
    '''
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



def newServerConn(msgJson, server, addr):
    '''This method handles events if a new server is made online.

    :param msgJson: The msg received from the new server when it came online.
    :type msgJson: dict

    :param server: The server which came online.
    :type server: socket.socket

    :param addr: The addr of the new server
    :type addr: tuple
    '''
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
