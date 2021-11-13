import os
import sys
import re
import collections
import win32wnet

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
    
create_error_log = False
def parseSparrowLogs(log_file):
    data = []
    error_texts = ["(FATAL step encountered)...","|FAILURE", "|FATAL"]
    #root = log_file[:log_file.index(os.sep)] if os.sep in log_file else log_file
    #root = log_file.split("\\")[2]
    #wnet_connect(root, "user", "Talkman1")
    os.chmod(os.path.dirname(log_file), 0777)
    with open(log_file, 'r') as fh:
        data = fh.readlines()
        create_error_log = True
        output_error_log_file = os.path.dirname(log_file)+"\log_error.log"
        if not os.path.isfile(output_error_log_file):
            open(output_error_log_file, 'w').close() 
        if create_error_log:
            failure_count = 0
            failedscript_list = []
            unique = ([])
            try:
                with open(output_error_log_file, 'w') as the_file:
                    for index in range(len(data)):
                        line = data[index].rstrip() 
                        try:
                            for error_text in error_texts:
                                #print error_text
                                if error_text in line:
                                    #line_list = line.split()
                                    #wont work if error line does not have script path
                                    #for failed_script_name in filter (lambda x: ".pl" in x, line_list):pass
                                        for k in range(index,-1,-1):
                                            if "*** Execution Start:" in data[k]:
                                                failed_script_name = os.path.basename((data[k].split("Development")[-1:])[0].split("***")[0])
                                                if failed_script_name not in failedscript_list:
                                                    the_file.write('******************************************************************************\n') 
                                                    the_file.write("Failed Script # {0} :: {1}\n".format(len(unique)+1,failed_script_name))
                                                    the_file.write('******************************************************************************\n')
                                                    the_file.write('******************************************************************************\n') 
                                                failedscript_list.append(failed_script_name)
                                                unique = set (failedscript_list)
                                                break
                                        if index >= 4:
                                            if index <= len(data) - 4:
                                                icounter = index - 4
                                                for i in range(0,9):                         
                                                    #print(data[icounter].rstrip())
                                                    the_file.write ("{0}\n".format(data[icounter].rstrip()))
                                                    icounter += 1
                                            else:
                                                if index < len(data):
                                                    lcounter = index - 4
                                                    for i in range(0,5):
                                                        #print(data[lcounter].rstrip())
                                                        the_file.write ("{0}\n".format(data[lcounter].rstrip()))
                                                        lcounter += 1
                                            #print('---')
                                            the_file.write('---\n')
                                        else:
                                            for j in range(0,5):
                                                #print(data[j].rstrip())
                                                the_file.write(data[j].rstrip(),"\n")
                                                j += 1
                                            #print('---')
                                            the_file.write('---\n')
                        except Exception,e:
                            print e
                                #Number_of_Retry=Number_of_Retry+1
                                #print "Try# %d : Exception: %s " %(Number_of_Retry,e)
                                #continue
                    return failedscript_list
            except Exception, e:
                print e
        
if __name__ == "__main__":
    log_file = sys.argv[1].strip()
    x = parseSparrowLogs(log_file)
    #print "Failed Scripts: {0}".format(x)
    
