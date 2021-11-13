import os
import os.path
import shutil
import sys
import win32wnet
import time
import datetime
import datetime
import glob
import multiprocessing
#import gc
#import disutils.dir_util

Create_Test_Status = False

def netcopy(host, source, dest_dir, username=None, password=None, move=False):
    """ Copies files or directories to a remote computer. """
    
    #wnet_connect(host, username, password)
            
    #dest_dir = covert_unc(host, dest_dir)

    # Pad a backslash to the destination directory if not provided.
    if not dest_dir[len(dest_dir) - 1] == '\\':
        dest_dir = ''.join([dest_dir, '\\'])

    if move:
        if os.path.isdir(source):
            shutil.copytree(source, dest_dir)
            shutil.rmtree(source)
        elif os.path.isfile(source):
            shutil.move(source, dest_dir)
        else:
            raise AssertionError, '%s is neither a file nor directory' % (source)
    else:
        if os.path.isdir(source):
            os.system(r'XCOPY "%s" "%s" /s /i /y' %(source, dest_dir))
        elif os.path.isfile(source):
            shutil.copy(source, dest_dir)
        else:
            raise AssertionError, '%s is neither a file nor directory' % (source)


def covert_unc(host, path):
    """ Convert a file path on a host to a UNC path."""
    path = '\\\\'+path.replace('\\', "\\\\")
    path = ''.join(['\\\\', host, path.replace(':', '$')])
    #print "covert_unc path is: ", path
    return path


    
def wnet_connect(host, username, password):
    unc = ''.join(['\\\\', host])
    try:
        win32wnet.WNetAddConnection2(0, None, unc, None, username, password)
    except Exception, err:
        if isinstance(err, win32wnet.error):
            # Disconnect previous connections if detected, and reconnect.
            if err[0] == 1219:
                win32wnet.WNetCancelConnection2(unc, 0, 0)
                return wnet_connect(host, username, password)
        raise err


def get_newestlogs_old(machine,logpath):
    retry = 0
    username = "random\sqa"
    password = "qaM1ssion"
    while (retry<5):
        try:
            path = covert_unc(machine, logpath)
            #all_subdirs = [d for d in os.listdir(path) if os.path.isdir(d)]
            all_subdirs = list_all_dirs(path)
            #print all_subdirs
            latest_subdir = max(all_subdirs, key=os.path.getmtime)
            #print latest_subdir
            return latest_subdir
        except Exception, e:
            print e
            wnet_connect(machine, username, password)
            retry+=1
            continue

def get_newestlogs(machine,logpath):
    retry = 0
    username = "random\sqa"
    password = "qaM1ssion"
    latest_subdirs = []
    while (retry<10):
        try:
            path = covert_unc(machine, logpath)
            #print path
            #all_subdirs = [d for d in os.listdir(path) if os.path.isdir(d)]
            all_subdirs = list_all_dirs(path)
            #print all_subdirs
            #taking top five latest logs, to ensure there is no data loss
            for i in range(3):
                latest_subdir = max(all_subdirs, key=os.path.getmtime)
                all_subdirs.remove(latest_subdir)
                #print "latest {0} : {1}".format(i,latest_subdir)
                latest_subdirs.append(latest_subdir)
            return latest_subdirs
        except Exception, e:
            print e
            wnet_connect(machine, username, password)
            retry+=1
            continue

def list_all_dirs(b):
  result = []
  for d in os.listdir(b):
    bd = os.path.join(b, d)
    if os.path.isdir(bd): result.append(bd)
  return result


def check_file_exists_old(path,b='.xml'):
    #print "check file exists",path
    keep_waiting = True
    iCount = 0
    while keep_waiting:
        text_files = [f for f in os.listdir(path) if f.endswith(b)]
        if text_files != []:
            return True
        else:
            time.sleep(1)
            iCount += 1
            if iCount == 9999999:
                keep_waiting = False


def check_file_exists(path,extension='.xml'):
    #print "check file exists",path
    keep_waiting = True
    now = time.time()
    global Create_Test_Status
    #two_day_ago = 60*60*24*2
    fifteen_min_ago = now - 60*5   #15, putting 5 minutes for now
    #print now, fifteen_min_ago
    while keep_waiting:
        text_files = [f for f in os.listdir(path) if f.endswith(extension)]
        if text_files != []:
            print "xml exists"
            Create_Test_Status = True
            return True
        else:
            print "xml dosent exist, wait for modification wait time check"
            log_path  = os.path.join(path, os.path.basename(path)+".log")
            fileCreation = os.path.getctime(path)
            fileModification = os.path.getmtime(log_path)
            print "path:",log_path
            print "fileCreation        :{0}, \nfileModification   :{1}, \ncurrent time      :{2}, \nfive_min_ago    :{3}".format(datetime.datetime.fromtimestamp(fileCreation).strftime('%Y-%m-%d %H:%M:%S'), datetime.datetime.fromtimestamp(fileModification).strftime('%Y-%m-%d %H:%M:%S'), datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),datetime.datetime.fromtimestamp(fifteen_min_ago).strftime('%Y-%m-%d %H:%M:%S'))
            #print "path:",path
            if fileModification < fifteen_min_ago:
                print "file modified 15 min before"
                Create_Test_Status = True
            keep_waiting = False
            return True
##            else:
##                print "file modification in progress"
##                time.sleep(10)


