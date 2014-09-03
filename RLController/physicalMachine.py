import multiprocessing
import time
import json
import os

class Instance:
  def __init__(self, id, cpu = 0.0, mem = 1.0, rmem = 0.25, failed = False, pm = None, dup = 1):
    self.id = id
    self.cpu = cpu  #single instance (not all dups)
    self.mem = mem
    self.rmem = rmem
    self.failed = failed 
    self.pm = pm
    self.dup = dup

  def addMem(self, dmem):
    tmp = self.mem + dmem
    if tmp >= 0.25 and tmp <= 2:
      self.mem = tmp
      self.reset()
    else:
      print "illegal addMem!"

  def isFailed(self):
    return self.failed

  def reset(self):
    self.pm.cpu -= self.cpu
    self.pm.mem = self.pm.mem - self.rmem + 0.25
    self.cpu = 0.0
    self.rmem = 0.25
    self.failed = False

  def setByReqrate(self, rate):
    rate = 1.0 * rate / self.dup
    c0 ,m0 = self.cpu, self.rmem
    tmp = rate * 0.05
    if tmp > m0:
      if tmp <= self.mem:
        self.rmem = tmp
      else:
        self.rmem = self.mem
        self.failed = True
    
    self.cpu = 0.1 * rate
    if self.cpu > 2:
      self.cpu = 2
      self.failed = True
    
    self.pm.cpu += (self.cpu - c0) * self.dup
    self.pm.mem += (self.rmem - m0) * self.dup
    if self.pm.cpu > 100:
      print 'cpu error'
      self.pm.cpu = 100
    if self.pm.mem > 100:
      print 'mem error'
      self.pm.mem = 100
    #print self.cpu,c0,self.rmem,m0

