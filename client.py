import socket
import select
import os
import sys
import json
import time
import datetime
import base64

HEADER_LENGTH = 10
BUFFER_LENGTH = 4096

connectionSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '127.0.0.1'
port = 5003
print('Waiting for connection response')
try:
    connectionSocket.connect((host, port))
except socket.error as e:
    print(str(e))
while True:
    username = input("Enter Username: ")
    if username == "":
        continue
    j = {"user":username}
    userMsg = json.dumps(j)
    userMsg = f'{len(userMsg):<{HEADER_LENGTH}}' + userMsg
    connectionSocket.send(userMsg.encode('utf-8'))
    resHeader = connectionSocket.recv(BUFFER_LENGTH)
    res = resHeader[HEADER_LENGTH:]
    resLength = int(resHeader[:HEADER_LENGTH])
    while len(res) < resLength:
        res = res + connectionSocket.recv(BUFFER_LENGTH)
    resJson = json.loads(res)
    if resJson["message"] == "Connected":
        print (f'Connection Established! Welcome Back, {username}')
        break
    else:
        print ("Username is invalid, try again!")

sockets = [connectionSocket, sys.stdin]

print (username + " > ", end="", flush=True)
while True:
    readSocket, x, errorSocket = select.select(sockets,[],sockets)
    for inputSocket in readSocket:
        if inputSocket == connectionSocket:
            msgHeader = inputSocket.recv(BUFFER_LENGTH)

            if not msgHeader:
                sockets = []
                break

            msg = msgHeader[HEADER_LENGTH:]
            msgLength = int(msgHeader[:HEADER_LENGTH])
            while len(msg) < msgLength:
                msg = msg + inputSocket.recv(BUFFER_LENGTH)
            
            msgJson = json.loads(msg)
            if msgJson["from"] == "server":
                print (msgJson["message"], '\n', username, " > ", sep="", end="", flush=True)
            else:
                print (flush=True)
                timeFormated = datetime.datetime.fromtimestamp(msgJson["time"])
                print ('\t', timeFormated.strftime('%a, %-d/%-m/%Y'))
                print(msgJson["from"], ": ", (msgJson["message"]), '\n', "Time: ", timeFormated.strftime('%-I:%M %p'), sep="", flush=True)
                if msgJson["type"] == "file":
                    print ("A file is attached, do you want to download it? (y/n)[n] > ", end="", flush=True)
                    res = sys.stdin.readline().strip()
                    if res == "y":
                        byte = msgJson["file"]
                        decodeit = open(msgJson["filename"], 'wb')
                        decodeit.write(base64.b64decode((byte)))
                        decodeit.close()
                print(username + " > ", end="", flush=True)
        else:
            msg = inputSocket.readline().strip()
            if msg != "":
                msgType = "text"
                fileString = ""
                print ("Send To > ", end="", flush=True)
                toClient = inputSocket.readline().strip()
                print ("Enter Filename if you want to attach it > ", end="", flush=True)
                filename = inputSocket.readline().strip()
                if filename != "":
                    if os.path.exists(filename):
                        if os.path.isdir(filename):
                            print ("Attaching folder is not supported!! Sending message without attachment.", flush=True)
                        else:
                            with open(filename, "rb") as file:
                                fileString = (base64.b64encode(file.read())).decode('utf-8')
                                filename = filename.split("/")
                                filename = filename[len(filename)-1]
                                msgType = "file"
                    else:
                        print ("File does not exist!! Sending without file.", flush=True)
                toSend = {
                    "from": username,
                    "to": toClient,
                    "type": msgType,
                    "message": msg,
                    "filename": filename,
                    "file": fileString,
                    "time": time.time()
                }
                sendString = json.dumps(toSend)
                sendString = f'{len(sendString):<{HEADER_LENGTH}}'+ sendString
                connectionSocket.send(sendString.encode('utf-8'))
            else:
                print (username + " > ", end="", flush=True)
    if sockets == []:
        break
connectionSocket.close()
