import psycopg2 # make sure to pip install psycopg2 for postgreSQL & downloaded postgreSQL on your machine
                    # also make sure your postgreSQL is running if running locally
from psycopg2 import sql
import pickle 
import numpy as np



class vectorDB:

    # myDB = vectorDB()
    def __init__(self, user : str, password : str, host = 'localhost'): # if host not given, uses localhost
        self.user = user
        self.password = password    # probably not the safest approach to get pw ??
        self.dbName = "postgres"
        self.host = host

        '''
        conn = psycopg2.connect(user="postgres", password='2518',
                                host='localhost', database='FaceDetect')
        '''

        self.conn = psycopg2.connect(user=self.user, password=self.password,
                                host=self.host, dbName=self.dbName)
        
        print("Connection established")

        self.conn.set_session(autocommit=True)
    

    # myDB.createDB("faceDetection")
    def createDB(self, dbName : str):
        cursor = self.conn.cursor()

        cursor.execute(sql.SQL("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s"), [dbName]) # checks if db with this name exists

        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE %s"), [dbName])  # ensures no duplicate DB is created
        
        print("Database successfully created!")

    
    # myDB.createTable("Faces")
    def createTable(self, tableName : str):

        cursor = self.conn.cursor()

        cursor.execute(
            """
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

            DROP TABLE IF EXISTS {%s};

            CREATE TABLE IF NOT EXISTS faces (
                id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(255) NOT NULL,
                encoding BYTEA NOT NULL
            )
            """
        )[tableName]

        print("Table successfully created!")

        cursor.close()


    # myDB.addFaces('andrew', img_to_encoding("images/andrew.jpg", FRmodel))
    def addFaces(self, name : str, encoding : np):  # otherwise take image_path : str rather than encoding
    
        cursor = self.conn.cursor()

        add_faces = ("INSERT INTO FACES "
                    "(name, encoding) "
                    "VALUES (%s, %s)")
        
        pickled_encoding = pickle.dumps(encoding) # dumps() serialises an object
        
        data_faces = (name, pickled_encoding)

        cursor.execute(add_faces, data_faces)

        print("Added faces to db")

        cursor.close()


    # myDB.verify("images/andrew.jpg", "andrew", FRmodel)
    def verify(self, image_path, identity, model): # erased 'database' from prev version
        
        cursor = self.conn.cursor()

        
        encoding = img_to_encoding(image_path, model)

        query = ("SELECT encoding FROM faces WHERE name='%s'") % (identity)
        cursor.execute(query)
    

        unpickled_encoding = pickle.loads(cursor.fetchone()[0]) # back to numpy
    

        dist = np.linalg.norm(tf.subtract(unpickled_encoding, encoding))
        
        if dist < 0.7:
            print("It's " + str(identity) + ", welcome in!")
            door_open = True
        else:
            print("It's not " + str(identity) + ", please go away")
            door_open = False

            cursor.close()

        return dist, door_open
    
        
    # myDB.close_conn()
    def close_conn(self):
        self.conn.close()



