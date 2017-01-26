import socket
import sys

def main(argv):
	cf = open("config.cfg", 'r')
	tmp_line = cf.readline()
	server_num = int(tmp_line.split()[1])
	
	for i in xrange(server_num):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		tmp_line = cf.readline()
		HOST, PORT = tmp_line.split()
		if HOST == "localhost":
			HOST = socket.gethostname()
		
		s.connect((HOST, int(PORT)))
		print(s.recv(1024))
		s.send("0")
		s.close()
	
	cf.close()

if __name__=="__main__":
	main(sys.argv)
