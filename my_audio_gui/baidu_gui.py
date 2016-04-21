#!usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4.QtGui import QMainWindow
from PyQt4.QtCore import pyqtSignature
from PyQt4 import QtCore, QtGui
import wave
import urllib, urllib2
import pycurl
import json

import numpy as np
from pyaudio import PyAudio,paInt16
from datetime import datetime
import wave
import time
from time import sleep,ctime
import threading
import Queue
import sys
import os
import serial
import StringIO



from Ui_baidu_gui import Ui_MainWindow
from matplotlib.backends.backend_qt5 import MainWindow
from PyQt4.Qt import QApplication

framerate=8000
NUM_SAMPLES=2000
channels=1
sampwidth=2
TIME=2 

    
class MyThread(threading.Thread):
    def __init__(self,func,args,name=''):
        threading.Thread.__init__(self)
        self.name=name
        self.func=func
        self.args=args
        
    def getResult(self):
        return self.res
    
    def run(self):
        print 'starting',self.name,'at:',ctime()
        self.res=apply(self.func,self.args)
        print self.name,'finished at:',ctime()
        
    def writeQ(self,queue,data):
        #    print 'producing object for Q...'
        queue.put(data,1)
        #    print "size now",queue.qsize()
    
    def readQ(self,queue):
        val=queue.get(1)
        return val
    
        
class MainWindow(QMainWindow,Ui_MainWindow,threading.Thread):
    """
    Class documentation goes here.
    """
    def __init__(self,parent=None):

        QMainWindow.__init__(self,parent)
        threading.Thread.__init__(self)
        self.name=self.voice_tts.__name__
        self.setupUi(self)
        self.NUM_SAMPLES=2000
        self.framerate=8000
        self.channels=1
        self.sampwidth=2
        self.TIME=2
        
        self.LEVEL=500
        self.mute_count_limit=10
        self.mute_begin=0
        self.mute_end=1
        self.not_mute=0
        self.voice_queue=Queue.Queue(1024)
        self.wav_queue=Queue.Queue(1024)
        self.file_name_index=1
        self.thread_flag=0
        self.start_flag=1
        try:
            self.serial=serial.Serial('/dev/ttyUSB0',9600)
        except Exception as e:
            print e
            self.serial=None
    def getResult(self):
        return self.res
        
    def run(self):
        print 'starting',self.name,'at:',ctime()
        self.res=apply(self.voice_tts,())
        print self.name,'finished at:',ctime()
        
    def writeQ(self,queue,data):
        #    print 'producing object for Q...'
        queue.put(data,1)
        #    print "size now",queue.qsize()
    
    def readQ(self,queue):
        val=queue.get(1)
        return val
        
    def save_wave_file(self,filename,data):

        wf=wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.sampwidth)
        wf.setframerate(self.framerate)
        wf.writeframes("".join(data))
        wf.close()   
        
    def record_wave(self,temp):
        while self.start_flag==1:
            pa=PyAudio()
            stream=pa.open(format=paInt16,channels=1,
                       rate=framerate,input=True,
                       frames_per_buffer=self.NUM_SAMPLES)
            my_buf=[]
            count=0
            print "* start recoding *"
            while count<self.TIME*20:
                string_audio_data=stream.read(self.NUM_SAMPLES)
                audio_data=np.fromstring(string_audio_data,dtype=np.short)
                large_sample_count=np.sum(audio_data>self.LEVEL)
                print large_sample_count
                if large_sample_count<self.mute_count_limit:
                    self.mute_begin=1
                else:
                    my_buf.append(string_audio_data)
                    self.mute_begin=0
                    self.mute_end=1
                count+=1
                if(self.mute_end-self.mute_begin)>9:
                    self.mute_begin=0
                    self.mute_end=1
                    break
                if self.mute_begin:
                    self.mute_end+=1
                print '.'
                
            my_buf=my_buf[:]
            if my_buf:
                if self.file_name_index<11:
                    pass
                else:
                    self.file_name_index=1
                filename=str(self.file_name_index)+'.wav'
                self.save_wave_file(filename=filename,data=my_buf)
                self.writeQ(queue=self.wav_queue,data=filename)
                self.file_name_index+=1
                print filename,"saved"
            else:
                print '* Error: file not saved! *'
            #self.save_wave_file(filename, my_buf)
            my_buf=[]
            stream.close()
        
    def dump_res(self,buf):
        print buf
        my_temp=json.loads(buf)
        if my_temp['err_no']:
            if my_temp['err_no']==3300:
                print u'参数输入不正确'
            elif my_temp['err_no']==3301:
                print u'识别错误'
            elif my_temp['err_no']==3302:
                print u'验证失败'
            elif my_temp['err_no']==3303:
                print u'语音服务器后端问题'
            elif my_temp['err_no']==3304:
                print u'请求GPS过大，超过限额'           
            elif my_temp['err_no']==3305:
                print u'产品线当前请求数超过限额'
        else:
            my_list=my_temp['result']
            print type(my_list)
            print my_list[0]
            self.textBrowser.append(my_list[0])
            
    def get_token(self):
        apiKey="cxULarS41y8rmCEvICpsuWUm"
        secretKey="55e9531bb4b5ceb9015f2e2e44fd6646"
    
        auth_url="https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id="+apiKey+"&client_secret="+secretKey;
    
        res=urllib2.urlopen(auth_url)
        json_data=res.read()
        # print 'json data:',type(json_data)
        return json.loads(json_data)['access_token']
    
    def use_cloud(self,token):
        while True:
            if self.wav_queue.qsize():
                filename=self.readQ(queue=self.wav_queue)
            else:
                continue
            fp=wave.open(filename,'rb')
            nf=fp.getnframes()
            #print 'sampwidth:',fp.getnframes()
            #print 'framerate:',fp.getframerate()
            #print 'channels:',fp.getnchannels()
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
            c.setopt(c.WRITEFUNCTION,self.dump_res)
            c.setopt(c.POSTFIELDS,audio_data)
            c.setopt(c.POSTFIELDSIZE,f_len)
            try:
                c.perform() #pycurl.perform() has no return val
            except Exception as e:
                print e
            sleep(0.3)
            
    def voice_tts(self):
        self.use_cloud(token=self.get_token())
    
    @pyqtSignature("")
    def on_pushButton_clicked(self):
        """
        Slot documentation goes here.
        """
        #print "OK!"
        #self.my_record()
        #self.use_cloud(self.get_token())
        if self.thread_flag==0:
            self.start_flag=1
            record_t=MyThread(self.record_wave,(self,),self.record_wave.__name__)
            record_t.setDaemon(True)
            record_t.start()
            self.thread_flag=1
        
    @pyqtSignature("")
    def on_pushButton_2_clicked(self):
        """
        Slot documentation goes here.
        """
        if self.thread_flag==1:
            self.start_flag=0
            self.thread_flag=0
            
    @pyqtSignature("")
    def on_radioButton_clicked(self):
         """
        Slot documentation goes here.
        """
        # TODO :not implemented yet
        #raise NotImplementedError
    @pyqtSignature("")
    def on_radioButton_2_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO :not implemented yet
        #raise NotImplementedError
        
if __name__=='__main__':
    app=QtGui.QApplication(sys.argv)
    ui=MainWindow()
    ui.setDaemon(True)
    ui.start()
    #record_t=MyThread(ui.use_cloud,(ui.get_token(),),ui.use_cloud.__name__)
    #record_t.setDaemon(True)
    #record_t.start()
    ui.show()
    app.exec_()
