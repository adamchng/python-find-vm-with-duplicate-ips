#!/bin/python

# adam 20170906 script to hit all esx servers and grab MAC address for each VM
# and store them in a mysql table

import MySQLdb
import subprocess
import re

# connect to mysql db first
db = MySQLdb.connect(host= "hostname",user="root",passwd="password",db="db")
cursor = db.cursor()

def macsplit(s):
  a = s.split(' = ')
  return a[1][1:-1]

def vmname_split(s):
  a = s.split('/', 4)
  return a[4]

# main function
def findmac(ip,dstore):
  out = subprocess.check_output("/bin/ssh -l root %s 'ls /vmfs/volumes/%s/*/*.vmx | while read i; do grep -i \"00:0c:\" \"$i\" /dev/null; done' || true" % (ip,dstore), stderr=subprocess.STDOUT, shell=True)
  out = out.split("\n")
  #print (out)

  for ln in out:
    #print (ln)

    if ln:
      line = ln.split(':', 1)
      vm_file = vmname_split(line[0])
      mac = macsplit(line[1])
      #print "%s: %s" % (vm_file,mac)

      # check if exists - mac needs to be the same, then update the row
      sql = "SELECT MAC FROM VMMAC WHERE MAC = '%s'" % mac
      cursor.execute(sql)
      mac_tbl = cursor.fetchone()

      if mac_tbl:
        sql = "UPDATE VMMAC SET VM_FILE = '%s', ESX_IP = INET_ATON('%s'), LAST_UPDATED = now() WHERE MAC = '%s'" % (vm_file, ip, mac)
        print "Updated %s for %s" % (mac, vm_file)
      else:
        sql = "INSERT INTO VMMAC (MAC, VM_FILE, ESX_IP, LAST_UPDATED) VALUES ('%s','%s',INET_ATON('%s'),now())" % (mac, vm_file,ip)
        print "Inserted %s for %s" % (mac, vm_file)

      #print(sql)
      cursor.execute(sql)
      db.commit()



# open file 'esx' and parse all the IPs
with open("/etc/file/esx") as f:
  esxes = f.read().splitlines()

for esx in esxes:
  if esx != '[all]':
    if esx[0:1] != '#':
      print "----- Starting ESX Server %s -----" % esx

	  # check for some servers with unique conditions
      if esx == '172.16.1.57':
        findmac(esx,'datastore1')
        findmac(esx,'datastore2')

      elif (esx == '172.16.1.61' or esx == '172.16.1.62'):
        findmac(esx,'datastore2')

      elif esx == '172.16.1.65':
        findmac(esx,'datastore2')
        findmac(esx,'datastore3')

      else:
        findmac(esx,'datastore1')


db.close()
