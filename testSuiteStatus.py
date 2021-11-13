import os
import stat
import re
import sys
import csv
import time
import json
from collections import OrderedDict

IgnorePath = "zip"

def tree():
    return collections.defaultdict(tree)

catalyst_status_dict = OrderedDict()
client_status_dict = OrderedDict()

translation_table = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;',
}

def escape1(input_text):
        return ''.join(translation_table.get(char, char) for char in input_text)

SECONDS_IN_A_DAY = 24 * 60 * 60
Hours = 12
now = time.time()


# Function to create csv file with all client and catalyst test status
def createTestStatusCSV():
    csv_file = LogsPath+"\AutomationStatus.csv"

    writer = csv.writer(open(csv_file, 'wb'))
    if catalyst_status_dict:
            writer.writerow(["Catalyst Status, {0}".format(catalyst_summary)])
            writer.writerow([""])
            for key, value in (catalyst_status_dict.items()):
                writer.writerow(["Catalyst", key, value[0],value[1]])
            writer.writerow([""])
            writer.writerow([""])
    if client_status_dict:
            writer.writerow(["Client Status, {0}".format(client_summary)])
            writer.writerow([""])
            for key, value in (client_status_dict.items()):
                    writer.writerow(["Client",key, value[0],value[1]])

#Global test summary dict
client_summary = {"PASSED":0,"FAILED":0,"INCOMPLETE":0}
catalyst_summary = {"PASSED":0,"FAILED":0,"INCOMPLETE":0}

# Function to add test status to dictionary
def addTestStatus(script_name,count,status,script_path,filename):
    catalyst_script = r"Sparrow\Scripts"
    client_script = r"Sparrow_Legacy\Scripts"
    script_name = script_name.replace('&amp;','&')
    if catalyst_script.lower() in script_path.lower():
       if not catalyst_status_dict.has_key(script_name.rstrip()):
           #print "{0} not in dict, adding..".format(passed_script)
            catalyst_summary[status] += 1
            #catalyst_status_dict[script_name.rstrip()+"(RN #"+str(len(catalyst_status_dict)+1)+")"] = [status,os.path.dirname(filename)]
            catalyst_status_dict[script_name.rstrip()] = [status,os.path.dirname(filename)]
       elif (catalyst_status_dict.has_key(script_name.rstrip()) and status == "PASSED"):
           catalyst_summary[catalyst_status_dict[script_name.rstrip()][0]] -= 1
           catalyst_summary[status] += 1
           catalyst_status_dict[script_name.rstrip()] = [status,os.path.dirname(filename)]            
        
    elif client_script.lower() in script_path.lower():
       #print "scriptname",script_name
        if not client_status_dict.has_key(script_name.rstrip()):
            client_summary[status] += 1
            #client_status_dict[script_name.rstrip()+" (RN #"+str(len(client_status_dict)+1)+")"] = [status,os.path.dirname(filename)]
            client_status_dict[script_name.rstrip()] = [status,os.path.dirname(filename)]
        elif (client_status_dict.has_key(script_name.rstrip()) and status == "PASSED"):
            client_summary[client_status_dict[script_name.rstrip()][0]] -= 1
            client_summary[status] += 1            
            client_status_dict[script_name.rstrip()] = [status,os.path.dirname(filename)]

##global constant delimeters for logs
SCRIPT_EXECUTION_COMPLETE = "SCRIPT_EXECUTION_COMPLETE"
PASSED_TESTCASE_SUMMARY = "Total number of failed test steps: 0"
EXECUTION_START = "*** Execution Start:"
EXECUTION_END = "*** Execution End:"
DEVICE_CODE_VERSION = "Device Code Version:"
COMPLETE_STEP_ENCOUNTERED = "Cleaning up (complete step encountered)..." #this is for pass status
FATAL_STEP_ENCOUNTERED = "Cleaning up (FATAL step encountered)..." #this is for fail test
TERMINATING_SCRIPT_EXECUTION = "Cleanup finished (terminating script execution)" #pass/fail
STOP_INITIATED = "Cleaning up (stop initiated)..." #incomplete
STOP_INITIATED_2 = "Stop initiated, stopping script execution, please wait..." #incomplete

