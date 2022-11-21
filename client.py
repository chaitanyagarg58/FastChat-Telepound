import socket
import select
import os
import sys
import json
import time
import datetime
import base64
import psycopg2
import bcrypt
import rsa
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

HEADER_LENGTH = 10
BUFFER_LENGTH = 4096
FILE_BUFFER = 117

conn = psycopg2.connect(database="postgres", user='client', password='telepoundClient', host='127.0.0.1', port= '5432')
conn.autocommit = True
cursor = conn.cursor()

def userPresent(username):
    cursor.execute("SELECT * FROM clientinfo WHERE username = '%s'"% (username))
    user = cursor.fetchall()
    if len(user) == 1:
        return True
    else:
        return False


HOST = '127.0.0.1'
PORT = 5000
ADDR = (HOST, PORT)

class Client:
    def __init__(self, client_, addr_):
        self.client = client_
        self.addr = addr_
        self.username = None
        self.public = None
        self.private = None
        choice = input("Sign-up(s) or Login(l) (s/l) [l] > ")
        if choice == 's':
            self.attemptSignup()
        else:
            self.attemptLogin()

    def attemptLogin(self):
        while True:
            username = ""
            while username == "":
                username = input("Enter Username: ")
            if not userPresent(username):
                choice = input("User not found, if you wish to signup, enter [s]: ")
                if choice == 's':
                    print ("Redirecting to Signup.")
                    self.attemptSignup()
                    return
                else:
                    print ("Retry Login.")
            else:
                cursor.execute("SELECT password FROM clientinfo WHERE username = '%s'"% (username))
                p = cursor.fetchone()[0]
                retry = False
                for i in range (5):
                    passwd = input("Enter Password: ")
                    if bcrypt.checkpw(passwd.encode('utf-8'), p.encode('utf-8')):
                        print ("Login Succesful!!")
                        break
                    else:
                        i += 1
                        if i == 5:
                            print ("Wrong Password, attempt 5/5")
                            print ("Maximum limit reached, aborting program!!")
                            conn.close()
                            connectionSocket.close()
                            quit()
                        choice = input ("Wrong Password, attempt %s/5 | press (i) to change username: "% (i))
                        if choice == 'i':
                            print ("Retry Login.")
                            retry = True
                            break
                if retry:
                    continue
                self.username = username
                cursor.execute("SELECT public_n, public_e, private_d, private_p, private_q, salt FROM clientinfo WHERE username = '%s'"% (username))
                (n,e,d,p,q,salt) = cursor.fetchone()
                n, e = int(n), int(e)
                salt = salt.encode('latin-1')
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=480000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(passwd.encode('utf-8')))
                f = Fernet(key)
                d = int(f.decrypt(d.encode('utf-8')).decode('utf-8'))
                p = int(f.decrypt(p.encode('utf-8')).decode('utf-8'))
                q = int(f.decrypt(q.encode('utf-8')).decode('utf-8'))
                self.public = rsa.PublicKey(n, e)
                self.private = rsa.PrivateKey(n, e, d, p, q)

                packet = self.packJSONlogin(username)
                self.client.send(packet)
                break


    def packJSONlogin(self, username):
        package = {"type": "login", "to": None, "username": username, "time": time.time()}
        packString = json.dumps(package)
        packString = f'{len(packString):<{HEADER_LENGTH}}'+ packString
        return packString.encode('utf-8')


    def attemptSignup(self):
        while True:
            username = ""
            while username == "":
                username = input("Enter Username: ")
            if userPresent(username):
                print ("Username already exists, try another!!")
            else:
                self.username = username
                break
        while True:    
            passwd = input ("Create Password: ")
            passwd2 = input ("Confirm Password: ")
            if passwd == passwd2:
                print ("Sign-up Successful !!")
                break
            else:
                print ("Passwords don't match, Retry !!!")
        
        (self.public, self.private) = rsa.newkeys(1024)
        password = passwd.encode('utf-8')
        salt = bcrypt.gensalt()
        password = bcrypt.hashpw(password, salt)

        saltPrivate = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=saltPrivate,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(passwd.encode('utf-8')))
        f = Fernet(key)
        private_d = f.encrypt(str(self.private['d']).encode('utf-8'))
        private_p = f.encrypt(str(self.private['p']).encode('utf-8'))
        private_q = f.encrypt(str(self.private['q']).encode('utf-8'))

        packet = self.packJSONsignup(username, password.decode('utf-8'), self.public, private_d.decode('utf-8'), private_p.decode('utf-8'), private_q.decode('utf-8'), saltPrivate.decode('latin-1'))
        self.client.send(packet)


    def packJSONsignup(self, username, passwd, public_key, private_d, private_p, private_q, saltPrivate):
        package = {
            "type": "signup",
            "to": None,
            "username": username,
            "password": passwd,
            "public_n": public_key['n'],
            "public_e": public_key['e'],
            "private_d": private_d,
            "private_p": private_p,
            "private_q": private_q,
            "salt": saltPrivate,
            "time": time.time()}
        packString = json.dumps(package)
        packString = f'{len(packString):<{HEADER_LENGTH}}'+ packString
        return packString.encode('utf-8')


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
        
        if msgJson["from"] == None:
            print (msgJson["message"])
            print (self.username, "> ", end="", flush=True)
            return

        timeFormated = datetime.datetime.fromtimestamp(msgJson["time"])
        print ('\n\t', timeFormated.strftime('%a, %-d/%-m/%Y'))
        print(msgJson["from"], ": ", rsa.decrypt(msgJson["message"].encode('latin-1'), self.private).decode('utf-8'), '\n', "Time: ", timeFormated.strftime('%-I:%M %p'), sep="", flush=True)
        if msgJson["type"] == "file":
            print ("A file is attached, do you want to download it? (y/n)[n] > ", end="", flush=True)
            res = sys.stdin.readline().strip()
            if res == "y":
                byteArray = msgJson["file"]
                filename = rsa.decrypt(msgJson["filename"].encode('latin-1'), self.private).decode('utf-8')
                byte = ""
                for i in byteArray:
                    byte += rsa.decrypt(i.encode('latin-1'), self.private).decode('utf-8')
                decodeit = open(filename, 'wb')
                decodeit.write(base64.b64decode((byte)))
                decodeit.close()
        print (self.username, "> ", end="", flush=True)
            

    def packJSON(self, type, fromUser, toUser, msg, filename):
        cursor.execute("SELECT public_n, public_e FROM clientinfo WHERE username = '%s'"% (toUser))
        (n,e,) = cursor.fetchone()
        n, e = int(n), int(e)
        pubKey = rsa.PublicKey(n, e)
        msg = rsa.encrypt(msg.encode('utf-8'), pubKey).decode('latin-1')
        package = {"type": type, "from": fromUser, "to": toUser, "message": msg, "filename": filename, "time": time.time()}
        
        if filename != None:
            with open(filename, "rb") as file:
                fileString = (base64.b64encode(file.read())).decode('utf-8')
                filename = filename.split("/")
                filename = filename[len(filename)-1]
                fileArray = []
                i = 0
                while i < len(fileString):
                    if i+FILE_BUFFER > len(fileString):     
                        temp = fileString[i:]
                        fileArray.append(rsa.encrypt(temp.encode('utf-8'), pubKey).decode('latin-1'))
                        break
                    temp = fileString[i:i+FILE_BUFFER]
                    fileArray.append(rsa.encrypt(temp.encode('utf-8'), pubKey).decode('latin-1'))
                    i = i + FILE_BUFFER
                package["file"] = fileArray
                package["filename"] = rsa.encrypt(filename.encode('utf-8'), pubKey).decode('latin-1')

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
