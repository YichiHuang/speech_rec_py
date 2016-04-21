#!usr/bin/env python
# -*- coding: utf-8 -*-
import wave
from pyaudio import PyAudio,paInt16
import numpy as np
from datetime import datetime
import urllib, urllib2
import pycurl
import json
import base64

import numpy as np
from StringIO import StringIO
import io
import time

# define parameters
framerate=8000
NUM_SAMPLES=2000
channels=1
sampwidth=2
TIME=2 

def save_wave_file(filename,data):
    '''save the data to the wav file'''
    wf=wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)
    wf.setframerate(framerate)
    wf.writeframes("".join(data))
    wf.close()
    
def dump_res(buf):
    print buf
    my_temp=json.loads(buf)
    my_list=my_temp['result']
    print type(my_list)
    print my_list[0]
    
    
def my_record():
    pa=PyAudio()
    stream=pa.open(format=paInt16,channels=1,
                   rate=framerate,input=True,
                   frames_per_buffer=NUM_SAMPLES)
    my_buf=[]
    count=0
    print "* start recoding *"
    while count<TIME*5:
        string_audio_data=stream.read(NUM_SAMPLES)
        my_buf.append(string_audio_data)
        count+=1
        print '.'
    #filename=datetime.now().strftime("%Y-%m-%d_%H_%M_%S")+".wav"
    filename="01.wav"
    save_wave_file(filename, my_buf)
    stream.close()
    print "* "+filename, "is saved! *"
    
def get_token():
    apiKey="cxULarS41y8rmCEvICpsuWUm"
    secretKey="55e9531bb4b5ceb9015f2e2e44fd6646"
    
    auth_url="https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id="+apiKey+"&client_secret="+secretKey;
    
    res=urllib2.urlopen(auth_url)
    json_data=res.read()
    # print 'json data:',type(json_data)
    return json.loads(json_data)['access_token']
    
def use_cloud(token):
    fp=wave.open(u'01.wav','rb')
    nf=fp.getnframes()
    print 'sampwidth:',fp.getnframes()
    print 'framerate:',fp.getframerate()
    print 'channels:',fp.getnchannels()
    f_len=nf*2 
    audio_data=fp.readframes(nf)
    
    cuid="10:2A:B3:58:28:88" #my redmi phone MAC
    srv_url='http://vop.baidu.com/server_api'+'?cuid='+cuid+'&token='+token
    http_header=[
                 'Content-Type:audio/pcm; rate=8000',
                 'Content-length:%d' % f_len
    ]
    
    c=pycurl.Curl()
    c.setopt(pycurl.URL,str(srv_url))
    c.setopt(c.HTTPHEADER,http_header)
    c.setopt(c.CONNECTTIMEOUT,80)
    c.setopt(c.TIMEOUT,80)
    c.setopt(c.WRITEFUNCTION,dump_res)
    c.setopt(c.POSTFIELDS,audio_data)
    c.setopt(c.POSTFIELDSIZE,f_len)
    c.perform() #pycurl.perform() has no return val
    
my_record()
print '* done recording! *'
use_cloud(get_token())
print 'OK!'
    
      