#to get test status for .xml or .csv file
def getstatus(filename):
    f = open(filename,'r')
    print "getstatus, filename to parse####",filename
    file_contents = f.readlines()
    f.close()
    #print file_contents
    sFile = os.path.basename(filename)
    basename, ext = os.path.splitext(sFile)
    len_file = len(file_contents)
    i = 0
    while( i < len_file ):
       #logic ...
        if ext.lower().endswith('xml'):
            for status in ["PASSED","FAILED","INCOMPLETE"]:
               if status in file_contents[i]:
                   try:
                       if "scriptName=" in file_contents[i]:
                           #print file_contents[i]
                           script_name = ([x for x in file_contents[i].split("\t") if re.search("scriptName=", x)])[0].split("=")[1].strip('"')
                           script_path = ([x for x in file_contents[i].split("\t") if re.search("scriptPath=", x)])[0].split("=")[1].strip('"')
                           addTestStatus(script_name,i,status,script_path,filename)
                   except Exception, e:
                       print "PARSING ERROR, status in file_contents[i]:", e, e.message, e.args
        elif (ext.lower().endswith('log')):
            if (PASSED_TESTCASE_SUMMARY in file_contents[i]):   
                for k in range(i-20,i+20):
                    try: 
                        if EXECUTION_END in file_contents[k]:
                            script_name = os.path.basename((file_contents[k].split("Development")[-1:])[0].split("***")[0])
                            script_path = file_contents[k].split("Development")[-2:][1].split("***")[0]
                            addTestStatus(script_name,i,"PASSED",script_path,filename)
                    except Exception, e:
                        print "PARSING ERROR for log file, PASSED_TESTCASE_SUMMARY in file_contents[i]:", e, e.message, e.args
                        continue
            #elif (PASSED_TESTCASE_SUMMARY.split(":")[0] in file_contents[i] or FATAL_STEP_ENCOUNTERED in file_contents[i]) :
            elif ("|FA" in file_contents[i]) :                   
                for k in range(i-10,i+1):
                    try:
                        if ".pl" in file_contents[k]:
                            script_name = os.path.basename((file_contents[k].split("Development")[-1:])[0].split(".pl(")[0])+".pl"
                            script_path = file_contents[k].split(".pl")[0].split("Development")[1]#+".pl(" #[1] #.split("***")[0]
                            #print script_name,script_path
                            addTestStatus(script_name,i,"FAILED",script_path,filename)
                            break
                    except Exception, e:
                        print "PARSING ERROR for log file, elif (FA in file_contents[i]):", e, e.message, e.args
                        continue
                for j in range (i,len_file):
                    #point line number to next test start to remove last error duplicacy
                    if EXECUTION_START in file_contents[j]:
                        i = j
                        break                    
            if (STOP_INITIATED in file_contents[i]):
                #print file_contents[i],i
                for k in (range(i,len_file)):
                    try:                        
                        if EXECUTION_END in file_contents[k]:
                            print file_contents[k]
                            if "Development" in file_contents[k]:
                                script_name = os.path.basename((file_contents[k].split("Development")[-1:])[0].split("***")[0])
                                script_path = file_contents[k].split("Development")[-2:][1].split("***")[0]
                                #print script_name,script_path
                                addTestStatus(script_name,i,"INCOMPLETE",script_path,filename)
                                break
                    except Exception, e:
                        print "PARSING ERROR for log file, STOP_INITIATED in file_contents[i]:", e, e.message, e.args                    
        i +=1


def parseTestStatus(LogsPath,DAYS_TO_PARSE):
    for (dirpath, dirnames, filenames) in os.walk(LogsPath):
        sInputFile = ""
        #print dirpath, dirnames, filenames
        dirnames[:] = filter(lambda x : not x.endswith(IgnorePath), dirnames)
        print "DIRNAMES[:]",dirnames[:]
        for sFilename in filenames:        
            try:
                basename, ext = os.path.splitext(sFilename)
                sFilepath= os.path.join(dirpath, sFilename)

                error_log_parser_file = os.path.join(os.path.dirname(sFilepath),(os.path.basename(os.path.dirname(sFilepath))+".log"))
                if os.path.isfile(error_log_parser_file):
                    print "PARSING LOG FILE FOR ERROR SNAPSHOT:", error_log_parser_file
                    #print os.path.dirname(sFilepath)+"\error.log"
                    try:
                        os.chmod(os.path.dirname(sFilepath), 0777)
                        os.system(r"C:\Python27\python.exe {0} {1}".format(os.path.join(os.getcwd(),"Sparrow_ErrorLogsParser.py"),error_log_parser_file))
                        #sys.stdout.close()
                        #sys.stderr.close()                        
                    except Exception, e:
                        print e
                                
                if ext.lower().endswith('xml'):
                    sInputFile = sFilepath
                    break
                elif (sFilename == os.path.basename(os.path.dirname(sFilepath))+".log"):
                    sInputFile = sFilepath
                else:      
                    continue
            except Exception, e:
                print "ERROR IN PARSING LOG FILE:%s" %e

        ##getting all the files newer than 'DAYS_TO_PARSE'
        if (os.path.isfile(sInputFile)) and (os.stat(sInputFile).st_mtime > now - DAYS_TO_PARSE * SECONDS_IN_A_DAY):
            print "file present to parse:",sInputFile
            getstatus(sInputFile)                

    # summary
    #print "catalyst status, {0}".format(catalyst_summary)
    #print "client status, {0}".format(client_summary)
                
    #json1 = json.dumps(catalyst_status_dict, ensure_ascii=False)
    #print json1
    
    if catalyst_status_dict or client_status_dict:
        createTestStatusCSV()
            


if __name__ == "__main__":
    LogsPath = sys.argv[1]
    #DAYS_TO_PARSE = int(sys.argv[2])
    DAYS_TO_PARSE = 300
    #LogsPath = r"C:\TEMP\ - Example1"
    parseTestStatus(LogsPath,DAYS_TO_PARSE)


