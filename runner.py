from pwn import *
import time
import threading
import os
import sys

NUM_CLIENTS = 2

if not os.path.exists("log"):
    os.makedirs("log")

class Runner:
    users = []
    def __init__(self, username):
        self.ps = None
        self.username = username
        self.ps = process(argv=['python3', 'client.py', sys.argv[1]])
        self.ps.clean()
        self.ps.sendline(b's')
        self.ps.clean()
        self.ps.sendline(self.username.encode())
        self.ps.clean()
        self.ps.sendline(self.username.encode())
        self.ps.clean()
        self.ps.sendline(self.username.encode())
        self.ps.clean()
        Runner.users.append(username)
        self.log_file = open("log/log_" + username + ".txt", "wb")
        
    def create_process(self)->None:
        for user in Runner.users:
            self.ps.clean()
            self.ps.sendline(f'{user}'.encode())
            self.ps.clean()
            self.ps.sendline(f'hi'.encode())
            self.ps.clean()
            self.ps.sendline(f''.encode())
            # self.log_file.write(self.ps.clean_and_log())

    def close(self):
        for i in range(NUM_CLIENTS*2):
            try:
                self.log_file.write(self.ps.clean_and_log())
                self.log_file.flush()
            except:
                pass
        # self.ps.sendline(b'EXIT')
        # if self.ps.poll(block = True):
        #     self.ps.close()

clients = [Runner(f"user{i}") for i in range(NUM_CLIENTS)]
sleep(4)
threads = []
for client in clients:
    threads.append(threading.Thread(target=client.create_process()))

closing_threads = []
for client in clients:
    closing_threads.append(threading.Thread(target=client.close()))

for thread in threads:
    thread.start()

for thread in closing_threads:
    thread.start()

for thread in threads:
    thread.join()

for thread in closing_threads:
    thread.join()

for c in clients:
    c.ps.sendline(b'EXIT')
