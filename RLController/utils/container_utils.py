#coding:utf-8
"""
@author 'zhangguanxing01'
@email  'zhangguanxing01@baidu.com'
@file   'container_utils.py'
@date   '2014/04/10'

@Copyright 
    Baidu Inc. 2014
"""

import os
import cPickle
STATUS_FILE = '/home/bae/run/baeng/hades/status/instance.status'


def get_all_containers():
    try:
        with open(STATUS_FILE, 'rb') as fd:
            a = cPickle.load(fd)
            i = [k for k in a.keys() if k.find('@') == -1]
            for k in i:
                del a[k]

    except Exception:
        raise IOError("can't get container list")
    return a


def get_container_id_list():
    containers = get_all_containers()
    ret = []
    for instance_name, info in containers.items():
        ret.append((info['display_name'], info['longid']))
    return ret


def get_path_by_container(base_path, container, filename):
    container_path = os.path.join(base_path, container)
    full_path = os.path.join(container_path, filename)
    if not os.path.isdir(container_path) or not os.path.isfile(full_path):
        raise IOError("Can't find [container_path : %s] or [file : %s]" %(container_path, full_path))
    return full_path


def get_file_content_kv(path, t=float):
    ret = dict()
    with open(path, 'r') as fd:
        for line in fd.readlines():
            k,v = line.strip().split()
            ret[k] = t(v)
    return ret

def get_file_content_cpu(path, t=float):
    ret = dict()
    with open(path, 'r') as fd:
        for line in fd.readlines():
          list = []
          for v in line.strip().split()[1:]
            list.append(t(v))
          return list


def get_file_content(path):
    ret = None
    with open(path, 'r') as fd:
        ret = fd.read().strip()
    return ret
