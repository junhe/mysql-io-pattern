import sys,os
import pprint
import glob
import re

import dataframe

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
        args = mo.group(i).split(',')
        dic['args'] = [ x.strip() for x in args ]
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

def maintain_filep(filep, entrydict):
    """
    structure of filep =
                    {
                      pid001: {
                        fd001: {
                                 'filepath':
                                 'pos':
                               }
                              }
                    }

    ########### OLD ###############
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
    offset   = None
    length   = None

    #print entrydict['original_line']
    if callname == 'open':
        filepath = entrydict['args'][0]
        fd = entrydict['ret']
        if not filep.has_key(pid):
            filep[pid] = {}
        if not filep[pid].has_key(fd):
            filep[pid][fd] = {}
        filep[pid][fd]['filepath'] = filepath
        filep[pid][fd]['pos']      = 0
    elif callname == 'openat':
        filepath = entrydict['args'][1]
        fd = entrydict['ret']
        if not filep.has_key(pid):
            filep[pid] = {}
        if not filep[pid].has_key(fd):
            filep[pid][fd] = {}
        filep[pid][fd]['filepath'] = filepath
        filep[pid][fd]['pos']      = 0
    elif callname == 'accept':
        filepath = 'NETWORK'
        fd = entrydict['ret']
        if not filep.has_key(pid):
            filep[pid] = {}
        if not filep[pid].has_key(fd):
            filep[pid][fd] = {}
        filep[pid][fd]['filepath'] = filepath
        filep[pid][fd]['pos']      = 0
    elif callname == 'clone':
        newpid = entrydict['ret']
        if 'CLONE_FILES' in entrydict['args'][1]:
            filep[newpid] = filep[pid]
            
    elif callname in ['dup', 'dup2', 'dup3']:
        newfd = entrydict['ret']
        assert newfd != '-1'
        oldfd = entrydict['args'][0]
        if filep[pid].has_key(oldfd):
            filep[pid][newfd] = filep[pid][oldfd]
        else:
            print 'dup() an non-existing oldfd'
            exit(1)

        fd = oldfd
        try:
            filepath = filep[pid][fd]['filepath']
        except:
            filepath = fd
    elif callname == 'close':
        fd = entrydict['args'][0]
        try:
            filepath = filep[pid][fd]['filepath']
            del filep[pid][fd]
        except:
            filepath = fd
    elif callname in \
            ['write', 'read', 'pwrite', 'pread', 'fsync', 'lseek']:
        fd = entrydict['args'][0]
        try:
            filepath = filep[pid][fd]['filepath']
        except Exception as ex:
            pprint.pprint( entrydict )
            pprint.pprint( filep )
            print ex

            filepath = fd

        try:
            if callname in ['write', 'read']:
                offset = filep[pid][fd]['pos']
                length = int(entrydict['ret'])
                filep[pid][fd]['pos'] = offset + length
            elif callname in ['pread', 'pwrite']:
                # they don't affect filep offset 
                offset = int(entrydict['args'][3])
                length = int(entrydict['ret'])
            elif callname in ['lseek']:
                #whence = entrydict['args'][2]
                #offset = int(entrydict['args'][1])
                filep[pid][fd]['pos'] = int(entrydict['ret'])
        except Exception as ex:
            pass
            #print ex
            #pprint.pprint( entrydict )
            #pprint.pprint( filep )
            #raise

    entrydict['filepath'] = filepath
    entrydict['offset'] = offset
    entrydict['length'] = length

def scan_trace(tracepath):
    f = open(tracepath, 'r')
    unfinished_dic = {} #indexed by call name
    entrylist = []
    filep = {}

    df = dataframe.DataFrame(
            header=['pid', 'time', 'callname', 'filepath', 'offset', 'length'],
            table =[])

    for line in f:
        print line,
        line = line.strip()
        if match_line(line):
            # normal line
            entrydict = line_to_dic(line) 
        #elif 'unfinished' in line: # 
        elif line.endswith(UNFINISHED_MARK):
            #print 'unfinished line:', line 
            udic = get_dic_from_unfinished(line)
            unfinished_dic[(udic['pid'], udic['callname'])] = udic
            continue
        elif 'resumed' in line:
            #print 'resumed line:', line 
            udic = get_dic_from_resumed(line)
            name = udic['callname']
            pid = udic['pid']
            try:
                completeline = unfinished_dic[(pid, name)]['trimedline'] +\
                            udic['trimedline']
                entrydict = line_to_dic(completeline)
                del unfinished_dic[(pid, name)]
            except Exception as ex:
                print ex
                print unfinished_dic
                raise

        entrylist.append( entrydict )
        maintain_filep( filep, entrydict )

        rowdic = {}
        for col in df.header:
            rowdic[col] = entrydict[col]

        df.addRowByDict( rowdic )

    print df.toStr()
    f.close()
    #pprint.pprint( entrylist )

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


