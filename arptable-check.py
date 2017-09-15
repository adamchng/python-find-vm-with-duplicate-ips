#!/bin/python

# adam 20170907 script to check and match any duplicate IP address with different MAC address and send out email alert

import MySQLdb
import subprocess
import re
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

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
  body = ''

  for ln in out:
    #print (ln)

    if ln:
      line = ln.split('"', 1)
      
      arpip = ip_process(line[0])
      mac = mac_process(line[1])

      # check if exists - mac needs to be the same, then update the row
      sql = "SELECT MAC, LAST_UPDATED FROM ARPTABLE WHERE IP = INET_ATON('%s')" % arpip
      cursor.execute(sql)
      #print(sql)
      mac_tbl = cursor.fetchone()
      #print(mac_tbl)

      if mac_tbl:
        # check to see if IP address has changed
        if mac_tbl[0] != mac:

          if mac_tbl[0][:-3] == mac[:-3]:
            body += "Same server, probably safe to ignore: %s (current mac: %s) is different from previously recorded (previous: %s on %s).\n" % (arpip, mac, mac_tbl[0], mac_tbl[1]) 
          else:
            body += "ALERT: %s (current mac: %s) is different from previously recorded (previous: %s on %s).\n" % (arpip, mac, mac_tbl[0], mac_tbl[1]) 

            sql = "SELECT VM_FILE,INET_NTOA(ESX_IP) AS ESX FROM VMMAC WHERE MAC = '%s'" % mac_tbl[0]
            cursor.execute(sql)
            info = cursor.fetchone()
            #print (sql)
            #print(info)
            if info:
              body += "\tPrevious %s (mac: %s) is assigned to %s on ESX %s \n\n" % (arpip, mac_tbl[0], info[0], info[1])
            else:
              body += "\tPrevious %s (mac: %s) seems like a physical server \n\n" % (arpip, mac_tbl[0])
     
  # send email if there is something 
  if body != '':
    fromaddr = "from@email.com"
    toaddr = "to@email.com"
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Alert: Duplicate IP detected"
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('localhost')
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()


# open file and parse all the IPs
with open("/etc/file/routers") as f:
  r = f.read().splitlines()

for x in r:
  if x != '[all]':
    if x[0:1] != '#':
      print "----- Checking Router %s -----" % x
      findmac(x)

db.close()