def runMultiProcess(process_list,funcname,src,dest,log_server):
    import multiprocessing as mp
    process_list= filter(None, process_list)
    pool = mp.Pool()
    #pool = Pool(processes=len(process_list)+1)
    pool_len = len(process_list)
    try:
        for i,process in enumerate(process_list):
            #result = pool.apply_async(funcname, (process,src,dest))
            pool.apply_async(funcname,args = (process,src,dest,log_server,),callback = None)    
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        print "error through keyboard interrupt"


def runMultiProcess_old(process_list,funcname,src,dest,log_server):               
    process_list= filter(None, process_list) 
    try:
        procs = []
        for process in process_list:
            #print "process", process
            procs.append(multiprocessing.Process(target=funcname, args=(process,src,dest,log_server)))
            procs[-1].daemon = True
            procs[-1].start()
            procs[-1].join()
    except KeyboardInterrupt:
        for p in procs:
            p.start()

def get_device_code_version(filename):
    code_version_text = "Device Code Version:"
    try:
        f = open(filename,'r')
        #file_contents = f.readlines()
        for line in f.readlines():
            if code_version_text in line:
                code_version = str((line.split("Version:")[1]).strip().translate(None, "'"))
                break
        return code_version
    except Exception, e:
        print "could not get the code version:",filename,e

    
def move_logs(machine, sparrow_logs, dest,log_server):
    machines = {'10.78.124.48':"VCAT1",'10.78.124.86':"VCAT3",'10.78.124.35':"VCAT4",'10.78.124.66':"VCAT5",'10.78.124.81':"VCAT6"}
    latest_sparrow_logs_list = get_newestlogs(machine,sparrow_logs)
    
    #print "move logs,machines", machines[machine]
    #print sparrow_log_path
    global Create_Test_Status
    for sparrow_log_path in reversed(list(latest_sparrow_logs_list)):
        try:
            if check_file_exists(sparrow_log_path):
                os.chmod(os.path.dirname(sparrow_log_path), 0777)
                #build_number = get_device_code_version(sparrow_log_path)
                source_dir = os.path.basename(sparrow_log_path)
                build_number = get_device_code_version(os.path.join(sparrow_log_path,source_dir+".log"))
                if build_number == None:
                    build_number = "IncompleteLogs_CanBeRemoved"

                if "IncompleteLogs_CanBeRemoved" not in build_number:
                    dest_dir_builds = [(os.path.join(dest,build_number)),(os.path.join(dest,build_number+"__"+datetime.datetime.now().strftime('%Y-%m-%d')))]
                else:
                    dest_dir_builds = [(os.path.join(dest,build_number))]

                for dest_dir_build in dest_dir_builds:                    
                    dest_dir_build = covert_unc(log_server,dest_dir_build)
                    print "#####dest_dir_build#######",dest_dir_build
                    dest_dir_machine = os.path.join(dest_dir_build, machines[machine])
                    dest_dir_log = os.path.join(dest_dir_machine,source_dir)
                    print "#####dest_dir_machine#######",dest_dir_machine
                    print "#####dest_dir_log#######",dest_dir_log
                    
                    if os.path.exists(dest_dir_build):
                        print "build folder exists:",dest_dir_build
                        os.chmod(os.path.dirname(dest_dir_build), 0777)
                        
                        #dest_dir_machine = covert_unc(log_server,dest_dir_machine)
                        if os.path.exists(dest_dir_machine):
                            os.chmod(os.path.dirname(dest_dir_machine), 0777)
                            print "machine folder exists:",dest_dir_machine
                            #this needs to be improved later (check log folder exists then copy)
                            #if not os.path.exists(dest_dir_log):
                            #print "log folder not exists",dest_dir_log
                            netcopy(log_server, sparrow_log_path, dest_dir_log)
                            Create_Test_Status = True
                        else:
                            print "machine folder not exists:",dest_dir_machine
                            os.makedirs(dest_dir_machine)
                            #print sparrow_log_path, dest_dir_log
                            netcopy(log_server, sparrow_log_path, dest_dir_log)
                            Create_Test_Status = True

                    else:
                        os.chmod(os.path.dirname(dest_dir_build), 0777)
                        print "build folder not exists:",dest_dir_build
                        os.makedirs(dest_dir_build)
                        os.makedirs(dest_dir_machine)
                        netcopy(log_server, sparrow_log_path, dest_dir_log)
                        Create_Test_Status = True

                    try:
                        if Create_Test_Status == True:
                            os.system(r"C:\Python27\python.exe {0} {1}".format(os.path.join(os.getcwd(),"testSuiteStatus.py"),dest_dir_build))
                            Create_Test_Status = False
                    except Exception, e:
                        print "failed to create the csv:",e
                        continue
        except:
            continue

if __name__ == '__main__':
    #machines = ['10.78.124.48','10.78.124.86','10.78.124.35','10.78.124.81']
    global machines
    machines = ['10.78.124.48','10.78.124.86']
    sparrow_logs = r'c:\Perl\site\lib\random\Sparrow\Driver\Logs'
    device_logs = ""
    console_logs = ""
    #dest = r"linuxshare\logs_dashboard\six_sigma\folders"
    dest = r"folders"
    log_server = "ie4biw66sjs62.random.int" #New windows server
    runMultiProcess(machines,move_logs,sparrow_logs,dest,log_server)
    #gc.collect()

