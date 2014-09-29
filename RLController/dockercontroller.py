import multiprocessing
import httplib
import urllib
import time
import json
import os
import logging
import utils
import MySQLdb

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
    ccpu,cpu = 0,0
    cmem,mem = 0,0
    tmp = {}
    try:
      conn=MySQLdb.connect(host='192.168.4.203',user='root',passwd='seforge520',db='dockerexp',port=3306)
      cursor=conn.cursor()
      cursor.execute('select * from consumption')
      dctns = {}
      ctn = ''
      for row in cursor.fetchall():
        ctn = row[0]
        dctns[row[0]] = []
        for r in row[1::]:
          dctns[row[0]].append(r)
      nparams = []
      params = []
      if ctn:
        cur = (int(dctns[ctn][-1]) + 1) % 6
      else:
        cur = -1
      for ctn in self.getContainers(self.id):
        now =  self.getContainerState(ctn)
        tmp[ctn] = now
        if not dctns.has_key(ctn):
          nparams.append((ctn,cur))
          continue
        #if last and last.has_key(ctn):
        ccpu = (now['cpu_usage']-last[ctn]['cpu_usage'])/(now['time']-last[ctn]['time'])
        cpu += ccpu
        mem += now['usage']
        cmem = now['usage']/now['limit']
        params.append((ccpu,cmem,cur,ctn))
      if nparams:
        nsql = 'insert into consumption(id, cur) values(%s, %s)'
        print nsql
        print nparams
        cursor.executemany(nsql, nparams)
      if params:
        sql = 'update consumption set cpu'+str(cur)+'=%s,mem'+str(cur)+'=%s,cur=%s where id = %s'
        print sql
        print params
        cursor.executemany(sql, params)
      cursor.close()
      conn.commit()
      conn.close()
    except MySQLdb.Error,e:
      print "Mysql Error %d: %s" % (e.args[0], e.args[1])

   
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

  def clearData(self):
    try:
      conn=MySQLdb.connect(host='192.168.4.203',user='root',passwd='seforge520',db='dockerexp',port=3306)
      cursor=conn.cursor()
      cursor.execute('delete from consumption')
      cursor.close()
      conn.commit()
      conn.close()
    except MySQLdb.Error,e:
      print "Mysql Error %d: %s" % (e.args[0], e.args[1])


  def initData(self):
    try:
      conn=MySQLdb.connect(host='192.168.4.203',user='root',passwd='seforge520',db='dockerexp',port=3306)
      cursor=conn.cursor()
      cursor.execute('delete from consumption')
      last = {}
      params = []
      for ctn in self.getContainers(self.id):
        last[ctn] =  self.getContainerState(ctn)
        params.append(ctn)
      sql = 'insert into consumption(id) values(%s)'
      cursor.executemany(sql, params)
      for cur in range(6):
        time.sleep(1)
        params = []
        for ctn in self.getContainers(self.id):
          now =  self.getContainerState(ctn)
          if last and last.has_key(ctn):
            cpu = (now['cpu_usage']-last[ctn]['cpu_usage'])/(now['time']-last[ctn]['time'])
          mem = now['usage']/now['limit']
          last[ctn] = now
          params.append((cpu,mem,cur,ctn))
        sql = 'update consumption set cpu'+str(cur)+'=%s,mem'+str(cur)+'=%s,cur=%s where id = %s'
        print sql
        print params
        print cursor.executemany(sql, params)
      cursor.close()
      conn.commit()
      conn.close()
    except MySQLdb.Error,e:
      print "Mysql Error %d: %s" % (e.args[0], e.args[1])

  def readMySQL(self):
    try:
      conn=MySQLdb.connect(host='192.168.4.203',user='root',passwd='seforge520',db='dockerexp',port=3306)
      cursor=conn.cursor()
      ctn = '8cd31d9844b7279e5c318ed9687655bde9a660a58c6c0a0abdc66eee35161f9cq' 
      print cursor.execute('select * from consumption')
      print cursor.fetchall()
      cursor.close()
      conn.commit()
      conn.close()
    except MySQLdb.Error,e:
      print "Mysql Error %d: %s" % (e.args[0], e.args[1])

  def mySQL(self):
    ctns = self.getContainers(202)
    params = []
    cur = 0
    for ctn in ctns:
      res = self.getContainerState(ctn)
      params.append((ctn, float(res['cpu_usage']),float(res['usage']/res['limit']),cur))
    sql = 'insert into consumption(id,cpu'+str(cur)+',mem'+str(cur)+',cur) values(%s,%s,%s,%s)'
    print sql
    print params
    try:
      conn=MySQLdb.connect(host='192.168.4.203',user='root',passwd='seforge520',db='dockerexp',port=3306)
      cursor=conn.cursor()
      cursor.executemany(sql, params)
      cursor.close()
      conn.commit()
      conn.close()
    except MySQLdb.Error,e:
      print "Mysql Error %d: %s" % (e.args[0], e.args[1])

  def diff_expma(self, data, ratio=2):
    y = 0
    for i in range(1,len(data)):
      y = 1.0 * (ratio * (float(data[i])-float(data[i-1])) + (i-1) * y) / (i-1+ratio)
    return [y, float(data[-1])]

  def compute_trend(self, id):
    try:
      conn=MySQLdb.connect(host='192.168.4.203',user='root',passwd='seforge520',db='dockerexp',port=3306)
      cursor=conn.cursor()
      n = cursor.execute('select * from consumption where id = %s', id)
      if n == 0:
        print 'No container info in database'
      else:
        for row in cursor.fetchall():
          cur = int(row[-1])
          cpudata = row[1:7:]
          cpudata = cpudata[(cur+1)%6:6:] + cpudata[0:(cur+1)%6:]
          cputrd = self.diff_expma(cpudata)
          memdata = row[7:13:]
          memdata = memdata[(cur+1)%6:6:] + memdata[0:(cur+1)%6:]
          memtrd = self.diff_expma(memdata)
      cursor.close()
      conn.commit()
      conn.close()
    except MySQLdb.Error,e:
      print "Mysql Error %d: %s" % (e.args[0], e.args[1])
    return cputrd, memtrd

if __name__ == '__main__':
  ph = PhysicalMachine(202)
  ph.clearData()
  last = None
  for i in range(9):
    _,last = ph.getState(last)
    time.sleep(2)
  print ph.compute_trend('3ddc7a209aecee63af10ba132fc89cdc7e47fac6e89ec5f1a8a662442fe5e50c')
  
  
  '''
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
  '''
  #print ph.getApps(203)
  #print ph.createContainer(203, {'Image':'training/webapp', 'Cmd':["python", "app.py"], 'Port':'5004'})
  #print ph.killContainer('training/webapp')
  #print ph.killContainer('360')
  #print ph.getApps(203)
