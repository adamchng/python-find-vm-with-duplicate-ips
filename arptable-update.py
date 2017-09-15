#!/bin/python

# adam 20170907 script to get core routers's arp table and store them in a mysql table

import MySQLdb
import subprocess
import re

# connect to mysql db first
db = MySQLdb.connect(host= "hostname",user="root",passwd="password",db="db")
cursor = db.cursor()

def ip_process(s):
  ip = s.split('.', 7)
  return ip[7].strip()

def mac_process(s):
  mac = s[:-2].strip()
  return re.sub(' ',':',mac).lower()

# main function
def findmac(ip):
  out = subprocess.check_output("/bin/snmpbulkwalk -v 2c -c xxx123 -OXsq %s .1.3.6.1.2.1.3.1.1.2 || true" % (ip), stderr=subprocess.STDOUT, shell=True)
  out = out.split("\n")
  #print (out)

  for ln in out:
    #print (ln)

    if ln:
      line = ln.split('"', 1)
      
      arpip = ip_process(line[0])
      mac = mac_process(line[1])

      # check if exists - mac needs to be the same, then update the row
      sql = "SELECT MAC FROM ARPTABLE WHERE MAC = '%s'" % mac
      cursor.execute(sql)
      mac_tbl = cursor.fetchone()

      if mac_tbl:
        sql = "UPDATE ARPTABLE SET IP = INET_ATON('%s'), HOST_ROUTER = INET_ATON('%s'), LAST_UPDATED = now() WHERE MAC = '%s'" % (arpip, ip, mac)
        print "Updated %s for %s" % (mac, arpip)
      else:
        sql = "INSERT INTO ARPTABLE (MAC, IP, HOST_ROUTER, LAST_UPDATED) VALUES ('%s',INET_ATON('%s'),INET_ATON('%s'),now())" % (mac,arpip,ip)
        print "Inserted %s for %s" % (mac, arpip)

      cursor.execute(sql)
      db.commit()


# open file and parse all the IPs
with open("/etc/file/routers") as f:
  r = f.read().splitlines()

for x in r:
  if x != '[all]':
    if x[0:1] != '#':
      print "----- Starting Router %s -----" % x
      findmac(x)

db.close()
