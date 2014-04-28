import sys,os
import pprint
import glob
import re

UNFINISHED_MARK = '<unfinished ...>'

def match_line(line):
    mo = re.match(r'(\S+)\s+(\S+)\s+(\w+)\((.+)\)\s+=\s+(\S+)',
    #mo = re.match(r'(\S+)\s+(\w+)\((.+)\)\s+=\s+(\S+)',
                  line)
    return mo

def line_to_dic(line):
    """
    This function only handles normal line.
    It does not handle interrupted lines.    
    """
    dic = {
            'pid'  :None,
            'time' :None,
            'callname': None,
            'args':None,
            'ret' :None,
          }
    line = line.replace('"', '')
    mo = match_line(line)

    #fdmap = {}
    if mo:
        #print mo.groups()
        i = 1
        dic['pid'] = mo.group(i)
        i += 1
        dic['time'] = mo.group(i)
        i += 1
        dic['callname'] = mo.group(i)
        i += 1
        dic['args'] = mo.group(i).split(',')
        i += 1
        dic['ret'] = mo.group(i)
        dic['original_line'] = line
        #if dic['callname'] == 'open':
        #if dic['callname'] == 'fsync':
            #print dic
        #try:
            #if dic['callname'] == 'open':
                ##print line
                #fdmap[ dic['ret'] ] = dic['args'][0]
                ##print fdmap
            #elif dic['callname'] == 'close':
                ##print line
                #del fdmap[ dic['args'][0] ]
        #except:
            #print fdmap
            #print 'error:', line
    else:
        print 'cannot parse:', line
    
    return dic

def get_dic_from_unfinished(line):
    """
    line has to be .... <unfinished ...>
    """
    mo = re.match(r'(\S+)\s+(\S+)\s+(\w+)\(',
                    line)
    dic = {}
    if mo:
        #print mo.groups()
        i = 1
        dic['pid'] = mo.group(i)
        i += 1
        dic['time'] = mo.group(i)
        i += 1
        dic['callname'] = mo.group(i)

    n = len(line)
    m = len(UNFINISHED_MARK)
    dic['trimedline'] = line[:(n-m)]

    return dic

def get_dic_from_resumed(line):
    """
    line has to be .... <... xxxx resumed>
    """
    mo = re.match(r'(\S+)\s+(\S+)\s+\<\.\.\. (\S+) resumed\>',
                    line)
    dic = {}
    if mo:
        #print mo.groups()
        i = 1
        dic['pid'] = mo.group(i)
        i += 1
        dic['time'] = mo.group(i)
        i += 1
        dic['callname'] = mo.group(i)

    # remove all chars before resumed>
    trimedline = re.sub(r'.*\<\.\.\. \S+ resumed\>', "", line)
    dic['trimedline'] = trimedline

    return dic

def maintain_filepath(fdmap, entrydict):
    """
    if entrydict is open:
        add the fd->path mapping to fdmap
    else if entrydict is close:
        remove the fd->path mapping to fdmap
    else if entrydict is read,write,...         
        get filepath from fdmap by the fd
    add 'filepath' to entrydict
    """
    callname = entrydict['callname']
    pid = entrydict['pid']
    filepath = None

    print entrydict['original_line']
    if callname == 'open':
        filepath = entrydict['args'][0]
        fd = entrydict['ret']
        if not fdmap.has_key(pid):
            fdmap[pid] = {}
        fdmap[pid][fd] = filepath
    elif callname == 'close':
        fd = entrydict['args'][0]
        if fdmap.has_key(pid) and fdmap[pid].has_key(fd):
            filepath = fdmap[pid][fd]
            del fdmap[pid][fd]
    elif callname in \
            ['write', 'read', 'pwrite', 'pread', 'fsync']:
        fd = entrydict['args'][0]
        if fdmap.has_key(pid) and fdmap[pid].has_key(fd):
            filepath = fdmap[pid][fd]

    entrydict['filepath'] = filepath

def scan_trace(tracepath):
    f = open(tracepath, 'r')
    unfinished_dic = {} #indexed by call name
    entrylist = []
    fdmap = {}
    for line in f:
        #print line
        line = line.strip()
        if match_line(line):
            # normal line
            entrydict = line_to_dic(line) 
        #elif 'unfinished' in line: # 
        elif line.endswith(UNFINISHED_MARK):
            udic = get_dic_from_unfinished(line)
            unfinished_dic[udic['callname']] = udic
            continue
        elif 'resumed' in line:
            udic = get_dic_from_resumed(line)
            name = udic['callname']
            completeline = unfinished_dic[name]['trimedline'] +\
                            udic['trimedline']
            #print completeline
            entrydict = line_to_dic(completeline)
            del unfinished_dic[name]

        entrylist.append( entrydict )
        maintain_filepath( fdmap, entrydict )



    f.close()
    pprint.pprint( entrylist )

def main():
    traceprefix = sys.argv[1]
    filelist = glob.glob(traceprefix+"*")
    #print filelist
    for filepath in filelist:
        print filepath
        scan_trace(filepath)
        #break
    #line_to_dic('7499  1396728590.779812 open("./mysql/func.MYD", O_RDWR) = 30')

if __name__ == '__main__':
    main()


