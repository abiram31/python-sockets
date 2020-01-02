#!/usr/bin/python3
from socket import *
import argparse
import os
import random
import logzero
from logzero import logger
SERVER_ADDRESS = (HOST, PORT  ) = '::1',  8888

#Sends requests to Server and recieves the ticket
def client(maxClients,  maxConn):
    os.chdir("/tmp") 
    socks = []
    # Loops for all the clients
    for clientNum in range(maxClients):
        pid = os.fork()
        # forks children to make connections with client
        if pid == 0:
            for connectionNum in range(maxConn):
                sock = socket(AF_INET6,  SOCK_STREAM) 
                sock.connect(SERVER_ADDRESS)
                socks.append(sock)
                tickets = ['LottoMax',  'Lotto649',  'DailyGrand']
                amounts = [1, 2, 3, 4, 5]
                lotto = random.choice(tickets)
                amount = random.choice(amounts)
                sock.sendall(str.encode("\n".join([str(lotto), 
                                                   str(amount)])))
                data = sock.recv(2048)
                msg = data.decode()
                logger.info("For Client " + str(clientNum) + ": "+ msg + "\n")
               
            os._exit(0)     
    for sockets in socks:
        sockets.close()
    #Harvests all the zombie children
    while True:
        try:
            pid,  status = os.waitpid(-1,  os.WNOHANG) 
        except OSError :
            break  
            
   


if __name__ == '__main__':
    logzero.logfile("Client.log",  maxBytes=1e6, backupCount=3,  disableStderrLogger=True)
    parser = argparse.ArgumentParser(
                                     description='Generate Lotto Codes')    #initialize the arguement parser 
    parser.add_argument('--client',   
                        help='name of the lottery tickect', default = 2)     #adds arguement to be parsed
    parser.add_argument('--conn',  
                        type=int,  default= 5,  
                        help='amount of lottery ticket the user wants to purchase')    #adds another optional arguement to be parsed
    args = parser.parse_args()
    client(args.client,  args.conn)
