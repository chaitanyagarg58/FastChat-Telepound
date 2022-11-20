import socket
import select
import os
import sys
import json
import time
import datetime
import base64
import psycopg2

HEADER_LENGTH = 10
BUFFER_LENGTH = 4096

conn = psycopg2.connect(database="postgres", user='client', password='telepoundClient', host='127.0.0.1', port= '5432')
conn.autocommit = True
cursor = conn.cursor()
cursor.execute("SELECT * FROM clientinfo")
print (cursor.fetchall())

HOST = '127.0.0.1'
PORT = 5000
ADDR = (HOST, PORT)

class Client:
    def __init__(self, client_, addr_):
        self.client = client_
        self.addr = addr_
        self.username = None
        self.attemptLogin()


    def attemptLogin(self):
        username = ""
        while username == "":
            username = input("Enter Username: ")
        packet = self.packJSON("signup", None, None, username, None)
        self.client.send(packet)


    def loginResponse(self, response):
        if response["message"] == "Successful":
            print ("Signup Successful")
            self.username = response["to"]
            print(self.username, "> ", end="", flush=True)
        else:
            print ("Username already Exists. Please Retry.")
            self.attemptLogin()


    def setup(self):
        pass


    def sendMessage(self, inputSocket):
        msg = inputSocket.readline().strip()
        if msg != "":
            msgType = "text"
            print ("Send To > ", end="", flush=True)
            toUser = inputSocket.readline().strip()
            print ("Enter Filename if you want to attach it > ", end="", flush=True)
            filename = inputSocket.readline().strip()
            if filename != "":
                if os.path.exists(filename):
                    if os.path.isdir(filename):
                        print ("Attaching folder is not Supported!! Sending message without attachment.", flush=True)
                        filename = None
                    else:
                        msgType = "file"
                else:
                    print ("File does not exist!! Sending without file.", flush=True)
                    filename = None
            else:
                filename = None
            packet = self.packJSON(msgType, self.username, toUser, msg, filename)
            self.client.send(packet)


    def recvMessage(self, msgLength):
        msg = b''
        while len(msg) < msgLength:
            msg = msg + self.client.recv(BUFFER_LENGTH)
        
        msgJson = self.unpackJSON(msg)
        if msgJson["type"] == "signup":
            self.loginResponse(msgJson)
            return
        if msgJson["from"] == None:
            print (msgJson["message"])
            print (self.username, "> ", end="", flush=True)
            return

        timeFormated = datetime.datetime.fromtimestamp(msgJson["time"])
        print ('\n\t', timeFormated.strftime('%a, %-d/%-m/%Y'))
        print(msgJson["from"], ": ", msgJson["message"], '\n', "Time: ", timeFormated.strftime('%-I:%M %p'), sep="", flush=True)
        if msgJson["type"] == "file":
            print ("A file is attached, do you want to download it? (y/n)[n] > ", end="", flush=True)
            res = sys.stdin.readline().strip()
            if res == "y":
                byte = msgJson["file"]
                decodeit = open(msgJson["filename"], 'wb')
                decodeit.write(base64.b64decode((byte)))
                decodeit.close()
        print (self.username, "> ", end="", flush=True)
            

    def packJSON(self, type, fromUser, toUser, msg, filename):
        package = {"type": type, "from": fromUser, "to": toUser, "message": msg, "filename": filename, "time": time.time()}
        
        if filename != None:
            with open(filename, "rb") as file:
                fileString = (base64.b64encode(file.read())).decode('utf-8')
                filename = filename.split("/")
                filename = filename[len(filename)-1]
                package["file"] = fileString
                package["filename"] = filename

        packString = json.dumps(package)
        packString = f'{len(packString):<{HEADER_LENGTH}}'+ packString
        return packString.encode('utf-8')

   
    def unpackJSON(self, packString):
        return json.loads(packString.decode('utf-8'))



connectionSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Waiting for connection response')
try:
    connectionSocket.connect((HOST, PORT))
except socket.error as e:
    print(str(e))

myClient = Client(connectionSocket, ADDR)
sockets = [connectionSocket, sys.stdin]

while True:
    readSocket, x, errorSocket = select.select(sockets,[],sockets)
    for inputSocket in readSocket:
        if inputSocket == connectionSocket:
            msgHeader = inputSocket.recv(HEADER_LENGTH)
            if not msgHeader:
                sockets = []
                break
            myClient.recvMessage(int(msgHeader))
        else:
            myClient.sendMessage(inputSocket)

    if sockets == []:
        break
conn.close()
connectionSocket.close()
