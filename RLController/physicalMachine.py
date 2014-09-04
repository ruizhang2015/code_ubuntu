import multiprocessing
import time
import json
import os
#import baeplatform

class Instance:
  def __init__(self, id, cpu = 0.0, mem = 1.0, rmem = 0.25, failed = False, pm = None, dup = 1):
    self.id = id
    self.cpu = cpu  #single instance (not all dups)
    self.mem = mem
    self.rmem = rmem
    self.failed = failed 
    self.pm = pm
    self.dup = dup
  def toStruct(self):
    return [self.id, self.cpu, self.mem, self.rmem, self.failed, self.dup]

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
  def __init__(self, id, lock, q, plinfo):
    self.id = id
    self.cpu = 0.0
    self.mem = 0.0
    self.instances = {}
    self.lock = lock
    self.q = q
    self.plinfo = plinfo
  
  def toStruct(self):
    list = []
    for insid in self.instances.keys():
      list.append(self.instances[insid].toStruct())
    return [self.id, self.cpu, self.mem, list]
  
  def structTo(self, pm):
    self.cpu = pm[1]
    self.mem = pm[2]
    list = pm[3]
    self.instances = {}
    for ins in list:
      self.instances[ins[0]] = Instance(ins[0], ins[1], ins[2], ins[3],ins[4], self, ins[5])

  def store(self):
    list = []
    while not self.plinfo.empty():
      pm = self.plinfo.get()
      if pm[0] == self.id:
        break
      list.append(pm)
    pm = self.toStruct()
    list.append(pm)
    #print 'store:', pm
    for pm in list:
      self.plinfo.put(pm)
      print 'put secc'

  def load(self):
    for _ in range(3):
      if self.plinfo.empty():
        time.sleep(0.1)
      else:
        break
    list = []
    while not self.plinfo.empty():
      pm = self.plinfo.get()
      list.append(pm)
      if pm[0] == self.id:
        self.structTo(pm)
        break
    for pm in list:
      self.plinfo.put(pm)
      time.sleep(0.5)
    print 'load: none'
    

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
    #self.readFromFile()
    print
    print "BEGIN ", insid
    self.load()
    if self.instances.has_key(insid):
      print '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
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
    print self.id, insid,'add instance suc!'
    self.q[insid] += 1
    print "add, insid, q", insid, self.q[insid]
    #self.writeToFile()
    self.store()
    return True

  def enlargeInstance(self, insid, dmem):
    #self.readFromFile()
    self.load()
    if self.instances.has_key(insid):
      self.instances[insid].addMem(dmem)
      self.writeToFile()

  def decInstance(self, insid):
    #self.readFromFile()
    self.load()
    if self.instances.has_key(insid):
      ins = self.instances[insid]
      ins.dup -= 1
      c, m = ins.cpu, ins.rmem
      self.cpu -= c
      self.mem -= m
      if ins.dup == 0:
        del self.instances[insid]
      self.q[insid] -= 1
      print "dec, insid, q", insid, self.q[insid]
      #self.writeToFile()
      self.store()
      return True
    return False

  def shrinkInstance(self, insid, dmem):
    #self.readFromFile()
    self.load()
    if self.instances.has_key(insid):
      self.instances[insid].addMem(0 - dmem)
      self.writeToFile()
      
  def listInstances(self):
    #self.readFromFile()
    self.load()
    return self.instances.keys()
  
  def getInstance(self, insid):
    #self.readFromFile()
    self.load()
    return self.instances[insid]

  def getState(self):
    #self.readFromFile()
    self.load()
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
    print (self.id,self.cpu,self.mem), (a,b,c) 
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
  def __init__(self, pmNum, locks, pllock, q, plinfo):
    self.pmNum = pmNum
    self.pms = []
    self.locks = locks
    self.pllock = pllock
    self.q = q
    self.plinfo = plinfo
  
  def load(self):
    self.pms = []
    for i in range(self.pmNum):
      pm = PhysicalMachine(i, self.locks[i],self.q, self.plinfo)
      #if not pm.readFromFile():
        #print "AAA", pm.id
        #time.sleep(60)
      pm.load()
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
