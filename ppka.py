# Import modules needed for script
import pexpect
import getpass
import sys

#TFTP server name, use either IP address or hostname if resolvable
tftphost = 'myTFTPserver.local'

#TFTP has no directory content listing function, so each public key's file name must be listed here.
managerkeys = ('my_key.pub', 'coworker_key.pub')
operatorkeys = ('backupserver_pub.key', 'auditserver_key.pub')

# Create a dictionary to store all the devices and attributes
devices = {}

# Set Switches Attributes and place them in the devices dictionary.
devices[('NYCoreSW-01')] = 'NYCoreSW-01', 'manager', '172.16.1.2', '.*\w+[\w\)]#'
devices[('ATLCoreSW-01')] = 'ATLCoreSW-01', 'manager', '172.16.2.2', '.*\w+[\w\)]#'
devices[('CHICoreSW-01')] = 'CHICoreSW-01', 'manager', '172.16.3.2', '.*\w+[\w\)]#'
devices[('LACoreSW-01')] = 'LACoreSW-01', 'manager', '172.16.4.2', '.*\w+[\w\)]#'
devices[('SEACoreSW-01')] = 'SEACoreSW-01', 'manager', '172.16.5.2', '.*\w+[\w\)]#'

### Definitions ###
  
# Open Switch connections
def switch_connect(d):
    #Setup the connection
    s = pexpect.spawn(('ssh %s@%s' % (d[1], d[2])))
    #Expect 3 different results from the connection attempt
    login_result = s.expect(['.*Are you sure you want to continue connecting','.*assword: ','Press any key to continue'])
    #Add SSH Keys to known hosts file if this is the first time connecting. 
    if login_result == 0:
        s.sendline('yes')
    #Send password  
    elif login_result == 1:
        p = getpass.getpass('\nPlease enter the password for %s: ' % (d[0]))
        s.sendline(p)
    #If we already have keys installed on the switch then send a return key to bypass the MOTD  
    elif login_result == 2:
        s.send('\r')
    else:
        sys.exit()
    #Repeat passowrd entry until password is correct  
    login_result = s.expect(['Press any key to continue', '.*assword:', d[3]])
    while login_result == 1:
        p = getpass.getpass('\nPlease enter the correct password for %s: ' % (d[0]))
        s.sendline(p)
        login_result = s.expect(['Press any key to continue', '.*assword: '])						
    s.send('\r')
    s.expect(d[3])
    #Enable configuration mode
    s.sendline('conf')
    s.expect(d[3])
    return s;

# Close Switch connections
def switch_close(d,s):
    s.expect(d[3])
    #Save the config
    s.sendline('wr mem')
    s.expect(d[3])
    #Close the connection to the switch
    s.close()

### Add Keys by looping through devices###
  
for d in devices.values():
  s = switch_connect(d)
  #Revoke existing manager keys
  s.sendline('clear crypto client-public-key manager')
  s.expect('continue [y/n]?')
  s.sendline('y')
  s.expect(d[3])
  #Revoke existing operator keys
  s.sendline('clear crypto client-public-key operator')
  s.expect('continue [y/n]?')
  s.sendline('y')
  s.expect(d[3])
  #Keys can only be uploaded via TFTP, eliminate the next 2 lines if not using SCP for file transfers
  s.sendline('no ip ssh filetransfer')
  s.expect(d[3])
  #Allow public key authentication for SSH  
  s.sendline('aaa authentication ssh login public-key none')
  s.expect(d[3])
  #Enable TFTP client
  s.sendline('tftp client')
  s.expect(d[3])
  #Download manager keys from the TFTP server and install them
  for managerkey in managerkeys:
    s.sendline('copy tftp pub-key-file %s %s manager append' % (tftphost, managerkey))
    s.expect(d[3])
  #Download operator keys from the TFTP server and install them              
  for operatorkey in operatorkeys:
    s.sendline('copy tftp pub-key-file %s %s operator append' % (tftphost, operatorkey))
    s.expect(d[3])  
  s.sendline('ip ssh filetransfer')              
  switch_close(d,s)               
  #Let us know which switches have completed
  
  print ('%s complete.' % (d[0]))
print 'Script Complete'
