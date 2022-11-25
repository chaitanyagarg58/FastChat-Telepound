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
                username = msgJson["username"]
                clientByUsername[username] = checkSocket
                clientBySockets[checkSocket] = username
                print (f"Connection created from: Username = '{username}' at {checkSocket.getpeername()}")
                if msgJson["assigned"] == True:
                    cursor.execute("SELECT message FROM undelivered WHERE touser = '%s'"% (username))
                    messages = cursor.fetchall()
                    cursor.execute("DELETE FROM undelivered WHERE touser = '%s'"% (username))
                    if len(messages) == 0:
                        continue
                    for m in messages:
                        checkSocket.send(eval(m[0]))
            
            elif msgJson["type"] == "newGroup":
                cursor.execute("INSERT INTO groupinfo (groupname, admin, members) VALUES ('%s', '%s', ARRAY[$t1$%s$t1$])"% (msgJson["groupName"], msgJson["username"], msgJson["username"]))
                readReceipt = json.dumps({"type": "readReceipt", "from": None, "message": "New Group Created.", "time": time.time()})
                readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
                checkSocket.send(readReceipt.encode('utf-8'))

            elif msgJson["type"] == "addMember":
                cursor.execute("UPDATE groupinfo SET members = array_append(members, $t1$%s$t1$) WHERE groupname = $t2$%s$t2$"% (msgJson["username"], msgJson["groupName"]))
                readReceipt = json.dumps({"type": "readReceipt", "from": None, "message": "Member added to Group.", "time": time.time()})
                readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
                checkSocket.send(readReceipt.encode('utf-8'))
            
            elif msgJson["type"] == "removeMember" or msgJson["type"] == "leaveGroup":
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
                checkSocket.send(readReceipt.encode('utf-8'))

            elif msgJson["to"] in clientByUsername and clientByUsername[msgJson["to"]] != checkSocket:
                clientByUsername[msgJson["to"]].send(msg)
                if not msgJson["groupMsg"]:
                    readReceipt = json.dumps({"type": "readReceipt", "from": None, "message": "Message Delivered", "time": time.time()})
                    readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
                    checkSocket.send(readReceipt.encode('utf-8'))
            
            elif msgJson["to"] not in clientByUsername:
                cursor.execute("INSERT INTO undelivered (time, touser, message) VALUES (%s, '%s', $t1$%s$t1$)"% (msgJson["time"], msgJson["to"], msg))
                if not msgJson["groupMsg"]:
                    readReceipt = json.dumps({"type": "readReceipt", "from": None, "message": "User is offline, message will be sent when he comes online.", "time": time.time()})
                    readReceipt = f'{len(readReceipt):<{HEADER_LENGTH}}'+ readReceipt
                    checkSocket.send(readReceipt.encode('utf-8'))

    if serverSideSocket in errorSockets:
        conn.close()
        balancer.close()
        quit()

    for checkSocket in errorSockets:
        sockets.remove(checkSocket)
        del clientByUsername[clientBySockets[checkSocket]]
        del clientBySockets[checkSocket]
