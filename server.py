import socket
import select

host = '127.0.0.1'
port = 5003
serverSideSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSideSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSideSocket.bind((host, port))
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
            while True:
                username = (newClient.recv(1024)).decode('utf-8')
                if username in clientByUsername:
                    newClient.send("AlreadyExists".encode('utf-8'))
                else:
                    newClient.send("Connected".encode('utf-8'))
                    clientByUsername[username] = newClient
                    clientBySockets[newClient] = username
                    sockets.append(newClient)
                    print (f"Connection from: Username = '{username}' at {addr}")
                    break
        else:        
            msg = checkSocket.recv(1024)

            if not msg:
                print (f"Connection Closed from: Username = '{username}' at {addr}")
                sockets.remove(checkSocket)
                del clientBySockets[checkSocket]
                break

            checkSocket.send("Message Delivered".encode('utf-8'))

            for otherClient in clientBySockets:
                if otherClient != checkSocket:
                    otherClient.send(msg)
    
    for checkSocket in errorSockets:
            sockets.remove(checkSocket)
            del clientBySockets[checkSocket]
