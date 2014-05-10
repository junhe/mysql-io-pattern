import subprocess
import os
import sys
import time

strlist = "test-ATIS test-big-tables test-create test-select test-wisconsin "\
          "test-alter-table test-connect test-insert test-transactions"
sqlbenchlist = strlist.split()
tinyscriptlist = [
        'cleanup.py',
        'create_table.py',
        'get_version.py',
        'retrieving_data.py',
        #dictionary_cursor.py  
        'insert_image.py',
        'read_image.py',
        'prepared_statement.py']

class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = newPath

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

def start_mysqld(tracepath):
    cmd = ['strace',
           '-o', tracepath,
           '-f', '-ttt',
           #'-ff',
           '-e', 'trace=open,openat,accept,close,fsync,sync,read,'\
                 'write,pread,pwrite,lseek,'\
                 'dup,dup2,dup3,clone,unlink',
           '-s', '8',
           'mysqld',
           '--innodb-thread-concurrency=1',
           '--innodb-write-io-threads=1',
           '--max-delayed-threads=1',
           '--performance-schema-max-thread-instances=1',
           '--thread-cache-size=1']
    proc = subprocess.Popen(cmd)
    #proc.wait()

def get_pid_by_name(procname):
    cmd = ['pgrep', procname]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    pid = p.communicate()[0]
    pid = pid.strip()

    return pid


def stop_mysqld():
    # get pid of strace
    stracepid = get_pid_by_name('strace')

    while len(stracepid) != 0:
        cmd = ['stop', 'mysql']
        subprocess.call(cmd)
        time.sleep(1)

        cmd = ['pkill', '-TERM', '-P', stracepid]
        subprocess.call(cmd)
        print 'We tried to kill strace', stracepid
        print 'wait for a while...'
        time.sleep(6)

        stracepid = get_pid_by_name('strace')

        print 'Can we find strace anymore?', stracepid
        time.sleep(1)

    #cmd = "mysqladmin -u root -p8888 shutdown"
    #cmd = cmd.split()
    #subprocess.call(cmd)
    
    #print 'tried to stop mysqld'
    #subprocess.call("sudo netstat -tap | grep mysql", shell=True)
    #time.sleep(2)

def run_sqlbench(testname):
    print 'in run_sqlbench***********'
    with cd('../bench/sql-bench/'):
        cmd = ['perl',
                testname,
                '--user', 'root',
                '--password', '8888'
                ]
        subprocess.call(cmd)

def run_tpcc():
    print 'in tpcc'
    with cd('../tpcc-mysql/tpcc-mysql/'):
        cmd = [
                './tpcc_start',
                '-h127.0.0.1',
                '-dtpcc1000',
                '-uroot',
                '-p8888',
                '-w20',
                '-c16',
                '-r10',
                '-l1200'
              ]
        subprocess.call(cmd)


def run_script(scriptname):
    print sqlbenchlist
    if scriptname in tinyscriptlist:
        print 'wrong place!'
        subprocess.call(['python', scriptname])
    elif scriptname in sqlbenchlist:
        run_sqlbench(scriptname)  
    elif scriptname == 'tpcc':
        run_tpcc()

def run_one_bench(targetdir, scriptname):
    stop_mysqld()
    time.sleep(2)

    start_mysqld( os.path.join(targetdir, scriptname+'.trace') )
    #print 'skipped starting mysqld'
    time.sleep(2)

    run_script(scriptname)
    time.sleep(2)
    subprocess.call(['sync'])

def test_main(targetdir):
    if not os.path.exists(targetdir):
        os.makedirs(targetdir)

    #scriptlist = tinyscriptlist+sqlbenchlist
    scriptlist = tinyscriptlist
    #scriptlist = ['tpcc']
    for scriptname in scriptlist:
        run_one_bench(targetdir, scriptname)
    #run_one_bench(targetdir, 'test-wisconsin')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'usage:', sys.argv[0], 'targetdir'
        exit(1)
    targetdir = sys.argv[1]

    test_main(targetdir)

