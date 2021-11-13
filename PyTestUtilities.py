#####################################################################################################
"""
 Script               : PyTestUtilities.py
 Description          : optimization of test environment,logs and results
 Author               : Lalit Singh
"""
######################################################################################################


import zipfile
import os
import stat
import time
import subprocess
import argparse
import win32api
import win32con
import win32netcon
import win32security
import win32wnet
import ConfigParser
import shutil
import wmi
import _winreg
import logging
import multiprocessing
from multiprocessing import Process
from _winreg import *
import inspect
import socket
import signal
import sys
from itertools import repeat
#from test.nft_test_utils import NFTestUtils


class PySparrowUtilities:
    
    def __init__(self):
        #objStatus = NFTestUtils()
        #runningStatus = objStatus.test_status()
        #print "RunningStatus is %s" % runningStatus
        #if runningStatus == 1:
        #    sys.exit(0)
        self.SECONDS_IN_A_DAY = 24 * 60 * 60
        self.Hours_forTempDeletion=12
        self.now = time.time()

    def SetupLogger(self,logname, id):
        global thisLogger
        thisLogger = logging.getLogger(__name__)
		#modify the logging path
        hdlr = logging.FileHandler(r'W:\test_results\PySparrowUtilitiesLogs\\%s_%s_%s_%s.log' %(id,logname,self.now,socket.gethostname()))
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        thisLogger.addHandler(hdlr) 
        thisLogger.setLevel(logging.DEBUG)


    ##FUNCTION TO RUN MULTIPLE CHILD PROCESSES
    def RunMultiProcesses(self,templist,funcname):
        if len(templist)<10:
            num_of_process=len(templist)
        else:
            num_of_process=10
        process_list = [[] for i in repeat(None, num_of_process)]
        while templist <> []:
            for i in range(num_of_process):
                if templist<>[]:
                    element = templist.pop()
                    process_list[i].append(element)
        process_list= filter(None, process_list) 
        del templist
        try:
            procs = []
            for process in process_list:
                procs.append(Process(target=funcname, args=(process,len(procs)+1)))
            for p in procs:
                p.start()
            for p in procs:
                p.join()
        except KeyboardInterrupt:
            for p in procs:
                p.start()


    ##FUNCTION TO RETURN TEMP LOCATION OF A WINDOWS MACHINE
    def GetTempofMachine(self,sMachine):
        try:
            response = os.system("ping -w 100 -n 1 " + sMachine)
            if response == 0:            
                reg = ConnectRegistry(sMachine, HKEY_CURRENT_USER)
                key = OpenKey(reg, 'Environment',0,KEY_READ)
                TempPath=QueryValueEx(key, 'TEMP')
                key = OpenKey(reg, 'Volatile Environment',0,KEY_READ)
                HomePath = QueryValueEx(key, 'HOMEPATH')
                HomeDrive = QueryValueEx(key, 'HOMEDRIVE')
                HomeDrive=HomeDrive[0].replace(':','$')
                HomePath=('\\\%s\%s%s' %(sMachine,HomeDrive,HomePath[0])).lower().strip()
                TempPath=TempPath[0].replace("%USERPROFILE%",HomePath)
                print TempPath
                return TempPath
        except Exception, e:
            print e


    ##FUNCTION TO READ LIST OF MACHINES FROM A RANGE EXAMPLE LON14MSTST011 - LON14MSTST044 (OR MSWIN7TST001-MSWIN7TST020) AND RETURN AS A LIST
    def ReadMachineListfromRange(self,machine,lastmachine):
        try:
            mlist=[]
            iFirst= int(machine[-3:])
            iLast= int(lastmachine[-3:])
            while iFirst<=iLast:
                if machine<>None:
                    machine=machine.replace(machine[-3:],('{0:03}'.format(iFirst)))
                    mlist.append(str(machine).lower())
                iFirst=iFirst+1
            return mlist
        except Exception, e:
            print e


    ##FUNCTION TO READ MACHINES FROM A CONFIG FILE AND RETURN AS A LIST
    def ReadMachinesfromConfig(self,ConfigPath, section):
        try:
            mlist=[]
            config = ConfigParser.ConfigParser(allow_no_value=True)
            config.read(ConfigPath)
            for sMachine in config.options(section.strip()):
                if sMachine<>None:
                    sMachine=sMachine.strip().lower()
                    mlist.append(sMachine)
            return mlist
        except Exception, e:
            print e



   ##FUNCTION TO READ MACHINES FROM A CONFIG FILE AND RETURN AS A LIST
    def ReadMachinesfromFile(self,machineFile):
        try:
            machines = open(machineFile).read().lower().splitlines()
            return machines
        except Exception, e:
            print e


        
    ##function for compressing all the logs/files under a directory which are older than X days
    def CompressLogs(self,args):
        global thisLogger
        logname=inspect.stack()[0][3]
        self.SetupLogger(logname,"PyUtils")         
        ##traversing all the files and directories in a directory path
        ##path and days can be passed as arguments, default values for arguments are initialized in class            
        for (dirpath, dirnames, filenames) in os.walk(args.LogsPath):
            dirnames[:] = filter(lambda x : not x.startswith(args.IgnorePath), dirnames)
            for sFilename in filenames:
                try:
                    ##splitting the basename and extension of a file to ignore the zipped files
                    basename, ext = os.path.splitext(sFilename)
                    sFilepath= os.path.join(dirpath, sFilename)
                    if ext.lower().endswith('zip'): continue
                    ##compressing all the files older than 'DAYS_TO_ARCHIVE'
                    if (os.path.isfile(sFilepath)) and (os.stat(sFilepath).st_mtime < self.now - args.DAYS_TO_ARCHIVE * self.SECONDS_IN_A_DAY):
                            print "Compressing old logs: %s" %sFilepath
                            thisLogger.info ("Compressing old logs: %s" %sFilepath)
                            try:
                                sZipFile = zipfile.ZipFile('%s.zip' %sFilepath,'w',compression=zipfile.ZIP_DEFLATED)								
                                sZipFile.write(sFilepath,sFilename)
                            except Exception, e:
                                if (os.path.isfile(sFilepath+".zip")):
                                    os.remove(sFilepath+".zip")
                                print "Failed to Zip File %s %s" %sFilepath %e
                                thisLogger.error ("Failed to Zip File %s %s" %sFilepath %e)
                            finally:
                                if sZipFile.fp:
                                    sZipFile.close()
                                if (os.path.isfile(sFilepath+".zip")):                                
                                    os.utime(sFilepath+".zip", (os.stat(sFilepath).st_atime,os.stat(sFilepath).st_mtime))                                
                                    os.remove(sFilepath)
                                else:
                                    print "Zip File not present %s " %sFilepath+".zip"
                                    thisLogger.warn ("Zip File not present %s " %sFilepath+".zip")
                except Exception, e:
                    print "Failed to compress files:%s" %e
                    thisLogger.error("Failed to compress files:%s" %e)
                    continue



    ##function for deleting all the logs/files under a directory which are older than X days
    ##path and days can be passed as arguments, default values for arguments are initialized in class
    def DeleteLogs(self,args):
        global thisLogger
        logname=inspect.stack()[0][3]
        self.SetupLogger(logname,"PyUtils")         
        try:
            ##traversing all the directories and files in a directory path
            for (dirpath, dirnames, filenames) in os.walk(args.LogsPath):
                if args.IgnorePath !="":
                    dirnames[:] = filter(lambda x : not x.startswith(args.IgnorePath), dirnames)
                for sFilename in filenames:
                    sFilepath = os.path.join(dirpath, sFilename)
                    if (os.path.isfile(sFilepath)):
                        ##check if file is client log then delete logs older than 'DAYS_TO_DELETE_CL' days
                        if(sFilepath.find("ClientLogs")<> -1) and (os.stat(sFilepath).st_mtime < self.now - args.DAYS_TO_DELETE_CL * self.SECONDS_IN_A_DAY):
                            print "Deleting old Client logs: %s" % sFilepath
                            thisLogger.info("Deleting old Client logs: %s" % sFilepath)
                            os.remove(sFilepath)
                        ##check if file is not client log 
                        elif (os.stat(sFilepath).st_mtime < self.now - args.DAYS_TO_DELETE * self.SECONDS_IN_A_DAY):
                            print "Deleting old logs: %s" %sFilepath
                            thisLogger.info("Deleting old logs: %s" %sFilepath)
                            os.remove(sFilepath)
        except Exception, e:
            print "Failed to delete Logs:%s" %e
            thisLogger.error ("Failed to delete Logs:%s" %e)
    


    ##function to clear Temp folder 
    ##range of machines and path can be passed as arguments, if VM names are not passed as argument then it reads the config file for VM names
    def ClearTemp(self,args):
        global thisLogger
        logname=inspect.stack()[0][3]
        self.SetupLogger(logname,"PyUtils") 
        try:
            templist=[]
            sBasePath=args.TempPath
            ##if range of VM is provided in the batch file or from the console
            if args.sMachineLow<>"":
                machinelist=self.ReadMachineListfromRange(args.sMachineLow,args.sMachineHigh)
            ##if list of vm is read from the config file
            elif args.ConfigPath<>"":
                machinelist=self.ReadMachinesfromConfig(args.ConfigPath,'Machines_forTempFolderDelete')          
            ##if list of VM is read from text file
            elif args.FilePath<>"":
                machinelist=self.ReadMachinesfromFile(args.FilePath)
            else:
                print "Please enter valid config path, File path or machine name"
                thisLogger.warn ("Please enter valid config path, File path or machine name")
            if machinelist<>[]:                
                for sMachine in machinelist:
                    args.TempPath=os.path.join('\\\\', sMachine, sBasePath).lower().strip()
                    if os.path.exists(args.TempPath):
                        templist.append(args.TempPath)
                    else:
                        print "path does not exists %s" %args.TempPath
                        thisLogger.warn("path does not exists: %s" %args.TempPath)
                    if args.sGetTemp=="yes":
                        sTempPath=self.GetTempofMachine(sMachine)                    
                        if sTempPath<>None and os.path.exists(sTempPath) and sTempPath <> args.TempPath:
                            sTempPath=sTempPath.lower().strip()                        
                            templist.append(sTempPath)
            if templist<>"":
                self.RunMultiProcesses(templist,self.Utilities_DeleteTempPath)
                ##self.RunMultiProcessesPool(templist,self.Utilities_DeleteTempPath)
        except Exception, e:
            print "Failed to clear Temp %s"%e
            thisLogger.error("Failed to clear Temp %s" %e)



    def Utilities_DeleteTempPath(self,TempPathList,procId):
        global thisLogger
        logname=inspect.stack()[0][3]
        self.SetupLogger(logname,procId)         
        Number_of_Retry=0
        while Number_of_Retry<5:            
            try:
                for TempPath in TempPathList:
                    ##deleting content using windows commands
                    for (dirpath, dirnames, filenames) in os.walk(TempPath):
                        for sFilename in filenames:
                            sFilepath = os.path.join(dirpath, sFilename)
                            if (os.path.isfile(sFilepath)):
                                if (os.stat(sFilepath).st_mtime < self.now - (float(self.Hours_forTempDeletion)/float(24)) * self.SECONDS_IN_A_DAY):
                                    print "Deleting old temp files: %s" %sFilepath
                                    thisLogger.info ("Deleting old temp file: %s" %sFilepath)
                                    os.system('DEL /F /S /Q "%s"' % sFilepath)
                        if os.path.isdir(dirpath) and os.listdir(dirpath)==[]:
                            print "Deleting empty folders: %s" %dirpath
                            thisLogger.info ("Deleting empty folders: %s" %dirpath)
                            os.system(r'RD /S /Q "%s"' % dirpath)
                    if not os.path.exists(TempPath):
                        os.makedirs(TempPath)
                        print "Temp folder cleared successfully %s" %TempPath
                        thisLogger.info ("Temp folder cleared successfully %s" %TempPath)
                    Number_of_Retry=5              
            except Exception, e:
                ##if there is an exception due to reasons like 'file is in use' then retry for 5 times
                Number_of_Retry=Number_of_Retry+1
                print "Try# %d : Exception: %s " %(Number_of_Retry,e)
                thisLogger.warn ("Try# %d : Exception: %s " %(Number_of_Retry,e))
                continue



    ##function to clear MW GUI and API Clients Folders from VM 
    ##range of machines and path can be passed as arguments, if VM names are not passed as argument then it reads the config file for VM names
    def ClearMWClient(self,args):
        global thisLogger
        logname=inspect.stack()[0][3]
        self.SetupLogger(logname,"PyUtils")         
        try:
            sBasePath=args.ClientPath
            ##if range of VM is provided in the batch file or from the console
            if args.sMachineLow<>"":
            ##getting last 3 charachetrs of the VM name eg. 001 from LON14MSTST001
                sLow =args.sMachineLow[-3:]
                iLow=int(sLow)
                ##getting base name of VM eg. LON14MSTST
                sMachineBase=args.sMachineLow[:-3].upper()
                ##getting last three characters of the last machine in the range
                sHigh =args.sMachineHigh[-3:]
                ##taking int value for the loop  counter
                iHigh=int(sHigh)
                while iLow <= iHigh:
                    try:
                        ##formatting of machine name
                        sMachine= sMachineBase+str("%03d" %iLow)
                        ##Calling function to delete client file
                        self.Utilities_DeleteClientFiles(args.IgnorePath, args.Folder, sMachine,sBasePath)
                        ##inceasing the counter for the next machine's temp folder
                        iLow=iLow+1
                    except Exception, e:
                        print ("Error occurred while formatting machine name : %s" %e)
                        thisLogger.error ("Error occurred while formatting machine name : %s"%e)
            ##if list of vm is read from the config file
            else:
                if args.ConfigPath<>"":
                    config = ConfigParser.ConfigParser(allow_no_value=True)
                    config.read(args.ConfigPath)
                    ##getting machine names from config file
                    for sMachine in config.options('Machines_DeleteClientFolder'):
                        ##Calling function to delete client file
                        self.Utilities_DeleteClientFiles(args.IgnorePath, args.Folder, sMachine,sBasePath)
                else:
                    print "Please enter valid config path or machine name"
                    thisLogger.warn ("Please enter valid config path or machine name")
        except Exception, e:
            print "Failed to clear Client folders %s"%e
            thisLogger.error ("Failed to clear Client folders %s"%e)



    ## function to delete client files on VMs
    def Utilities_DeleteClientFiles(self, IgnorePath, Folder, sMachine, sBasePath):
        global thisLogger
        logname=inspect.stack()[0][3]
        self.SetupLogger(logname,"PyUtils")         
        try:
            ##formatting complete path for MW Client files
            sCompletePath="\\\%s\\%s"%(sMachine,sBasePath)
            ##listing all directories present under client path
            sDirectories = os.listdir(sCompletePath)                
            ##listing the MW client directories which need not to be deleted
            sIngnoreClient=(IgnorePath).split(',')
            for dir in sDirectories:
                if dir not in sIngnoreClient:
                    sCompletePath="\\\%s\\%s\\%s"%(sMachine,sBasePath,dir)
                    ##delete 32 or 64 bit folder is specified in config file, else delete all folders
                    if (Folder)<>"":
                        sSubdirectory=os.listdir(sCompletePath)
                        sSubdirectory[:]= filter(lambda x : x.startswith(Folder), sSubdirectory)
                        for subdir in sSubdirectory:
                            sCompletePathwithsubdir=os.path.join(sCompletePath,subdir)
                            print "deleting matching client folder %s" %(sCompletePathwithsubdir)
                            thisLogger.info ("Deleting matching client folder %s" %(sCompletePathwithsubdir))
                            shutil.rmtree(sCompletePathwithsubdir)
                            if os.listdir(sCompletePath)==[]:
                                print "Deleting Client %s as it is empty folder" %(sCompletePath)
                                thisLogger.info ("Deleting Client %s as it is empty folder" %(sCompletePath))
                                shutil.rmtree(sCompletePath)
                    else:
                        print "deleting client %s" %(sCompletePath)
                        thisLogger.info ("Deleting client %s" %(sCompletePath))
                        shutil.rmtree(sCompletePath)
        except Exception, e:
            print "failed to Clear client logs %s" %(e)
            thisLogger.error ("Failed to Clear client logs %s" %(e))


                
    ##function to restart the list of machines from config file or from range of VMs provided in command line
    def RestartMachines(self,args):
        global thisLogger
        logname=inspect.stack()[0][3]
        self.SetupLogger(logname,"PyUtils")         
        try:
            successful = False
            machine_list=[]
            ##if range of VM is provided in the batch file or from the console
            if args.sMachineLow<>"":
            ##getting last 3 charachetrs of the VM name eg. 001 from LON14MSTST001
                sLow =args.sMachineLow[-3:]
                iLow=int(sLow)
                ##getting base name of VM eg. LON14MSTST
                sMachineBase=args.sMachineLow[:-3].upper()
                ##getting last three characters of the last machine in the range
                sHigh =args.sMachineHigh[-3:]
                ##taking int value for the loop  counter
                iHigh=int(sHigh)
                while iLow <= iHigh:
                    try:
                        ##formatting of machine name
                        sMachine= sMachineBase+str("%03d" %iLow)
                        ##call to restart all machines in the range
                        self.Utilities_RebootMachines(sMachine)
                        ##inceasing the counter for the next machine's hostname
                        iLow=iLow+1
                        successful = True
                        if successful== True:
                            machine_list.append(sMachine)
                    except Exception, e:
                        print "error while restarting the machines in range"%(e)
                        thisLogger.error ("Error while restarting the machines in range"%(e))
            ##if list of VM is read from the config file
            else:        
                try:
                    if args.ConfigPath<>"":  
                        config = ConfigParser.ConfigParser(allow_no_value=True)
                        config.read(args.ConfigPath)
                        for sMachine in config.options('Machines_forRebooting'):
                            self.Utilities_RebootMachines(sMachine)
                            successful = True
                            if successful== True:
                                machine_list.append(sMachine)                            
                    else:
                        print "Please enter valid config path or machine name"
                        thisLogger.warn ("Please enter valid config path or machine name")
                except Exception, e:
                    print "Error while reading configuration file, path you provided is:%s \n%s"%(args.ConfigPath,e)
                    thisLogger.error ("Error while reading configuration file, path you provided is:%s \n%s"%(args.ConfigPath,e))
            args.sLogin = args.sLogin.strip().lower()
            if args.sLogin=="yes":
                try:
                    time.sleep(60) 
                    for sMachine in machine_list:
                        sMachine = sMachine.strip().lower()
                        self.Utilities_LoginMachines(sMachine,args.close)
                except Exception, e:
                        print "error while restarting the machines in range"%(e)
                        thisLogger.error ("Error while restarting the machines in range"%(e))                
        except Exception, e:
            print "Failed to reboot machine%s" %(e)
            thisLogger.error ("Failed to reboot machine%s" %(e))



    def Utilities_RebootMachines(self,sMachine,user=None, passwrd=None, msg="Machine Rebooting", timeout=0, force=1,reboot=1):
        global thisLogger
        logname=inspect.stack()[0][3]
        self.SetupLogger(logname,"PyUtils")         
        Number_of_Retry=0
        while Number_of_Retry<5:
            try:
                # Create an initial connection if a username & password is given.
                connected = 0
                if user and passwrd:
                    try:
                        win32wnet.WNetAddConnection2(win32netcon.RESOURCETYPE_ANY, None,''.join([r'\\', sMachine]), None, user,passwrd)
                    # Don't fail on error, it might just work without the connection.
                    except:
                        pass
                    else:
                        connected = 1
                # adding remote shutdown privileges.
                p1 = win32security.LookupPrivilegeValue(sMachine, win32con.SE_SHUTDOWN_NAME)
                p2 = win32security.LookupPrivilegeValue(sMachine,win32con.SE_REMOTE_SHUTDOWN_NAME)
                newstate = [(p1, win32con.SE_PRIVILEGE_ENABLED),(p2, win32con.SE_PRIVILEGE_ENABLED)]
                # Grab the token and adjust its privileges.
                htoken = win32security.OpenProcessToken(win32api.GetCurrentProcess(),win32con.TOKEN_ALL_ACCESS)
                win32security.AdjustTokenPrivileges(htoken, False, newstate)
                win32api.InitiateSystemShutdown(sMachine, msg, timeout, force, reboot)
                # Release the previous connection.
                if connected:
                    win32wnet.WNetCancelConnection2(''.join([r'\\', sMachine]), 0, 0)
                print "restarted %s successfully"%sMachine
                thisLogger.info ("Restarted %s successfully"%sMachine)
                Number_of_Retry=5
            except Exception, e:
                ##if there is an exception then retry
                Number_of_Retry=Number_of_Retry+1
                print "Try# %d : Exception: %s " %(Number_of_Retry,e)
                thisLogger.warn ("Try# %d : Exception: %s " %(Number_of_Retry,e))
                continue  


    ##function to login the list of machines from config file or from range of VMs provided in command line
    def LoginMachines(self,args):
        global thisLogger
        logname=inspect.stack()[0][3]
        self.SetupLogger(logname,"PyUtils")         
        try:
            ##if range of VM is provided in the batch file or from the console
            if args.sMachineLow<>"":
                ##getting last 3 charachetrs of the VM name eg. 001 from LON14MSTST001
                sLow =args.sMachineLow[-3:]
                iLow=int(sLow)
                ##getting base name of VM eg. LON14MSTST
                sMachineBase=args.sMachineLow[:-3].upper()
                ##getting last three characters of the last machine in the range
                sHigh =args.sMachineHigh[-3:]
                ##taking int value for the loop  counter
                iHigh=int(sHigh)
                machine_list=[]
                while iLow <= iHigh:
                    ##formatting of machine name
                    sMachine= sMachineBase+str("%03d" %iLow)
                    machine_list.append(sMachine)
                    iLow=iLow+1
                try:
                    print machine_list
                    for sMachine in machine_list:
                        sMachine = sMachine.strip().lower()
                        self.Utilities_LoginMachines(sMachine,args.close)
                except Exception, e:
                        print "error while restarting the machines in range"%(e)
                        thisLogger.error ("Error while restarting the machines in range"%(e))            
            ##if list of VM is read from the config file
            else:        
                try:
                    if args.ConfigPath<>"":  
                        config = ConfigParser.ConfigParser(allow_no_value=True)
                        config.read(args.ConfigPath)
                        for sMachine in config.options('Machines_forLogin'):
                            sMachine = sMachine.strip().lower()
                            self.Utilities_LoginMachines(sMachine,args.close)
                    else:
                        print "Please enter valid config path or machine name"
                        thisLogger.warn ("Please enter valid config path or machine name")
                except Exception, e:
                    print "Error while reading configuration file, path you provided is:%s \n%s"%(args.ConfigPath,e)
                    thisLogger.error ("Error while reading configuration file, path you provided is:%s \n%s"%(args.ConfigPath,e))
        except Exception, e:
            print "Failed to login machine%s" %(e)
            thisLogger.error ("Failed to login machine%s" %(e))            
            
            
    def Utilities_LoginMachines(self, sMachine, sCw):
        global thisLogger
        logname=inspect.stack()[0][3]
        self.SetupLogger(logname,"PyUtils")         
        try:
            os.system(r"W:\NFT\tools\win\AutomaticLogin\WinLogin_RDP.exe %s %s" %(sCw,sMachine))
            print "%s Logged in successfully" %sMachine
        except Exception, e:
            print "Failed to login %s %s " %(sMachine, e)
        

    def Exitfun(self):
        pass            

