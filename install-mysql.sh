# please use password 8888

sudo apt-get update
sudo apt-get install mysql-server
sudo netstat -tap | grep mysql
mysqladmin --version
sudo apt-get install python-mysqldb

# prepaare for my tiny benchmarks
mysql -u root -p8888 -Bse "SHOW DATABASES;CREATE DATABASE testdb;"
mysql -u root -p8888 -Bse "CREATE USER 'testuser'@'localhost' IDENTIFIED BY 'test623';USE testdb;"
mysql -u root -p8888 -Bse "GRANT ALL ON testdb.* TO 'testuser'@'localhost';"

# for sqlbench
RPW=8888 #enter the root sql password at the prompt
mysqladmin -u root -p$RPW create test



