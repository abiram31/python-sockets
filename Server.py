#!/usr/bin/python3
#==============================================================================
 #   Assignment:  Milestone 3
 #
 #       Author:  Abiram Kaimathuruthy
 #     Language:  Python
 #   To Compile:  n/a
 #
 #        Class:  DPI912
 #    Professor:  Prof. Kaduri
 #     Due Date:  2019-10-10
 #    Submitted:  2019-10-11
 #
 #-----------------------------------------------------------------------------
 #
 #  Description:  Double forks a Daemon, and concurrently accept connections from clients and send lottery tickets
 #
 #        Input:  N/A
 #
 #       Output:  Saves errors, and when a daemon starts and ends to a file.
 #
 #    Algorithm:  Double fork a daemon and for every incoming connection, fork off a child to handle requests and send lottery tickets
 #
 #   Required Features Not Included:  n/a
 #
 #   Known Bugs:  n/a
 #
 #   Classification: A
 #
#==============================================================================

import os
from socket import *
import signal
from signal import  SIGPIPE,  SIG_DFL
import errno
import random
import sys 
import logzero
from logzero import logger
SERVER_ADDRESS = (HOST, PORT  ) = '::1',  8888
QUEUE_SIZE = 1024
# Harvests any zombie children that are left over
def grim_reaper(signum,  frame):
    while True:
        try:
            pid,  status = os.waitpid(-1,  os.WNOHANG)
        except OSError:
            return
# Function to handle client connections, recieves client request and sends the tickets
def handle_client(clientConnection):
    # Recieves lottery name and amount
    lotto, amount= [i for i in clientConnection.recv(2048).decode('utf-8').split('\n')]
    
    lottonum = set()                    #initializes a set to hold all the lotto numbers
    string = ''          
    if (lotto == 'LottoMax'):                       
        for i in range(0,  int(amount)):            
            while(len(lottonum) != 7):                         # loops until there are 7 numbers in the set
                lottonum.add(random.randint(1, 50))     # adds a random number from 1 to 50 in the set
            for j in lottonum:                                         # loops through the set and concatanates string
                string+= str(j)      + " "        
            string += "\n"
            lottonum.clear()                                           # clears the set to hold the next set of lotto numbers
        clientConnection.send( string.encode())   
    elif (lotto == 'Lotto649'):                           
        for i in range(0,  int(amount)):            
            while(len(lottonum) != 6):                         
                lottonum.add(random.randint(1, 49))
            for j in lottonum:                                            
                string += str(j)      + " "        
            string += "\n"
            lottonum.clear()                                           # clears the set to hold the next set of lotto numbers
        clientConnection.send( string.encode())   
    elif (lotto == 'DailyGrand'):       #Checks if the lotto_name arguement is DailyGrand 
        for i in range(0,  int(amount)):
            while(len(lottonum) != 5):
                lottonum.add(random.randint(1, 49))
            for j in lottonum:
                string += str(j)      + " "        
            string += "\n"
            lottonum.clear()                                           # clears the set to hold the next set of lotto numbers
        clientConnection.send( string.encode())   
 

def server(pidfile,  *,  stdin='/dev/null',  stdout='/dev/null',  stderr='/dev/null'):
    logzero.logfile("/tmp/Server.log",  maxBytes=1e6, backupCount=3,  disableStderrLogger=True)
    # Check if a pidfile already exists, if it does, throw error, if it doesnt, continue
    if os.path.exists(pidfile):
        logger.error('Already Running')
        
    # start a socket and listen to the socket
    listenSocket= socket(AF_INET6,  SOCK_STREAM)
    listenSocket.setsockopt(SOL_SOCKET,  SO_REUSEPORT,  1)
    listenSocket.bind(SERVER_ADDRESS)
    listenSocket.listen(QUEUE_SIZE)
    # Kill zombie children process
    signal.signal(signal.SIGCHLD, grim_reaper )
    signal.signal(SIGPIPE,  SIG_DFL)
    # Fork once
    try: 
        if os.fork() > 0:
            raise SystemExit(0)
    except OSError as e: 
        logger.error("Fork #1 failed:" + e)
    
    
    # change current directory. session id and file permissions
    os.chdir("/tmp") 
    os.setsid() 
    os.umask(0) 
    # try setuid and setgid
    try:
        os.setuid(os.getuid())
        os.setgid(os.getgid())
    except Exception as err:
        logger.info("Error: " + err)
    #Fork a second time
    try:
        if os.fork() >0:
            raise SystemExit(0)
    except OSError as e:
        raise RuntimeError('fork #1 failed:' + e)
    #Write the pid of the process to a file
    f = open(pidfile, "w+") 
    f.write(str(os.getpid()))
    f.close()
    # Flush out I/O buffers
    sys.stdout.flush()
    sys.stderr.flush()
    # Replace file descriptors for stdin, stdout and stderr
    with open(stdin,  'rb',  0) as f:
        os.dup2(f.fileno(),  sys.stdin.fileno())
    with open(stdout,  'ab',  0) as f:
        os.dup2(f.fileno(),  sys.stdout.fileno())
    with open(stderr,  'ab',  0) as f:
        os.dup2(f.fileno(),  sys.stderr.fileno())
    # Remove Pid File once the daemon stops
    def removePidFile(signum,  frame):
        os.remove(pidfile)
    try:
        signal.signal(signal.SIGTERM,  removePidFile)
    except Exception :
        raise RuntimeError("ERROR")
    # Accept connections and fork off children to handle connection requests
    while True:
        try:
            clientConnection, clientAddress=listenSocket.accept()
        except IOError as e:
            code,  msg = e.args
            if code == errno.EINTR:
                continue
            else:
                raise
        childPid = os.fork()
        if childPid==0:
                listenSocket.close()
                handle_client(clientConnection)
                clientConnection.close()
                os._exit(0)
                
        else:
            clientConnection.close()
        
    def sigterm_handler(signo,  frame):
        raise SystemExit(1)
    
    signal.signal(signal.SIGTERM,  sigterm_handler)
    
    
# Run the server in main
if __name__ == '__main__':
    PIDFILE = '/tmp/PidFile'
    logzero.logfile("/tmp/Server.log",  maxBytes=1e6, backupCount=3,  disableStderrLogger=True)
    if len(sys.argv) < 2:
        logger.info("usage: {} [start|stop]".format(sys.argv(0)))
        raise SystemExit(1)
    if sys.argv[1] == 'start':
        logger.info('Deamon Started')
        server(PIDFILE,  stdout='Server.log',  stderr='Server.log')
    elif sys.argv[1] == 'stop':
        logger.info('Deamon Stopped')
        if os.path.exists(PIDFILE):
            with open(PIDFILE) as f:
                os.kill(int(f.read()),  signal.SIGTERM)
        else:
            logger.info("Daemon already running")
            raise SystemExit(1)
    else:
        logger.error("Unknown command")
        raise SystemExit(1)