if __name__ == "__main__":
        starttime=time.time()
        ##Create instance of class PythonUtilities
        objUtilities=PySparrowUtilities()
        parser = argparse.ArgumentParser(description='Pass function name and arguments')
        subparsers = parser.add_subparsers(dest='functions', help='These are the function names, for argument help enter function name and -h, E.G. Fun -h')

        ##creating subparser and arguments for function CompressLogs
        parser_CompressLogs=subparsers.add_parser('CompressLogs') 
        parser_CompressLogs.set_defaults(func = objUtilities.CompressLogs)
        parser_CompressLogs.add_argument('-l',dest='LogsPath', default="\\c$\Perl\Driver\Logs", help='Path for Logs, Default is: \\\\VCAT\c$\Perl\site\lib\Driver\Logs')
        parser_CompressLogs.add_argument('-i',dest='IgnorePath', default="QTPScreenshots", help='Folder to be ignored, Default is: QTPScreenshots')        
        parser_CompressLogs.add_argument('-d', dest='DAYS_TO_ARCHIVE', type=int, default=1, help='Compress files older than how many days?default is 1.')

        ##creating subparser and arguments for function DeleteLogs
        parser_DeleteLogs=subparsers.add_parser('DeleteLogs') 
        parser_DeleteLogs.set_defaults(func = objUtilities.DeleteLogs)
        parser_DeleteLogs.add_argument('-l',dest='LogsPath', default="\\Driver\Logs", help='Path for Logs, Default is:  \\\\VCAT\c$\Perl\site\lib\Vocollect\Sparrow\Driver\Logs')
        parser_DeleteLogs.add_argument('-i',dest='IgnorePath', default='', help='Folder to be ignored, Default is kept blank but ideally should be QTPScreenshots which is passed from the batch file')        
        parser_DeleteLogs.add_argument('-d', dest='DAYS_TO_DELETE', type=int, default=30, help='Delete files older than how many days?Default is 30.')
        parser_DeleteLogs.add_argument('-dcl', dest='DAYS_TO_DELETE_CL', type=int, default=7, help='Delete Client logs files older than how many days?Default is 7.')

        ##creating subparser and arguments for function ClearTemp
        parser_ClearTemp=subparsers.add_parser('ClearTemp') 
        parser_ClearTemp.set_defaults(func = objUtilities.ClearTemp)
        parser_ClearTemp.add_argument('-t',dest='TempPath', default='c$\Users\Administrator\AppData\Local\Temp', help='enter the Temp path to be cleared, please ensure to change C: as C$. Default Path is: c$\Users\Administrator\AppData\Local\Temp')
        parser_ClearTemp.add_argument('-gettemp', dest='sGetTemp', default='No', help='Pass a Yes if you want to get machines temp location through function')
        parser_ClearTemp.add_argument('-fm', dest='sMachineLow', default='', help='enter first VM name in the range E.G. LON14MSTST001, leave it if you want to use list of VM from Config File')
        parser_ClearTemp.add_argument('-lm', dest='sMachineHigh', default='', help='enter last VM name in the range E.G. LON14MSTST010, leave it if you want to clear logs on single machine')
        parser_ClearTemp.add_argument('-c', dest='ConfigPath', default='', help='Add config path, example: \\ukrobot\PyUtilities_Configuration.cfg')
        parser_ClearTemp.add_argument('-f', dest='FilePath', default='', help='Add text File path, example: C:\Temp\SmokeMachines.txt')

        ##creating subparser and arguments for function RestartMachines
        parser_RestartMachines=subparsers.add_parser('RestartMachines') 
        parser_RestartMachines.set_defaults(func = objUtilities.RestartMachines)
        parser_RestartMachines.add_argument('-fm', dest='sMachineLow', default='', help='enter first VM name in the range E.G. LON14MSTST001, leave it if you want to reboot list of VM from Config File')
        parser_RestartMachines.add_argument('-lm', dest='sMachineHigh', default='', help='enter last VM name in the range E.G. LON14MSTST010, leave it if you want to reboot a single machine')
        parser_RestartMachines.add_argument('-c', dest='ConfigPath', default='', help='Add config path, example: \\ukrobot\PyUtilities_Configuration.cfg')
        parser_RestartMachines.add_argument('-login', dest='sLogin', default='No', help='Provide yes or no if you want to login to machine after reboot, default is No')
        parser_RestartMachines.add_argument('-cw',dest='close', default="close", help='parameter to close window after login')

        ##creating subparser and arguments for function ClearMWClient
        parser_ClearMWClient=subparsers.add_parser('ClearMWClient') 
        parser_ClearMWClient.set_defaults(func = objUtilities.ClearMWClient)
        parser_ClearMWClient.add_argument('-fm', dest='sMachineLow', default='', help='enter first VM name in the range E.G. LON14MSTST001, leave it if you want to use list of VM from Config File')
        parser_ClearMWClient.add_argument('-lm', dest='sMachineHigh', default='', help='enter last VM name in the range E.G. LON14MSTST010, leave it if you want to delete client files on single machine')        
        parser_ClearMWClient.add_argument('-cp',dest='ClientPath', default="C$\Clients", help='Path for Logs, Default is:  C:\Clients')
        parser_ClearMWClient.add_argument('-i',dest='IgnorePath', default='', help='Folder to be ignored, Default is kept blank but it could be a client version like "SW_9_2...."')
        parser_ClearMWClient.add_argument('-c', dest='ConfigPath', default='', help='Add config path, example: \\ukrobot\PyUtilities_Configuration.cfg')
        parser_ClearMWClient.add_argument('-f', dest='Folder', default='', help='Adding 32 bit or 64 bit folder name to be deleted, example: -f 32, if not passed then all subfolders will be deleted')


        ##creating subparser and arguments for function LoginMachines
        parser_LoginMachines=subparsers.add_parser('LoginMachines') 
        parser_LoginMachines.set_defaults(func = objUtilities.LoginMachines)
        parser_LoginMachines.add_argument('-fm', dest='sMachineLow', default='', help='enter first VM name in the range E.G. LON14MSTST001, leave it if you want to use list of VM from Config File')
        parser_LoginMachines.add_argument('-lm', dest='sMachineHigh', default='', help='enter last VM name in the range E.G. LON14MSTST010, leave it if you want to delete client files on single machine')        
        parser_LoginMachines.add_argument('-cw',dest='close', default="close", help='parameter to close window after login')
        parser_LoginMachines.add_argument('-c', dest='ConfigPath', default='', help='Add config path, example: \\ukrobot\Utilities\PyUtilities_Configuration.cfg')

        ##parse the arguments and call whichever function was selected
        args = parser.parse_args()
        ##This is only for ClearTemp and RestartMachine functions if last machine in the range is not specified then treat first machine as single machine
        if args.functions=='ClearTemp'or args.functions=='RestartMachines' or args.functions=='ClearMWClient' or args.functions=='LoginMachines':
            if args.sMachineHigh=='': args.sMachineHigh=args.sMachineLow                 
        args.func(args)

        print 'Total Time Taken : ', time.time()- starttime, 'seconds for', args.functions
