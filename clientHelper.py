import socket
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


def userExist(username):
    '''
    This function finds if a user of given username exists or not.

    :param username: The username we want to find.
    :type username: string
    '''
    cursor.execute("SELECT * FROM clientinfo WHERE username = '%s'"% (username))
    user = cursor.fetchall()
    if len(user) == 1:
        return True
    else:
        return False
        
def groupExist(groupname):
    '''
    This function finds if a group of given groupname exists or not.

    :param groupname: The groupname we want to find.
    :type groupname: string
    '''
    cursor.execute("SELECT * FROM groupinfo WHERE groupname = '%s'"% (groupname))
    group = cursor.fetchall()
    if len(group) == 1:
        return True
    else:
        return False


class Client:
    '''
    This class contains all the functionalities of a client.
    '''
    def __init__(self, balancer_):
        '''Constructor Method.
        This method initialises member variables of class and also initialised signup/login process.

        :param balancer_: This is the socket of the load balancer we are connected to.
        :type balancer_: socket.socket
        '''
        self.balancer = balancer_
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverAddr = None
        self.serverCounter = 0
        self.username = None
        self.sockets = [self.balancer, sys.stdin]
        self.public = None
        self.private = None
        choice = input("Sign-up(s) or Login(l) (s/l) [l] > ")
        if choice == 's':
            self.attemptSignup()
        else:
            self.attemptLogin()
        print (self.username, "> " , end="", flush=True)

    def attemptLogin(self):
        '''This method completes login process.
        It completes the login process including:

        1. Takes username and password inputs and verifies if correct or not.

        2. Retrieves the public and private of the client and stores them.

        3. Sends login details to server.
        '''
        while True:
            username = ""
            while username == "":
                username = input("Enter Username: ")
            if not userExist(username):
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
                            self.balancer.close()
                            quit()
                        choice = input ("Wrong Password, attempt %s/5 | press (i) to change username: "% (i))
                        if choice == 'i':
                            print ("Retry Login.")
                            retry = True
                            break
                if retry:
                    continue
                break
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
        self.balancer.send(packet)
        self.recvServers()
        self.recvServers()



    def packJSONlogin(self, username):
        '''This method packs a json object for the login info to send to server.

        :param username: The username of the client that logged in.
        :type username: string
        '''
        package = {"type": "connectionClient", "action": "login", "to": None, "username": username, "time": time.time()}
        packString = json.dumps(package)
        packString = f'{len(packString):<{HEADER_LENGTH}}'+ packString
        return packString.encode('utf-8')


    def attemptSignup(self):
        '''This method completes Signup process.
        It does the following:

        1. Checks if the given username is valid.

        2. Confirms password.
        
        3. Generate rsa encryption keys for this client.
        
        4. Sends new user information to server to be stored.
        '''
        while True:
            username = ""
            while username == "":
                username = input("Enter Username: ")
            if userExist(username) or groupExist(username):
                print ("Username not available, try another!!")
            elif username in ["CREATE GROUP", "ADD MEMBER", "REMOVE MEMBER", "LEAVE GROUP"]:
                print ("Username Not Allowed, try another!!")
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
        self.balancer.send(packet)
        self.recvServers()
        self.recvServers()


    def packJSONsignup(self, username, passwd, public_key, private_d, private_p, private_q, saltPrivate):
        '''This method packs a json object for the signup info to send to server.

        :param username: The username of the client that logged in.
        :type username: string

        :param passwrd: The password of this client (encrypted).
        :type passwrd: string

        :param public_key: The public rsa key of this client, contains n and e values.
        :type public_key: rsa.PublicKey

        :param private_d: The d value of private key of this client (encrypted).
        :type private_d: string

        :param private_p: The p value of private key of this client (encrypted).
        :type private_p: string

        :param private_q: The q value of private key of this client (encrypted).
        :type private_q: string

        :param saltPrivate: The salt used to encrypt the private keys.
        :type saltPrivate: string
        '''
        package = {
            "type": "connectionClient",
            "action": "signup",
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
    


    def recvServers(self):
        '''This function is used to receive active servers information from the load balancer.
        
        If it receives a singal assigned server, it stores it's information.

        If it receives all the servers online, it stores them and connects to all.
        '''
        svrHeader = self.balancer.recv(HEADER_LENGTH)
        svrLength = int(svrHeader.decode('utf-8'))
        msg = b''
        while len(msg) < svrLength:
            if len(msg) + BUFFER_LENGTH > svrLength:
                msg = msg + self.balancer.recv(svrLength - len(msg))
                break
            msg = msg + self.balancer.recv(BUFFER_LENGTH)
        
        msgJson = self.unpackJSON(msg)
        package = {"type": "connect", "to": None, "username": self.username, "time": time.time()}

        if msgJson["type"] == "serverAssigned":
            self.serverAddr = (msgJson["serverIP"], msgJson["serverPort"])
            try:
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.connect(self.serverAddr)
            except socket.error as e:
                print(str(e))
            package["assigned"] = True
            packString = json.dumps(package)
            packString = f'{len(packString):<{HEADER_LENGTH}}'+ packString
            self.server.send(packString.encode('utf-8'))
            
        elif msgJson["type"] == "servers":
            ip = msgJson["serverIP"]
            port = msgJson["serverPort"]
            for i in range(len(ip)):
                addr = (ip[i], port[i])
                if addr == self.serverAddr:
                    self.sockets.append(self.server)
                else:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    try:
                        s.connect(addr)
                    except socket.error as e:
                        print(str(e))
                    package["assigned"] = False
                    packString = json.dumps(package)
                    packString = f'{len(packString):<{HEADER_LENGTH}}'+ packString
                    s.send(packString.encode('utf-8'))
                    self.sockets.append(s)


    def createGroup (self):
        '''This method handles new Group creation.
        
        It takes groupname as user input, checks if it is valid, and sends group info to server for group to be created.
        '''
        while True:
            groupName = ""
            while groupName == "":
                groupName = input("Enter Group Name: ")
            if userExist(groupName) or groupExist(groupName):
                print ("Group Name not available, try another!!")
            elif groupName in ["CREATE GROUP", "ADD MEMBER", "REMOVE MEMBER"]:
                print ("Group Name Not Allowed, try another!!")
            else:
                package = {"type": "newGroup", "to": None, "groupName": groupName, "username": self.username, "time": time.time()}
                packString = json.dumps(package)
                packString = f'{len(packString):<{HEADER_LENGTH}}'+ packString
                self.server.send(packString.encode('utf-8'))
                break


    def modifyGroup(self, msg):
        '''This method handles modification of group, adding of removing members.

        If takes required groupname and member name from user, checks if they are valid, and sends information to server for changs to be made.

        :param msg: This is the type of modification requested.
        :type msg: string
        '''
        cursor.execute("SELECT groupname FROM groupinfo WHERE admin='%s'"% (self.username))
        groups = cursor.fetchall()
        groupName = input("Enter Group Name: ")
        if (groupName,) not in groups:
            print ("Group does not exist or You do not have admin privelege on group. No changes made.")
            print (self.username, "> ", end="", flush=True)
            return
        else:
            cursor.execute("SELECT members FROM groupinfo WHERE groupname='%s'"% (groupName))
            members = cursor.fetchall()[0][0]
            if msg == "ADD MEMBER":
                user = input ("Enter User to add: ")
                if user in members:
                    print ("User is already in Group, No changes made.")
                    print (self.username, "> ", end="", flush=True)
                    return
                elif not userExist(user):
                    print ("User does not exist, No changes made.")
                    print (self.username, "> ", end="", flush=True)
                    return
                else:
                    package = {"type": "addMember", "to": None, "groupName": groupName, "username": user, "time": time.time()}
                    packString = json.dumps(package)
                    packString = f'{len(packString):<{HEADER_LENGTH}}'+ packString
                    self.server.send(packString.encode('utf-8'))
            
            elif msg == "REMOVE MEMBER":
                user = input ("Enter User to remove: ")
                if user not in members:
                    print ("No such User in Group, No changes made.")
                    print (self.username, "> ", end="", flush=True)
                    return
                else:
                    package = {"type": "removeMember", "to": None, "groupName": groupName, "username": user, "time": time.time()}
                    packString = json.dumps(package)
                    packString = f'{len(packString):<{HEADER_LENGTH}}'+ packString
                    self.server.send(packString.encode('utf-8'))

    
    def leaveGroup(self):
        '''This method handles leaving a group.
        
        It takes groupname from user and if client is in the group, it sends informaiton to server for changes to be made.
        '''
        while True:
            groupName = ""
            while groupName == "":
                groupName = input("Enter Group Name: ")
            cursor.execute("SELECT members FROM groupinfo WHERE groupname='%s'"% (groupName))
            members = cursor.fetchall()[0][0]
            if self.username not in members:
                print ("You are not a member of such group. No changes made.")
                print (self.username, "> ", end="", flush=True)
                return
            else:
                package = {"type": "leaveGroup", "to": None, "groupName": groupName, "username": self.username, "time": time.time()}
                packString = json.dumps(package)
                packString = f'{len(packString):<{HEADER_LENGTH}}'+ packString
                self.server.send(packString.encode('utf-8'))
                break


    def sendMessage(self, inputSocket):
        '''This method handles everything that can happen if The user enters some instruction.
        
        It initializes group creation/modification if appropriate command is entered.
        
        Else it sends specified message to the specified user/group.

        :param inputSocket: The socket in which the user is giving input.
        :type inputSocket: socket.socket
        '''
        toUser = inputSocket.readline().strip()
        if toUser != "":
            if toUser == "CREATE GROUP":
                self.createGroup()
                return
            elif toUser in ["ADD MEMBER", "REMOVE MEMBER"]:
                self.modifyGroup(toUser)
                return
            elif toUser == "LEAVE GROUP":
                self.leaveGroup()
                return

            uExist = userExist(toUser)
            gExist = groupExist(toUser)
            if not (uExist or gExist):
                print ("User/Group does not exist, try again.", flush=True)
                print (self.username, "> ", end="", flush=True)
                return
            
            msgType = "text"
            print ("Message > ", end="", flush=True)
            msg = inputSocket.readline().strip()
    
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

            if uExist:
                packet = self.packJSON(msgType, self.username, toUser, msg, filename, False)
                self.server.send(packet)
                self.serverCounter += 1
                if self.serverCounter == 5:
                    self.serverCounter = 0
                    package = {"type": "clientReassign", "username": self.username, "time": time.time()}
                    packString = json.dumps(package)
                    packString = f'{len(packString):<{HEADER_LENGTH}}'+ packString
                    self.balancer.send(packString.encode('utf-8'))
                    self.recvServers()
            else:
                cursor.execute("SELECT members FROM groupinfo WHERE groupname=$$%s$$"% (toUser))
                members = cursor.fetchall()[0][0]
                for member in members:
                    if member == self.username:
                        continue
                    packet = self.packJSON(msgType, 'Group ' + toUser + ': ' + self.username, member, msg, filename, True)
                    self.server.send(packet)
                    self.serverCounter += 1
                    if self.serverCounter == 5:
                        self.serverCounter = 0
                        package = {"type": "clientReassign", "username": self.username, "time": time.time()}
                        packString = json.dumps(package)
                        packString = f'{len(packString):<{HEADER_LENGTH}}'+ packString
                        self.balancer.send(packString.encode('utf-8'))
                        self.recvServers()
                print ("Message will reach users when they are online.")
                print (self.username, "> ", end="", flush=True)

        else:
            print (self.username, "> ", end="", flush=True)


    def recvMessage(self, msgLength, inputSocket):
        '''This method receives a msg is any connection/server tries to send one and handles all cases for types of messages.

        :param msgLength: The length of the message to be received.
        :type msgLength: int

        :param inputSocket: The socket which is trying to send message.
        :type inputSocket: socket.socket
        '''
        msg = b''
        while len(msg) < msgLength:
            if len(msg) + BUFFER_LENGTH > msgLength:
                msg = msg + inputSocket.recv(msgLength-len(msg))
                break
            msg = msg + inputSocket.recv(BUFFER_LENGTH)
        
        msgJson = self.unpackJSON(msg)
        
        if msgJson["type"] == "newServer":
            package = {"type": "connect", "to": None, "username": self.username, "time": time.time()}
            packString = json.dumps(package)
            packString = f'{len(packString):<{HEADER_LENGTH}}'+ packString

            newServerAddr = (msgJson["serverIP"], msgJson["serverPort"])
            try:
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.connect(newServerAddr)
            except socket.error as e:
                print(str(e))
            print (self.server.getpeername())
            self.server.send(packString.encode('utf-8'))

        if msgJson["type"] == "readReceipt":
            print (msgJson["message"])
            print (self.username, "> ", end="", flush=True)
            return

        timeFormated = datetime.datetime.fromtimestamp(msgJson["time"])
        print ('\n\t', timeFormated.strftime('%a, %-d/%-m/%Y'))
        print(msgJson["from"], " > ", rsa.decrypt(msgJson["message"].encode('latin-1'), self.private).decode('utf-8'), '\n', "Time: ", timeFormated.strftime('%-I:%M %p'), sep="", flush=True)
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
            

    def packJSON(self, type, fromUser, toUser, msg, filename, groupMsg):
        '''This method packs a json object with given information, mainly for sending messages to another user.
        
        This method, while reading and attaching files, encrypts them.

        :param type: This is the type of message we are sending.
        :type type: string

        :param fromUser: Username of this client, the user sending this message.
        :type fromUser: string

        :param toUser: Username of client we want to send message to.
        :type toUser: string

        :param msg: THe message to be sent (encrypted).
        :type msg: string

        :param filename: The name/path of the file to be attached.
        :type filename: string

        :param groupMsg: If the message is the group message or individual.
        :type groupMsg: bool
        '''
        cursor.execute("SELECT public_n, public_e FROM clientinfo WHERE username = '%s'"% (toUser))
        (n,e,) = cursor.fetchone()
        n, e = int(n), int(e)
        pubKey = rsa.PublicKey(n, e)
        msg = rsa.encrypt(msg.encode('utf-8'), pubKey).decode('latin-1')
        package = {"type": type, "from": fromUser, "to": toUser, "message": msg, "filename": filename, "time": time.time(), "groupMsg": groupMsg}
        
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
        '''This message unpacks any json strings and returns the json object.

        :param packString: The string to be unpacked.
        :type packString: string
        '''
        return json.loads(packString.decode('utf-8'))

