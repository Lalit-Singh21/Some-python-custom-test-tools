import os

x = '\\
y = r'\\

#x=os.path.join("r",x)

#a='\nu + \lambda + \theta'; 
#b=a.replace(r"\\",r"\\\\"); 
#c='%r' %a; 
#d=a.encode('string_escape');


#x = x.encode('unicode-escape')
#x = x.encode('utf-8')
x = x.encode('string-escape')
print x

if os.path.exists(x):
    print "pass"

def covert_unc(host, path):
    """ Convert a file path on a host to a UNC path."""
    return ''.join(['\\\\', host, '\\', path.replace(':', '$')])

#if os.path.exists(covert_unc('it',dest_dir_build)):
