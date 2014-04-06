import sys,os
import re

def line_to_dic(line):
    dic = {
            'pid'  :None,
            'time' :None,
            'callname': None,
            'args':None,
            'ret' :None,
          }
    line = line.replace('"', '')
    mo = re.match(r'(\S+)\s+(\S+)\s+(\w+)\((.+)\)\s+=\s+(\S+)',
                  line)
    if mo:
        #print mo.groups()
        dic['pid'] = mo.group(1)
        dic['time'] = mo.group(2)
        dic['callname'] = mo.group(3)
        dic['args'] = mo.group(4).split(',')
        dic['ret'] = mo.group(5)
        #if dic['callname'] == 'open':
        if dic['callname'] == 'fsync':
            print dic

def scan_trace(tracepath):
    f = open(tracepath, 'r')
    for line in f:
        #print line
        line_to_dic(line)
    f.close()

def main():
    tracepath = sys.argv[1]
    scan_trace(tracepath)
    #line_to_dic('7499  1396728590.779812 open("./mysql/func.MYD", O_RDWR) = 30')

if __name__ == '__main__':
    main()




