#!/usr/bin/env python

import os, boto3, botocore, jmespath, copy
from sqlalchemy import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

# describes how to connect to a DB
# used for inputs to most functions below
class DB():

    def __init__(self, 
                 db_name,
                 db_user,
                 db_pwd,
                 db_host,
                 db_port,
                 db_engine):

        self.configs = {}

        self.configs['db_name'] = db_name
        self.configs['db_user'] = db_user
        self.configs['db_pwd']  = db_pwd
        self.configs['db_host'] = db_host
        self.configs['db_port'] = db_port        
        self.configs['engine'] = db_engine

# get the driver corresponding to the os we are running on
def get_db_driver(this_os = os.name):

    # drivers that seem to work best include:
    # windows:  pyodbc
    # macos:    pymssql

    if this_os == 'posix':
        # for posix-compliant os like macos
        driver = 'pymssql'
    else:
        # for windows this one seems to work best
        driver = 'pyodbc'

    return driver

# get connection string for connecting to an ms-sql RDBMS 
# db is an instance of the DB class
def get_connection_string(db):
    connection = ""

    if db.configs['engine']=='mssql':
        driver = get_db_driver()
        connection = "mssql+%s"%driver
    elif db.configs['engine']=='postgres':
        # pg8000 is the only "pure-python" driver available for python 2.7
        connection = 'postgresql+pg8000'
        #connection = 'postgresql'

    connection_string = "%s://%s:%s@%s/%s" % (connection, 
                                        db.configs['db_user'], 
                                        db.configs['db_pwd'], 
                                        db.configs['db_host'], 
                                        db.configs['db_name'])

    return connection_string

# connect to database
# db is an instance of the DB class
def connect_to_db(db):
    return create_engine(get_connection_string(db))
    
# get an executable table (a table that alchemy commands can be run against)
# db is an instance of the DB class
def get_table(table_name, db):

    engine = connect_to_db(db)
    connection = engine.connect()
    metadata = MetaData(engine)

    # build table
    return Table(table_name, metadata, autoload=True)

def get_session(db):

    engine = connect_to_db(db)

    # create a configured "Session" class
    Session = sessionmaker(bind=engine)

    # create a Session
    session = Session()

def rename_rds_instance(old_name, new_name):

    # rename
    print('renaming %s to %s'%(old_name, new_name))

    client = boto3.client('rds')
    response = client.modify_db_instance(
        DBInstanceIdentifier=old_name,
        ApplyImmediately=True,
        NewDBInstanceIdentifier=new_name)

# take all of the security groups assigned to instance_to_mimic_id and assign them to
# instance_id
def restore_security_group(instance_id, instance_to_mimic_id):
            
    try:
        client = boto3.client('rds')

        response = client.describe_db_instances(DBInstanceIdentifier=instance_to_mimic_id)

        security_group_groups = jmespath.search("DBInstances[*].VpcSecurityGroups[*].VpcSecurityGroupId", response)

        # the outer group should correspond to the unique instance specified, so should have 
        # length==1
        if len(security_group_groups)==1:

            security_group_ids = security_group_groups[0]
            client.modify_db_instance(DBInstanceIdentifier=instance_id,
                                      VpcSecurityGroupIds=security_group_ids)

    except botocore.exceptions.ClientError as e:

        print("Could not add security group(s) to %s. Error %s"%(instance_id,str(e)))  

def delete_instance(instance_id):

    client = boto3.client('rds')

    response = client.delete_db_instance(
        DBInstanceIdentifier=instance_id,
        SkipFinalSnapshot=True)

def snapshot_exists(snapshot_name):

    client = boto3.client('rds')

    try:
        response = client.describe_db_snapshots(
            DBSnapshotIdentifier=snapshot_name)

        # should return exactly one snapshot
        return (len(response['DBSnapshots'])==1)

    except botocore.exceptions.ClientError as e:
        # print "Could not find rds snapshot. Error %s"%str(e)
        return False  

def instance_exists(instance_id):

    client = boto3.client('rds')

    try:
        response = client.describe_db_instances(
            DBInstanceIdentifier=instance_id)

        # should return exactly one instance
        return (len(response['DBInstances'])==1)

    except botocore.exceptions.ClientError as e:
        # print "Could not find rds instance. Error %s"%str(e)
        return False         

# instance_id: id of instance to create from snapshot
# instance_to_mimic_id: id of instance with parameters to mimic (usually the original instance)
# snapshot_name: name of the snapshot to restore into instance_id
def restore_intance_from_snapshot(instance_id, instance_to_mimic_id, snapshot_name):

    try:

        # start a new client session
        client = boto3.client('rds')

        response = client.describe_db_instances(DBInstanceIdentifier=instance_to_mimic_id)

        if len(response['DBInstances'])==1:

            instance_params = response['DBInstances'][0]

            # restore the snapshot into a new instance
            client.restore_db_instance_from_db_snapshot(DBInstanceIdentifier=instance_id,
                DBSnapshotIdentifier=snapshot_name,
                DBInstanceClass=instance_params['DBInstanceClass'],
                DBSubnetGroupName=instance_params['DBSubnetGroup']['DBSubnetGroupName'],
                PubliclyAccessible=instance_params['PubliclyAccessible'],
                MultiAZ=instance_params['MultiAZ']) 

    except botocore.exceptions.ClientError as e:

        print("Could not find instance to mimic. Error %s"%str(e))

# db exists
def db_exists(db, db_name):

    db2 = copy.deepcopy(db)
    db2.configs['db_name'] = db_name
    connection_str = get_connection_string(db2)

    return database_exists(connection_str)

# create a DB
def create_db(db, create_db_sql):

    err = None

    try:

        connection_str = get_connection_string(db)

        engine = create_engine(connection_str,
                               isolation_level='AUTOCOMMIT')
        
        conn = engine.connect()
        
        conn.execute(create_db_sql)
        conn.close()  
    
    except SQLAlchemyError as e:

        err = e

    return err

# drop a DB
def drop_db(db, drop_db_sql):

    connection_str = get_connection_string(db)

    engine = create_engine(connection_str,
                           isolation_level='AUTOCOMMIT')
    
    conn = engine.connect()
    
    conn.execute(drop_db_sql)
    conn.close()
