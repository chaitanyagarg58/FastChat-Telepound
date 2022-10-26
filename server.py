import socket
import sys
import json

# Server name and port
host = 'local host'
port = int(sys.argv[1])

#Create a socket at server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('',port))

# Maximum 100 clients possible
s.listen(100)

# Wait for client
c, addr = s.accept()

# Display Client address
print ('CONNECTION FROM:', str(addr))

# send message to the client after
# encoding into binary string
c.send(b"HELLO, How are you? Welcome to Akash hacking World")

msg = "Bye.........."
c.send(msg.encode())

msg = c.recv(1024)
print (msg)

c.close()