#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import pybcs 

#设置日志级别
#pybcs.init_logging(logging.INFO)


# 请修改这里
AK = "CA15013bf89aa0acdb989bae0b9db63a"
SK = "16304ea0b4b2d484efd615bf5300a2eb"
BUCKET='dsc-api'



bcs = pybcs.BCS('http://bcs.duapp.com/', AK, SK, pybcs.HttplibHTTPC)    #这里可以显式选择使用的HttpClient, 可以是:
                                                                        #PyCurlHTTPC
#声明一个bucket
bucket = bcs.bucket(BUCKET)

#o = bucket.object("/log/2013/10/02-5.png")

#img = '/home/iceleaf/02-5.PNG'
#with open(img) as fp:
    #o.put(fp.read())

#for obj in bucket.list_objects():
    #print obj

