# -*- coding: utf-8 -*-
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from http.server import BaseHTTPRequestHandler
import sys
import signal
import time
import ssl
import http.client
import re
import shutil
from itertools import islice
from tkinter import *
import time
import msvcrt
from msvcrt import getch
from select import select


send_insight = False
#insight_msg = '[{"InsightDelivery":{"id":"067e6162-3b6f-4ae2-a171-2470b63dff00","type":"invalid-battery-change","producer":"OAWFP","version":"1.0.0","created":"111111111111","customerid":"bbbbbbbb-3b6f-4ae2-a171-2470b63dff00","headline":"You are doing a good Job today","model":"77818181","intentions":"hints/intent","critical":"true","priority":"priority_false","playtime":"0800-0830","disposition":"+","target":"operator","recipient":"s8393882","platform":"talkman","mode":"audible","exposure":"private","audience":"individual","expires":"2222222222","opportunity":"asap"}}]'
#23rd oct build
insight_msg = '[{"InsightDelivery":{"id":"067e6162-3b6f-4ae2-a171-2470b63dff00","type":"invalid-battery-change","producer":"OAWFP","version":"1.0.0","created":"3111111111","customerid":"bbbbbbbb-3b6f-4ae2-a171-2470b63dff00","headline":"Please have your previous battery checked by supervisor","model":"77818181","intentions":"hints/intent","critical":"true","priority":"priority_false","playtime":"0800-0830","disposition":"+","target":"operator","recipient":"s8393882","platform":"talkman","mode":"audible","exposure":"private","audience":"individual","expires":"3222222222","opportunity":"asap"}}]'
#class serviceRequest
class myHTTPServer(SimpleHTTPRequestHandler):
    
    stopped = False
    def handle_request(self,data):
        #print("See the request...")
        self.send_header('Content-type','text-html')
        self.send_header("Content-length", len(data))
        self.end_headers()
        print("Sending.. "+data)
        self.wfile.write(data.encode(encoding='UTF-8'))

    """ this is my http server, override do_POST(), and serve_forever()"""
    def do_POST(self):    ## Messages from VA captured here.
        length = self.headers.get('Content-Length',"")
        if length:
            print("Content length is: "+length)
        readAll = self.rfile.read(int(length))
        #print("Read somthing! "+str(readAll))
        self.protocol_version = 'HTTP/1.1'
        self.send_response(200)
        # need to start manipulating requests here. 
        requestStr = str(readAll)
        #requestStr = readAll.decode("utf-8",errors = 'ignore')
        print ("\n~~~~~requestStr~~~~~~~"),requestStr
	#requestStr = readAll.decode(('utf-8').encode('cp850','replace').decode('cp850'))
        print ("\n************************************************************")
        print("Received Packet......\r\n "+requestStr)
        global send_insight
        if (send_insight == True):
            print ("####################                            ####################\r\n")
            print ("####################                            ####################\r\n")
            print ("#################### Sending insight from proxy ####################\r\n")
            print ("####################                            ####################\r\n")
            print ("####################                            ####################\r\n")
            self.handle_request(insight_msg)
            send_insight = False
        else:
            print ("No insight. Moving on...")
            self.handle_request("**********Handshake********\r\n")


        

def run():
    
    print("HTTP Server is running....")
    server_address = ('10.78.124.46', 8090)
    httpd = HTTPServer(server_address, myHTTPServer)
    global send_insight
    while 1:
        try:
           httpd.serve_forever()
           # httpd.rel_hound()
        except:
            global insight_msg
            #print("You pressed ctrl+C, sending insight now")
            insight_msg = input("You pressed ctrl+C, Type insight message to be sent and press enter: ")
            send_insight = True
            #httpd.server_close()
            #httpd.stopped = True
            continue
           

if __name__ == '__main__':
  run()
