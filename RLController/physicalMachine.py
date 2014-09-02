import time
import json

class Instance:
  def __init__(self, id, cpu = 0.0, mem = 1.0, rmem = 0.25, failed = False, pm = None):
    self.id = id
    self.cpu = cpu
    self.mem = mem
    self.rmem = rmem
    self.failed = failed 
    self.pm = pm

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
    self.pm.mem -= self.rmem + 0.25
    self.cpu = 0.0
    self.rmem = 0.25
    self.failed = False

  def setByReqrate(self, rate):
    c0 ,m0 = self.cpu, self.rmem
    if rate < 20 * self.mem:
      if rate * 0.05 > self.rmem:
	if self.rmem * 2 <= self.mem:
          self.rmem *= 2
	else:
          self.rmem = self.mem
      	  self.failed = True
    else:
      self.rmem = self.mem
      self.failed = True
    
    self.cpu = 0.1 * rate
    if self.cpu > 2:
      self.cpu = 2
      self.failed = True
    
    self.pm.cpu += self.cpu - c0
    print self.cpu,c0
    self.pm.mem += self.rmem - m0

class PhysicalMachine:
  def __init__(self, id):
    self.id = id
    self.cpu = 0.0
    self.mem = 0.0
    self.instances = {}

  def addInstance(self, ins):
    if self.cpu + ins.cpu <= 100 and self.mem + ins.rmem <= 100 and len(self.instances) <50:
      #self.cpu += ins.cpu
      ins.pm = self
      self.mem += ins.rmem
      self.instances[ins.id] = ins
    else:
      print('add instance failed!')

  def enlargeInstance(self, insid, dmem):
    if self.instances.has_key(insid):
      self.instances[insid].addMem(dmem)

  def decInstance(self, insid):
    if self.instances.has_key(insid):
      ins = self.instances[insid]
      c, m = ins.cpu, ins.rmem
      self.cpu -= c
      self.mem -= m
      del self.instances[insid]

  def shrinkInstance(self, insid, dmem):
    if self.instances.has_key(insid):
      self.instances[insid].addMem(0 - dmem)
      
  def listInstances(self):
    return self.instances.keys()
  
  def getInstance(self, insid):
    return self.instances[insid]

  def getState(self):
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
    
    return (a,b,c)

  def writeToFile(self):
    name = 'vm_' + str(self.id) + '.info'
    outfile = open(name, 'w')
    data = {}
    data['id'] = self.id
    data['cpu'] = self.cpu
    data['mem'] = self.mem
    inss = []
    for insid in self.instances.keys():
      ins = self.instances[insid]
      inss.append((insid, ins.cpu, ins.mem, ins.rmem, ins.failed))
    data['instances'] = inss
    outfile.write(json.dumps(data))
    outfile.close()

  def readFromFile(self):
    name = 'vm_' + str(self.id) + '.info'
    infile = open(name, 'r')
    strs = infile.read()
    infile.close()
    data = json.loads(strs)
    self.cpu = data['cpu']
    self.mem = data['mem']
    for id, cpu, mem, rmem, failed in data['instances']:
      self.instances[id] = Instance(id, cpu, mem, rmem, failed, self)

class PlatformController:
  def __init__(self):
    pass

  def add(self, ins):
    pass

  def dec(self, insid):
    pass
