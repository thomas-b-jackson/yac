import unittest, os, random
from yac.lib.db import DB, get_connection_string, get_db_driver

#class DB():
#
#    def __init__(self, 
#                 db_name,
#                 db_user,
#                 db_pwd,
#                 db_host,
#                 db_port,
#                 db_engine):

class TestCase(unittest.TestCase):

    def test_db_configs(self): 

        db = DB('this','test','test','test','test','test')

        self.assertTrue(len(list(db.configs.keys()))==6)

    def test_db_connection_postgres(self): 

        db = DB(db_name='this',db_user='test',db_pwd='test',db_host='test',db_port='test', db_engine ='postgres')

        connection_string = get_connection_string(db)

        #print connection_string
        self.assertTrue('postgres' in connection_string)

    def test_db_connection_mssql(self): 

        db = DB(db_name='this',db_user='test',db_pwd='test',db_host='test',db_port='test', db_engine ='mssql')

        connection_string = get_connection_string(db)

        #print connection_string
        self.assertTrue('mssql' in connection_string)

    def test_db_connection(self): 

        db_driver = get_db_driver()

        self.assertTrue('pymssql' in db_driver or 'pyodbc' in db_driver)        