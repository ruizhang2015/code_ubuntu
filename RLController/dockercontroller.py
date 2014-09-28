import multiprocessing
import httplib
import urllib
import time
import json
import os
import logging
import utils

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
  def __init__(self, id):
    self.id = id
    self.cpu = 0.0
    self.mem = 0.0

  def getContainers(self):
    return self.listContainers()

  def getApps(self, pmid):
    apps = {}
    containers = self.listContainers(pmid)
    for ctn in containers:
      img = ctn['Image'].split(':')[0]
      if apps.has_key(img):
        apps[img].append(ctn['Id'])
      else:
        apps[img] = [ctn['Id']]
    return apps
  
  def getContainers(self, pmid):
    ctns = []
    containers = self.listContainers(pmid)
    for ctn in containers:
      ctns.append(ctn['Id'])
    return ctns
  

  def listContainers(self, pmid):
      # online: curl newsch.bce.duapp.com/igroup/getByGid -d '{"vcode":"qew$%^^21i412o3i4u12(*(*(*)(*)*@*)*)*!","gid":"27854"}'
        try:
            #headers = {"Content-Type":"application/json", "Connection":"Keep-Alive"}
            headers = {"Content-Type":"application/x-www-form-urlencoded", "Connection":"Keep-Alive"}
            params = {"all":0}
            conn = httplib.HTTPConnection('192.168.4.'+ str(pmid) + ':4243')
            #conn.request("POST",GET_APPID_URL,urllib.urlencode() json.JSONEncoder().encode(params), headers)
            conn.request("GET",'/containers/json',urllib.urlencode(params), headers)
            response = conn.getresponse()
            if response.status == 200:
                data = json.loads(response.read())
                return data
            else:
                logging.debug(response.read())
        except Exception as e:
            logging.exception('internal error happens: %s' % str(e))
            raise error_code.internal_err
  def createContainer(self, pmid, args):
      # online: curl newsch.bce.duapp.com/igroup/getByGid -d '{"vcode":"qew$%^^21i412o3i4u12(*(*(*)(*)*@*)*)*!","gid":"27854"}'
        try:
            headers = {"Content-Type":"application/json", "Connection":"Keep-Alive"}
            #headers = {"Content-Type":"application/x-www-form-urlencoded", "Connection":"Keep-Alive"}
            img = args['Image']
            params = {"Memory":134217728, "Image":img,"Cmd":args['Cmd']}
            conn = httplib.HTTPConnection('192.168.4.'+ str(pmid) + ':4243')
            #conn.request("POST",GET_APPID_URL,urllib.urlencode() json.JSONEncoder().encode(params), headers)
            conn.request("POST",'/containers/create', json.JSONEncoder().encode(params), headers)
            response = conn.getresponse()
            if response.status == 201:
                params = {"PortBindings":{ "5000/tcp": [{ "HostPort": args['Port'] }] }}
                data = json.loads(response.read())
                conn.request("POST",'/containers/'+ data['Id']+'/start', json.JSONEncoder().encode(params), headers)
                response = conn.getresponse()
                if response.status == 204:
                  return 'CREATE OK'
            print response.read()
        except Exception as e:
            logging.exception('internal error happens: %s' % str(e))
            raise error_code.internal_err
 
  def listImages(self, pmid):
      # online: curl newsch.bce.duapp.com/igroup/getByGid -d '{"vcode":"qew$%^^21i412o3i4u12(*(*(*)(*)*@*)*)*!","gid":"27854"}'
        try:
            #headers = {"Content-Type":"application/json", "Connection":"Keep-Alive"}
            headers = {"Content-Type":"application/x-www-form-urlencoded", "Connection":"Keep-Alive"}
            params = {"all":0}
            conn = httplib.HTTPConnection('192.168.4.'+ str(pmid) + ':4243')
            #conn.request("POST",GET_APPID_URL,urllib.urlencode() json.JSONEncoder().encode(params), headers)
            conn.request("GET",'/images/json',urllib.urlencode(params), headers)
            response = conn.getresponse()
            if response.status == 200:
                data = json.loads(response.read())
                return data
            else:
                logging.debug(response.read())
        except Exception as e:
            logging.exception('internal error happens: %s' % str(e))
            raise error_code.internal_err
  def killContainer(self, pmid, image):
        apps = self.getApps(pmid)
        if len(apps[image]) == 1:
          print 'only one left, cannot delete!'
          return
      # online: curl newsch.bce.duapp.com/igroup/getByGid -d '{"vcode":"qew$%^^21i412o3i4u12(*(*(*)(*)*@*)*)*!","gid":"27854"}'
        try:
            #headers = {"Content-Type":"application/json", "Connection":"Keep-Alive"}
            headers = {"Content-Type":"application/x-www-form-urlencoded", "Connection":"Keep-Alive"}
            conn = httplib.HTTPConnection('192.168.4.'+ str(pmid) + ':4243')
            id = apps[image][-1]
            print id
            #conn.request("POST",GET_APPID_URL,urllib.urlencode() json.JSONEncoder().encode(params), headers)
            conn.request("POST",'/containers/'+ id  +'/kill',None, headers)
            response = conn.getresponse()
            if response.status == 204:
                return 'KILL OK'
            else:
                logging.debug(response.read())
        except Exception as e:
            logging.exception('internal error happens: %s' % str(e))
            raise error_code.internal_err
  def getContainerImage(self,pmid, id):
      # online: curl newsch.bce.duapp.com/igroup/getByGid -d '{"vcode":"qew$%^^21i412o3i4u12(*(*(*)(*)*@*)*)*!","gid":"27854"}'
        try:
            #headers = {"Content-Type":"application/json", "Connection":"Keep-Alive"}
            headers = {"Content-Type":"application/x-www-form-urlencoded", "Connection":"Keep-Alive"}
            #params = {"all":0}
            conn = httplib.HTTPConnection('192.168.4.'+ str(pmid) + ':4243')
            #conn.request("POST",GET_APPID_URL,urllib.urlencode() json.JSONEncoder().encode(params), headers)
            conn.request("GET",'/containers/'+ id  +'/json',None, headers)
            response = conn.getresponse()
            if response.status == 200:
                data = json.loads(response.read())
                return data["Config"]
            else:
                logging.debug(response.read())
        except Exception as e:
            logging.exception('internal error happens: %s' % str(e))
            raise error_code.internal_err

  def getContainerState(self, container): 
        #print (utils.get_file_content_cpu('/proc/stat'))
        CPU_BASE_DIR="/sys/fs/cgroup/cpuacct/docker/"
        p = utils.get_path_by_container(CPU_BASE_DIR, container, 'cpuacct.usage')
        now = time.time()
        value = float(utils.get_file_content(p))

        MEMORY_BASE_DIR="/sys/fs/cgroup/memory/docker/"
        p = utils.get_path_by_container(MEMORY_BASE_DIR, container, 'memory.usage_in_bytes')
        usages = float(utils.get_file_content(p))
        p = utils.get_path_by_container(MEMORY_BASE_DIR, container, 'memory.limit_in_bytes')
        limits = float(utils.get_file_content(p))
        p = utils.get_path_by_container(MEMORY_BASE_DIR, container, 'memory.stat')
        d = utils.get_file_content_kv(p)
        rss = d["rss"]
        cache = d["cache"]

        return {'time': now, 'cpu_usage': value/1e9,'rss': rss, 'cache': cache, 'usage': usages, 'limit': limits}
    

  def getState(self, last):
    cpu = 0
    mem = 0
    tmp = {}
    for ctn in self.getContainers(self.id):
      now =  self.getContainerState(ctn)
      if last and last.has_key(ctn):
        cpu += (now['cpu_usage']-last[ctn]['cpu_usage'])/(now['time']-last[ctn]['time'])
      mem += now['usage']
      tmp[ctn] = now
    print tmp, cpu, mem
    mem /= 39000000000   
    n = 0
    if cpu < 0.4:
      a = 0
    elif cpu < 1.6:
      a = 1
    else:
      a = 2
    if mem < 0.20:
      b = 0
    elif mem < 0.80:
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
    return (a,b,c),tmp

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
      if not pm.readFromFile():
        print "AAA", pm.id
        time.sleep(60)
      #pm.load()
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
    print 'dec insid n',insid, n
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

if __name__ == '__main__':
  ph = PhysicalMachine(202)
  last = {}
  for ctn in ph.getContainers(202):
    last[ctn] =  ph.getContainerState(ctn)
  for _ in range(4):
    for ctn in ph.getContainers(202):
      time.sleep(2)
      now =  ph.getContainerState(ctn)
      print ctn, (now['cpu_usage']-last[ctn]['cpu_usage'])/(now['time']-last[ctn]['time']), now['usage']/now['limit'],
      last[ctn] = now
    print 
  #print ph.getApps(203)
  #print ph.createContainer(203, {'Image':'training/webapp', 'Cmd':["python", "app.py"], 'Port':'5004'})
  #print ph.killContainer('training/webapp')
  #print ph.killContainer('360')
  #print ph.getApps(203)