class PhysicalMachine:
  def __init__(self, id, lock):
    self.id = id
    self.cpu = 0.0
    self.mem = 0.0
    self.instances = {}
    self.lock = lock
  '''
  def modifyCpu(self, diff):
    self.readFromFile()
    tmp = self.cpu + diff
    if tmp >=0 and tmp <= 100: 
      self.cpu = tmp
      self.writeToFile()

  def modifyMem(self, diff):
    self.readFromFile()
    tmp = self.mem + diff
    if tmp >=0 and tmp <= 100: 
      self.mem = tmp
      self.writeToFile()
  '''
  def addInstance(self, insid):
    self.readFromFile()
    if self.instances.has_key(insid):
      ins = self.instances[insid]
      if self.cpu + ins.cpu <= 100 and self.mem + ins.rmem <= 100:
        self.cpu -= ins.cpu
        ins.cpu = 0 # cpu clear
        self.mem += ins.rmem
        ins.dup += 1
        ins.failed = False
      else:
        print self.id, 'add instance failed!'
        return False
    else:
      ins = Instance(insid)
      if self.cpu + ins.cpu <= 100 and self.mem + ins.rmem <= 100:
        ins.pm = self
        self.instances[ins.id] = ins
        self.mem += ins.rmem
      else:
        print self.id, 'add instance failed!'
        return False
    self.writeToFile()
    return True

  def enlargeInstance(self, insid, dmem):
    self.readFromFile()
    if self.instances.has_key(insid):
      self.instances[insid].addMem(dmem)
      self.writeToFile()

  def decInstance(self, insid):
    self.readFromFile()
    if self.instances.has_key(insid):
      ins = self.instances[insid]
      ins.dup -= 1
      c, m = ins.cpu, ins.rmem
      self.cpu -= c
      self.mem -= m
      if ins.dup == 0:
        del self.instances[insid]
      self.writeToFile()
      return True
    return False

  def shrinkInstance(self, insid, dmem):
    self.readFromFile()
    if self.instances.has_key(insid):
      self.instances[insid].addMem(0 - dmem)
      self.writeToFile()
      
  def listInstances(self):
    self.readFromFile()
    return self.instances.keys()
  
  def getInstance(self, insid):
    self.readFromFile()
    return self.instances[insid]

  def getState(self):
    self.readFromFile()
    n = 0
    for id in self.instances.keys():
      ins = self.instances[id]
      if ins.isFailed(): n += 1
    if self.cpu < 20:
      a = 0
    elif self.cpu <80:
      a = 1
    else:
      a = 2
    if self.mem < 20:
      b = 0
    elif self.mem <80:
      b = 1
    else:
      b = 2
    if n == 0:
      c = 0
    elif n < 5:
      c = 1
    elif n <25:
      c = 2
    else:
      c = 3
    #print (self.cpu,self.mem), (a,b,c) 
    return (a,b,c)

  def writeToFile(self):
    self.lock.acquire()
    #print multiprocessing.current_process(), 'A', self.id
    name = 'vm_' + str(self.id) + '.info'
    outfile = open(name, 'w')
    data = {}
    data['id'] = self.id
    data['cpu'] = self.cpu
    data['mem'] = self.mem
    inss = []
    for insid in self.instances.keys():
      ins = self.instances[insid]
      inss.append((insid, ins.cpu, ins.mem, ins.rmem, ins.failed, ins.dup))
    data['instances'] = inss
    try:
      strs = json.dumps(data)
    except:
      print "!!!!", data
    else:
      outfile.write(strs)
      return strs
    finally:
      outfile.close()
      #print multiprocessing.current_process(), 'R', self.id
      self.lock.release()

  def readFromFile(self):
    self.lock.acquire()
    #print multiprocessing.current_process(), 'A', self.id
    name = 'vm_' + str(self.id) + '.info'
    infile = open(name, 'r')
    strs = infile.read()
    infile.close()
    if not strs:
      #print "???", self.id
      #print multiprocessing.current_process(), 'B', self.id
      self.lock.release()
      return 
    try:
      data = json.loads(strs)
    except:
      print "#################", strs
      #print multiprocessing.current_process(), 'B', self.id
      self.lock.release()
      return
    self.cpu = data['cpu']
    self.mem = data['mem']
    self.instances = {}
    for id, cpu, mem, rmem, failed, dup in data['instances']:
      self.instances[id] = Instance(id, cpu, mem, rmem, failed, self, dup)
    #print multiprocessing.current_process(), 'B', self.id
    self.lock.release()
    return strs

class PlatformController:
  def __init__(self, pmNum, locks, pllock):
    self.pmNum = pmNum
    self.pms = []
    self.locks = locks
    self.pllock = pllock
  
  def load(self):
    self.pms = []
    for i in range(self.pmNum):
      pm = PhysicalMachine(i, self.locks[i])
      if not pm.readFromFile():
        print "AAA", pm.id
        time.sleep(60)
      self.pms.append(pm)

  def add(self, ins):
    self.pllock.acquire()
    self.load()
    self.pms.sort(key = lambda pm : pm.mem)
    for pm in self.pms:
      #print pm.id, pm.mem
      if pm.addInstance(ins.id):
        self.pllock.release()
        return True
    self.pllock.release()
    return False

  def dec(self, insid):
    #print multiprocessing.current_process(), 'wanto Al', self.pllock
    self.pllock.acquire()
    #print multiprocessing.current_process(), 'Al', self.pllock
    n = 0
    self.load()
    for pm in self.pms:
      if pm.instances.has_key(insid):
        n += pm.instances[insid].dup
    print '~~~~~~',insid, n
    if n > 1:
      self.pms.sort(key = lambda pm : pm.mem, reverse = True)
      for pm in self.pms:
        if pm.decInstance(insid):
          print "successs dec", pm.id, insid,pm.cpu,pm.mem
          #print multiprocessing.current_process(), 'Bl', self.pllock
          self.pllock.release()
          return True
      #print multiprocessing.current_process(), 'Bl', self.pllock
    self.pllock.release()
    return False
