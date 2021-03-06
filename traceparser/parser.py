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
    filepath = 'NA'
    offset   = 'NA'
    length   = 'NA'

    if entrydict['ret'] == '-1':
        # failed..
        entrydict['filepath'] = filepath
        entrydict['offset'] = offset
        entrydict['length'] = length
        return

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
    elif callname == 'unlink':
        filepath = entrydict['args'][0]
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
                offset = int(entrydict['ret'])
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
    #entrylist = []
    filep = {}

    tablefile = open(tracepath+'.table', 'w')
    header=['pid', 'time', 'callname',
            'offset', 'length', 'filepath', 'trace_name']
    tablefile.write( " ".join(header) + "\n" )

    trace_name = os.path.basename(tracepath)

    cnt = 0
    for line in f:
        #print line,
        if cnt % 5000 == 0:
            print '.',
            cnt += 1
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
                continue
                #raise

        #entrylist.append( entrydict )
        maintain_filep( filep, entrydict )

        rowlist = []
        entrydict['trace_name'] = trace_name
        for col in header:
            rowlist.append(entrydict[col])

        rowlist = [ str(x) for x in rowlist ]
        tablefile.write( " ".join(rowlist) + "\n" )

    f.close()
    #pprint.pprint( entrylist )
    tablefile.close()

def main():
    if len(sys.argv) != 2:
        print 'usage: python', sys.argv[0], 'tracepath'
    filepath = sys.argv[1]
    print 'Doing', filepath, '...........'
    df = scan_trace(filepath)

if __name__ == '__main__':
    main()


