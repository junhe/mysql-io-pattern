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


def scan_trace(tracepath):
    f = open(tracepath, 'r')
    unfinished_dic = {} #indexed by call name
    entrylist = []
    for line in f:
        #print line
        line = line.strip()
        if match_line(line):
            # normal line
            entrylist.append( line_to_dic(line) )
        #elif 'unfinished' in line: # 
        elif line.endswith(UNFINISHED_MARK):
            udic = get_dic_from_unfinished(line)
            #print udic
            unfinished_dic[udic['callname']] = udic
            #pprint.pprint(unfinished_dic)
        elif 'resumed' in line:
            udic = get_dic_from_resumed(line)
            name = udic['callname']
            completeline = unfinished_dic[name]['trimedline'] +\
                            udic['trimedline']
            #print completeline
            dic = line_to_dic(completeline)
            entrylist.append( dic )
            del unfinished_dic[name]
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


