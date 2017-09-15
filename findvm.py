#!/bin/python

# adam 20170906 script to hit all esx servers and grab info about the VMs stored in them
# and store them in a table

import MySQLdb
import subprocess
import re

# connect to mysql db first
db = MySQLdb.connect(host= "hostname",user="root",passwd="password",db="db")
cursor = db.cursor()

def RepresentsInt(s):
    return re.match(r"[-+]?\d+$", s) is not None

# main function
def findvms(ip):
  sshcmd = "/bin/ssh -l root " + ip + " 'vim-cmd vmsvc/getallvms' || true"
  out = subprocess.check_output(sshcmd, shell=True)
  out = out.split("\n")
  del out[0]

  for single in out:
    o = single.strip()
    p = o.split()

    #print (p)

    if (p and RepresentsInt(p[0])):

      vmid = p[0]
      vm_name = p[1]
      dstore = p[2]
      vm_file = p[3]

      if dstore == '[datastore1]':
        vm_dstore = 'datastore1'
      elif dstore == '[datastore2]':
        vm_dstore = 'datastore2'
      elif dstore == '[datastore3]':
        vm_dstore = 'datastore3'
      else:
        vm_dstore = p[1:-1]

      matchOS = re.match( r'win', p[4], re.M|re.I)
      if matchOS:
        vm_os = 'windows'
      else:
        vm_os = 'linux'


      # check if exists - esx ip & vmid needs to be the same, then update the row
      sql = "SELECT VMTABLEID FROM VM WHERE ESX_IP = INET_ATON('%s') AND VM_ID = '%s'" % (ip, vmid)
      cursor.execute(sql)
      vmtableid = cursor.fetchone()

      if vmtableid:
        sql = "UPDATE VM SET VM_NAME = '%s', VM_FILE = '%s', OS = '%s', DATASTORE = '%s', LAST_UPDATED = now() WHERE VMTABLEID = '%s'" % (vm_name, vm_file, vm_os, vm_dstore, vmtableid[0])
        print "Updated %s for %s: %s" % (ip, vmid, vm_name)
      else:
        sql = "INSERT INTO VM (ESX_IP, VM_ID, VM_NAME, VM_FILE, OS, DATASTORE, LAST_UPDATED) VALUES (INET_ATON('%s'),'%d','%s','%s','%s','%s',now())" % (ip, int(vmid), vm_name, vm_file, vm_os, vm_dstore)
        print "Inserted %s for %s: %s" % (ip, vmid, vm_name)

      #print (sql)

      cursor.execute(sql)
      db.commit()

      #print "%s %s %s %s %s %s" % (ip, vmid, vm_name,vm_file,vm_dstore,vm_os)
  

# open file 'esx' and parse all the IPs
with open("/etc/file/esx") as f:
  esxes = f.read().splitlines()

for esx in esxes:
  if esx != '[all]':
    if esx[0:1] != '#':
      print "----- Starting ESX Server %s -----" % esx
      findvms(esx)
      #print "----- Completed ESX Server %s -----" % esx

db.close()
