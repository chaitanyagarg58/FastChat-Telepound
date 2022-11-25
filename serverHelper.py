import json
import time
import psycopg2


HEADER_LENGTH = 10
BUFFER_LENGTH = 4096


conn = psycopg2.connect(database="postgres", user='postgres', password='telepoundServer', host='127.0.0.1', port='5432')
conn.autocommit = True
cursor = conn.cursor()


clientBySockets = {}
clientByUsername = {}


def newConnection(msgJson, client):
    '''This method handles events if new client connects to this server.

    :param msgJson: This is the message sent by client for new connection request.
    :type msgJson: dict

    :param client: This is the client who established new connection.
    :type client: socket.socket
    '''
    username = msgJson["username"]
    clientByUsername[username] = client
    clientBySockets[client] = username
    print (f"Connection created from: Username = '{username}' at {client.getpeername()}")
    if msgJson["assigned"] == True:
        cursor.execute("SELECT message FROM undelivered WHERE touser = '%s'"% (username))
        messages = cursor.fetchall()
        cursor.execute("DELETE FROM undelivered WHERE touser = '%s'"% (username))
        if len(messages) == 0:
            return
        for m in messages:
            client.send(eval(m[0]))


def newGroup(msgJson, client):
    '''This method handles events when client sends a request to create a new group.

    :param msgJson: The request message send by client
    :type msgJson: dict

    :param client: The client who send the request
    :type client: socket.socket
    '''
    cursor.execute("INSERT INTO groupinfo (groupname, admin, members) VALUES ('%s', '%s', ARRAY[$t1$%s$t1$])"% (msgJson["groupName"], msgJson["username"], msgJson["username"]))
    readReceipt = json.dumps({"type": "readReceipt", "from": None, "message": "New Group Created.", "time": time.time()})
    readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
    client.send(readReceipt.encode('utf-8'))


def addMember(msgJson, client):
    '''This method handles events when client sends a request to add a member to a group.

    :param msgJson: The request message send by client
    :type msgJson: dict

    :param client: The client who send the request
    :type client: socket.socket
    '''
    cursor.execute("UPDATE groupinfo SET members = array_append(members, $t1$%s$t1$) WHERE groupname = $t2$%s$t2$"% (msgJson["username"], msgJson["groupName"]))
    readReceipt = json.dumps({"type": "readReceipt", "from": None, "message": "Member added to Group.", "time": time.time()})
    readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
    client.send(readReceipt.encode('utf-8'))


def removeMember(msgJson, client):
    '''This method handles events when client sends a request to remove a member from a group, or leave a group.

    :param msgJson: The request message send by client
    :type msgJson: dict

    :param client: The client who send the request
    :type client: socket.socket
    '''
    cursor.execute("SELECT admin FROM groupinfo WHERE groupname = $t2$%s$t2$"% (msgJson["groupName"]))
    admin = cursor.fetchone()[0]
    readReceipt = {"type": "readReceipt", "from": None, "message": "Member removed from Group.", "time": time.time()}
    if admin == msgJson["username"]:
        cursor.execute("DELETE FROM groupinfo WHERE groupname = $t2$%s$t2$"% (msgJson["groupName"]))
    else:
        cursor.execute("UPDATE groupinfo SET members = array_remove(members, $t1$%s$t1$) WHERE groupname = $t2$%s$t2$"% (msgJson["username"], msgJson["groupName"]))
    if msgJson["type"] == "leaveGroup":
        readReceipt["message"] = "You Left the Group."
    if admin == msgJson["username"]:
        readReceipt["message"] = "You were group admin and you left the Group. Group has been deleted."
    readReceipt = json.dumps(readReceipt)
    readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
    client.send(readReceipt.encode('utf-8'))


def sendMsg(msgJson, client, msg):
    '''This method handles events when client sends a message to another user or group and the user is online.

    :param msgJson: The unpacked message send by client
    :type msgJson: dict

    :param client: The client who send the request
    :type client: socket.socket

    :param msg: The packed/complete message sent by the client
    :type msg: bit string
    '''
    clientByUsername[msgJson["to"]].send(msg)
    if not msgJson["groupMsg"]:
        readReceipt = json.dumps({"type": "readReceipt", "from": None, "message": "Message Delivered", "time": time.time()})
        readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
        client.send(readReceipt.encode('utf-8'))


def storeMsg(msgJson, client, msg):
    '''This method handles events when client sends a message to another user or group and the user is offline.

    :param msgJson: The unpacked message send by client
    :type msgJson: dict

    :param client: The client who send the request
    :type client: socket.socket

    :param msg: The packed/complete message sent by the client
    :type msg: bit string
    '''
    cursor.execute("INSERT INTO undelivered (time, touser, message) VALUES (%s, '%s', $t1$%s$t1$)"% (msgJson["time"], msgJson["to"], msg))
    if not msgJson["groupMsg"]:
        readReceipt = json.dumps({"type": "readReceipt", "from": None, "message": "User is offline, message will be sent when he comes online.", "time": time.time()})
        readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
        client.send(readReceipt.encode('utf-8'))
