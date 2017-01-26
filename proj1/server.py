import socket
import select
import sys
import time
import thread
import operator

def broadcast_release( request_released, lamport_id, ticket_num, peer_server, success ):
	release_delay = 2
	time.sleep(release_delay)
	
	for cs_info in peer_server:
		cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		cs.connect(cs_info)
		cs.recv(1024)
		cs.send("1 " + str(request_released[0]) + " " +  lamport_id + " release " + str(request_released[1]) + " " + str(ticket_num) + " " + str(success))
		cs.close()

def broadcast_request( sind, lamport_id, ticket_num, peer_server ):
	request_delay = 2
	time.sleep(request_delay)
	
	for cs_info in peer_server:
		cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		cs.connect(cs_info)
		cs.recv(1024)
		cs.send("1 " + sind + " " + lamport_id + " request " + str(ticket_num))
		cs.close()
	
def send_reply( sind, lamport_id, receive_server ):
	reply_delay = 2
	time.sleep(reply_delay)
	
	cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	cs.connect(receive_server)
	cs.recv(1024)
	cs.send("1 " + sind + " " + lamport_id + " reply")
	cs.close()

def main(argv):
	script_name, sind = argv
	total_amount = 5
	
	log_file_name = "log/server-" + sind + ".log"
	log_file = open(log_file_name, 'w')

	cf = open("config.cfg", 'r')
	tmp_line = cf.readline()
	server_num = int(tmp_line.split()[1])
	
	peer_server = list()
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	for i in xrange(server_num):
		tmp_line = cf.readline()
		HOST, PORT = tmp_line.split()
		if HOST == "localhost":
			HOST = socket.gethostname()
		
		if i == int(sind) - 1:
			s.bind((HOST, int(PORT)))
		else:
			peer_server.append((HOST, int(PORT)))

	cf.close()			# CLOSE config file
	
	s.listen(5)
	log_file.write("\nServer Started\n")

	client_conn = []
	request_list = list()
	reply_count = 0
	lamport_id = 0

	while True:
		c, addr = s.accept()
		log_file.write("\nGot connection from" + str(addr))
		c.send("\nYou are connecting with server" + sind)
		
		lamport_id += 1
		
		msg = c.recv(1024)
		msg_seq = msg.split()
		conn_id = msg_seq[0] 
		log_file.write(msg)
		if int(conn_id) == 0:
			if len(client_conn) > 0:
				client_conn[0].close()
			c.close()
			break

		if int(conn_id) == 1:
			peer_server_ind = int(msg_seq[1])
			peer_server_lamport = int(msg_seq[2])

			if peer_server_lamport + 1 > lamport_id:
				lamport_id = peer_server_lamport + 1

			log_file.write("\nReceived msg from " + str(addr) + ": " + str(peer_server_ind) + "~" + str(peer_server_lamport))

			if msg_seq[3] == "request":
				log_file.write("\n[ Request ] Received from " + str(addr) + ": " + msg_seq[4])
				
				request_list.append((peer_server_ind, peer_server_lamport, int(msg_seq[4])))
				request_list = sorted(request_list, key=operator.itemgetter(1, 0))

				peer_server_stat = peer_server[0]
				if peer_server_ind > int(sind):
					peer_server_stat = peer_server[peer_server_ind - 2];
				else:
					peer_server_stat = peer_server[peer_server_ind - 1];

				try:
					thread.start_new_thread( send_reply, (sind, str(lamport_id), peer_server_stat) )
				except:
					log_file.write("\n\nError: Cannot reply! ")

			elif msg_seq[3] == "reply":
				log_file.write("\n[ Reply ] Received from " + str(addr) + ": " + str(peer_server_ind))
				reply_count += 1
				
				if len(request_list) > 0 and reply_count == len(peer_server) and request_list[0][0] == int(sind):
					log_file.write("\n[ Start Process ] Received all replies:")
					
					if total_amount >= request_list[0][2]:
						log_file.write("\n[ Success ] Previous Total: " + str(total_amount) + " ;Sale " + str(request_list[0][2]) + " tickets!")
						total_amount -= request_list[0][2]
						try:
							thread.start_new_thread( broadcast_release, (request_list[0], str(lamport_id), request_list[0][2], peer_server, 1) )
						except:
							log_file.write("\n\nError: Cannot broadcast releases!")
						client_conn[0].send("You successfully bought " + str(request_list[0][2]) + " ticket(s).\nThank you!\n")
						client_conn[0].close()
						client_conn.pop(0)
						reply_count = 0
						request_list.pop(0)
					else:
						log_file.write("\n[ Fail ] Previous Total: " + str(total_amount) + " ;Request " + str(request_list[0][2]) + " tickets!")
						try:
							thread.start_new_thread( broadcast_release, (request_list[0], str(lamport_id), request_list[0][2], peer_server, 0))
						except:
							log_file.write("\n\nError: Cannot broadcaset releases!")
						client_conn[0].send("Remaining tickets are " + str(total_amount) + ", so your request cannot be completed.\nSorry\n")
						client_conn[0].close()
						client_conn.pop(0)
						reply_count = 0
						request_list.pop(0)

			elif msg_seq[3] == "release":
				log_file.write("\n[ Release ] Received from " + str(addr) + ": " + str(peer_server_ind))

				request_list.remove((peer_server_ind, int(msg_seq[4]), int(msg_seq[5])))

				if int(msg_seq[6]) == 1:
					total_amount -= int(msg_seq[5])

				log_file.write("\n[ Release ] Release one request: (" + str(peer_server_ind) + " " + msg_seq[4] + " " + msg_seq[5] + ")" + " Success: " + msg_seq[6])
				if len(request_list) > 0:
					log_file.write("\n[ Release ] Next request is (" + str(request_list[0][0]) + " " + str(request_list[0][1]) + " " + str(request_list[0][2]) + ")")

				if len(request_list) > 0 and reply_count == len(peer_server) and request_list[0][0] == int(sind):
					log_file.write("\n[ Start Process ] Received all replies:")
					
					if total_amount >= request_list[0][2]:
						log_file.write("\n[ Success ] Previous Total: " + str(total_amount) + " ;Sale " + str(request_list[0][2]) + " tickets!")
						total_amount -= request_list[0][2]
						try:
							thread.start_new_thread( broadcast_release, (request_list[0], str(lamport_id), request_list[0][2], peer_server, 1) )
						except:
							log_file.write("\n\nError: Cannot broadcast releases!")
						client_conn[0].send("You successfully bought " + str(request_list[0][2]) + " ticket(s).\nThank you!\n")
						client_conn[0].close()
						client_conn.pop(0)
						reply_count = 0
						request_list.pop(0)
					else:
						log_file.write("\n[ Fail ] Previous Total: " + str(total_amount) + " ;Request " + str(request_list[0][2]) + " tickets!")
						try:
							thread.start_new_thread( broadcast_release, (request_list[0], str(lamport_id), request_list[0][2], peer_server, 0))
						except:
							log_file.write("\n\nError: Cannot broadcaset releases!")
						client_conn[0].send("Remaining tickets are " + str(total_amount) + ", so your request cannot be completed.\nSorry\n")
						client_conn[0].close()
						client_conn.pop(0)
						reply_count = 0
						request_list.pop(0)
				
			else:
				log_file.write("\n[ ERROR ] Unrecognized message from " + str(addr) + ": " + str(peer_server_ind))
				

			c.close()
		else:
			if len(client_conn) > 0:
				c.close()
				continue

			reply_count = 0
			buy_msg = msg_seq[1] 
			client_conn.append(c)
			
			request_list.append((int(sind), lamport_id, int(buy_msg)))
			request_list = sorted(request_list, key=operator.itemgetter(1, 0))
			try:
				thread.start_new_thread( broadcast_request, (sind, str(lamport_id), int(buy_msg), peer_server) )
			except:
				log_file.write("\n\nError: Cannot broadcast request!")
			
	s.close()

	log_file.write("\n\nServer Shutted Down!\n")
	log_file.close()
	print("\nServer " + sind + " existing..")

if __name__=="__main__":
	main(sys.argv)
