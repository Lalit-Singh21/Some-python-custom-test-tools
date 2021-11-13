# -*- coding: utf-8 -*-
import os
import sys
import re
import string

def parseJunkCharacters():
    data = []
    LogsPath = sys.argv[1]
    try:
        for (dirpath, dirnames, filenames) in os.walk(LogsPath):
            for sFilename in filenames:
                sFilepath= os.path.join(dirpath, sFilename)
                #print sFilepath
                with open(sFilepath, 'r') as fh:
                    data = fh.readlines()                    
                    #print len(data)
                    print "Junk Characters in: {0}".format(sFilepath)
                    print('---')
                    for index in range(len(data)):
                        line = data[index].rstrip()
                        filtered_string = filter(lambda x: x not in string.printable, line)
                        if filtered_string <> "":
                            print(data[index].rstrip())
                           
    except Exception, e:
        print e


if __name__ == "__main__":
    parseJunkCharacters()
    
