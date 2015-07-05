# PiSensorNetwork

---

PiSensorNetwork uses Raspberry Pi as weather station that collects environment data and uploads the data to a central server. Codes are written in Python.

# Installation

---

## Server

Our PiSensorNetwork server is based on Twisted, an event-driven network engine that we use to deal with concurrency, deamonization, etc. Therefore, the first thing to install on a PiSensorNetwork server is Twisted. We recommend doing this with pip:
```
pip install twisted
```
And of course, virtualenv is recommended here which allows you to create an isolated Python environment when installing Twisted or any other Python packages. Our server side implementation also makes use of Twistar, an ORM for Twisted framework's database interface, so Twistar needs to be installed as well:
```
pip install twistar
```
The last Python package we need is MySQL-python, the MySQL interface for Python:
```
pip install MySQL-python
```
Next step is to initialize the database we used for data server. Head PiSensorNetwork/server folder and create a MySQL database named 'mapdb' with following command which imports configurations stored in mapdb.sql: 
```
mysql -u username -p -h localhost mapdb < mapdb.sql
```
Remember the username and password typed above, as we need them to edit server's config file: PiSensorNetwork/server/server.json. Open this file and then substitute values for 'user' and 'passwd' with your database's username and password respectively.

Yeah! We can finally start running our server now! Use 
```
python dataServer.py
```
to start the dataServer. If everything goes well, you will see loggings shown on your screen.

## Node

The only two things we need on our raspberry Pi related to database are MySQL and Python's MySQL interface, MySQLdb.
```
sudo apt-get install mysql-server python-mysqldb
```

