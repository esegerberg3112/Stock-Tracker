# module for managing queries/commands and connection PostgreSQL database
import psycopg2
from config import config
import bcrypt

# hash a password for the first time - using bcrypt, the salt is saved into the hash
def hash_password(plain_txt_passw):
    return bcrypt.hashpw(plain_txt_passw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    # decoding the salt because psycopg2 adapts binary values such as bytes
    # by converting them to the Postgresql binary string representation, so want to add the hashed string
    # rather than the bytes to database and then do the bytes conversion upon querying

# check the hashed password to see if it matches plain text password
def check_password(plain_txt_passw, hashed_passw):
    # bytes converts the hashed string to bytes, as that is what bcrypt expects
    return bcrypt.checkpw(plain_txt_passw.encode('utf-8'), bytes(hashed_passw, 'utf-8'))

# class to define connection to PostgreSQL database and manage all the different commands/queries
class MySQLConnect():
    # instantiate class with a connection to the database
    def __init__(self):
        pass

    # use context managers enter/exit to control opening/closing multiple SQL database connections
    # made throughout the lifecycle of the program for querying/commanding database
    def __enter__(self):
        """ Conect to PostgreSQL database server"""
        params = config()
        try:
            self.conn = psycopg2.connect(**params)
            return self.conn
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            pass

    # including the call to commit function since will be making queries/commands in the cursor with block
    # rather than the commit with block
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()

# function to create a new user in the database
def add_user(username, password):
    # create instance of MySQLConnect class that supports context manager protocol
    with MySQLConnect() as db:
        with db.cursor() as cur:
            try:
                sql_query = "INSERT INTO test (username,password) VALUES (%s, %s);"
                data = (username, password, )
                cur.execute(sql_query, data)
            # catch error if username already exists in database
            except psycopg2.errors.DuplicateJsonObjectKeyValue:
                raise psycopg2.errors.UniqueViolation
            except psycopg2.errors.StringDataRightTruncation:
                raise psycopg2.errors.StringDataRightTruncation
    return "Account Created"

# for user login, query database to check if user exists
def check_credentials(username, password):
    auth = False
    # create instance of MySQLConnect class that supports context manager protocol
    with MySQLConnect() as db:
        with db.cursor() as cur:
            try:
                # pull name of data table from db instance
                sql_query = "SELECT password FROM test WHERE username=%s;"
                data = (username,)
                cur.execute(sql_query, data)
                # query should always only return 1 result if the username exists, since
                # that column is a Primary Key so it's unique
                result = cur.fetchall()[0][0]
                auth = check_password(password, result)
            except IndexError:
                auth = False
    return auth

# return favorite string for a given username
def get_favorites(username):
    # create instance of MySQLConnect class that supports context manager protocol
    with MySQLConnect() as db:
        with db.cursor() as cur:
            sql_query = "SELECT favorite FROM test WHERE username=%s;"
            data = (username,)
            cur.execute(sql_query, data)
            result = cur.fetchall()[0][0]
    return result

def add_favorite(username, ticker):
    # create instance of MySQLConnect class that supports context manager protocol
    with MySQLConnect() as db:
        with db.cursor() as cur:
            try:
                sql_query = "UPDATE test SET favorite = %s WHERE username = %s;"
                data = (ticker, username, )
                cur.execute(sql_query, data)
            except psycopg2.errors.StringDataRightTruncation:
                raise psycopg2.errors.StringDataRightTruncation
