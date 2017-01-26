import socket
import sys

scriptName, port = sys.argv

s = socket.socket()
host = socket.gethostname()

s.connect((host, int(port)))
print(s.recv(1024))
s.send("2 1")
print(s.recv(1024))
s.close()

