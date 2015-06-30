mysql-io-pattern
================

In this project we study the I/O pattern (system call level) of MySql. 

Source code tree
================


- ./README.md           This file.
- ./bench               SqlBench source code
- ./script/             R analysis code
- ./install-mysql.sh    shell code to prepare environment
- ./tpcc-mysql          TPC-C for MySql source code
- ./src                 TutorialBench, trace collector, trace parser



The following instructions are for Ubuntu only. It is similar for other
Linux distribution though. 

To prepare the environment
=================
`./install-mysql.sh`

This will install mysql and python-mysqldb. It also sets up the database
for testing. 
You will be asked to create MySql Root password, please use '8888'.
Because I used that throughout the whole source code.
If you use another password and  you don't want to modify it, you can 
just replace all 8888 in the source coode. with your password.

To run tpcc
=================
The script above does not prepare the environment for TPC-C. 
To prepare TPCC, please follow in structions here:
```
sudo apt-get install libmysqlclient-dev

sudo apt-get install bzr
bzr branch lp:~percona-dev/perconatools/tpcc-mysql
make all

mysqld &
cd ~/tpcc-mysql
mysql -u root -p -e "CREATE DATABASE tpcc1000;"
mysql -u root -p tpcc1000 < create_table.sql
mysql -u root -p tpcc1000 < add_fkey_idx.sql

./tpcc_load 127.0.0.1 tpcc1000 root "8888" 20
```
http://www.mysqlperformanceblog.com/2013/07/01/tpcc-mysql-simple-usage-steps-and-how-to-build-graphs-with-gnuplot/

To change mysql data directory
=================
1. Stop MySQL using the following command:
  ```
  sudo /etc/init.d/mysql stop
  ```

2. Copy the existing data directory (default located in /var/lib/mysql) using the following command:
  ```
  sudo cp -R -p /var/lib/mysql /newpath
  ```

3. edit the MySQL configuration file with the following command:
  ```
  sudo gedit /etc/mysql/my.cnf
  ```
  Look for the entry for datadir, and change the path (which should be /var/lib/mysql) to the new data directory.

4. found out that one needs to edit the file `/etc/apparmor.d/tunables/alias` to include a line "alias /var/lib/mysql/ -> /newpath/," With this in place, I did not need any changes in any of the other AppArmor files. It worked immediately after restarting AppArmor with "/etc/init.d/apparmor restart" and MySQL with "restart mysql"

5. Restart the AppArmor profiles with the command:
  ```
  sudo /etc/init.d/apparmor reload
  ```
6. Restart MySQL with the command:
  ```
  sudo /etc/init.d/mysql restart
  ```
  Now login to MySQL and you can access the same databases you had before.

To remove mysqld
==============================
```
sudo service mysql stop  #or mysqld
sudo killall -9 mysql
sudo killall -9 mysqld
sudo apt-get remove --purge mysql-server mysql-client mysql-common
sudo apt-get autoremove
sudo apt-get autoclean
sudo deluser mysql
sudo rm -rf /var/lib/mysql
sudo apt-get purge mysql-server-core-5.5
sudo apt-get purge mysql-client-core-5.5
```


To collect traces
=================
```
cd ./src
python test_framework.py target-trace-dir
```
After running, the traces will be in target-trace-dir.

You can choose which benchmark to run in test_framework.py.
Please search 'scriptlist'.

To run a little demo, you can do
```
cd ./src
python test_framework.py /tmp
```

The default will run TutorialBench. 

To parse the trace
=================
```
cd ./src/
python trace_scanner.py path-to-your-trace
```

The parsed result will be in the same directory of the trace.
It is named as $tracename.table

You can do a little demo with
```
cd ./src
python trace_scanner test.trace
```
