mysql-io-pattern
================

In this project we study the I/O pattern (system call level) of MySql. 

Source code tree
================
./README.md           This file.
./bench               SqlBench source code
./script/             R analysis code
./install-mysql.sh    shell code to prepare environment
./tpcc-mysql          TPC-C for MySql source code
./src                 TutorialBench, trace collector, trace parser



The following instructions are for Ubuntu only. It is similar for other
Linux distribution though. 

To prepare the environment
=================
./install-mysql.sh

This will install mysql and python-mysqldb. It also sets up the database
for testing. 

To collect traces
=================
cd ./src
python test_framework.py target-trace-dir

After running, the traces will be in target-trace-dir.

You can choose which benchmark to run in test_framework.py.
Please search 'scriptlist'.

To parse the trace
=================
cd ./src/
python trace_scanner.py path-to-your-trace

The parsed result will be in the same directory of the trace.
It is named as $tracename.table



