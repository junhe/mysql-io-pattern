import subprocess
import os
import sys
import time

def start_mysqld(tracepath):
    cmd = ['strace',
           '-o', tracepath,
           '-f', '-ttt',
           #'-ff',
           '-e', 'trace=open,close,fsync,sync,read,'\
                 'write,pread,pwrite,lseek,unlink,fcntl,mmap,munmap,'\
                 'dup,dup2,dup3,fork,vfork',
           '-s', '8',
           'mysqld',
           '--innodb-thread-concurrency=1',
           '--innodb-write-io-threads=1',
           '--max-delayed-threads=1',
           '--performance-schema-max-thread-instances=1',
           '--thread-cache-size=1']
    subprocess.Popen(cmd)

def stop_mysqld():
    cmd = "mysqladmin -u root shutdown"
    cmd = cmd.split()
    subprocess.call(cmd)

def run_script(scriptname):
    subprocess.call(['python', scriptname])

def run_one_bench(targetdir, scriptname):
    start_mysqld( os.path.join(targetdir, scriptname+'.trace') )
    time.sleep(2)
    run_script(scriptname)
    time.sleep(2)
    subprocess.call(['sync'])
    stop_mysqld()
    subprocess.call(['sync'])
    time.sleep(2)

def test_main(targetdir):
    if not os.path.exists(targetdir):
        os.makedirs(targetdir)

    scriptlist = [
            'cleanup.py',
            'create_table.py',
            'get_version.py',
            'retrieving_data.py',
            #dictionary_cursor.py  
            'insert_image.py',
            'read_image.py',
            'prepared_statement.py']
    for scriptname in scriptlist:
        run_one_bench(targetdir, scriptname)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'usage:', sys.argv[0], 'targetdir'
        exit(1)
    targetdir = sys.argv[1]

    test_main(targetdir)

