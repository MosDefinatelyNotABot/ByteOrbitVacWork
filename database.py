# postgreSQL database to store faces (name & img_encoding)


import psycopg2 # make sure to pip install psycopg2 for postgreSQL & downloaded postgreSQL on your machine
                # also make sure your postgreSQL is running if running locally
from psycopg2 import sql
from pgvector.psycopg2 import register_vector   # pip install pgvector
import pickle 
import numpy as np  # pip instll numpy



class vectorDB:

    # myDB = vectorDB('user', password, database, host)
    def __init__(self, user : str, password : str, database : 'postgres', host = 'localhost'): # if host not given, uses localhost
        self.user = user
        self.password = password    # probably not the safest approach to get pw ??
        self.database = database
        self.host = host

        '''
        conn = psycopg2.connect(user="postgres", password='2518',
                                host='localhost', database='FaceDetect')
        '''

        self.conn = psycopg2.connect(user=self.user, password=self.password, database = database, host=self.host)
        
        print("Connection established")


        self.conn.set_session(autocommit=True)
    
        cursor = self.conn.cursor()

        cursor.execute(sql.SQL("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s"), [database]) # checks if db with this name exists

        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))  # ensures no duplicate DB is created
            print("Database successfully created!")
        else:
            print("Successfully connected to database!")

        cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        # CREATE EXTENSION IF NOT EXISTS vector ## still need to work on this
        # register_vector(self.conn) 
        
        

    
    # myDB.createTable('Faces')
    def createTable(self, tableName : str):

        cursor = self.conn.cursor()
    
        cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(tableName)))    # deletes table if exists

        cursor.execute(sql.SQL(
            """
            CREATE TABLE {}(
            id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL,
            encoding BYTEA NOT NULL)
            """
        ).format(sql.Identifier(tableName)))


        print("Table successfully created!")

        cursor.close()


    # myDB.addFaces('andrew', img_to_encoding("images/andrew.jpg", FRmodel))
    def addFaces(self, tableName : str, name : str, encoding : np):  # otherwise take image_path : str rather than encoding
    
        cursor = self.conn.cursor()

        addFace = ("INSERT INTO {} "
                    "(name, encoding) "
                    "VALUES (%s, %s)").format(tableName)
        
        pickledEncoding = pickle.dumps(encoding) # dumps() serialises an object
        
        dataFace = (name, pickledEncoding)

        cursor.execute(addFace, dataFace)

        print("Successfully added faces to db!")

        cursor.close()


    # myDB.verify("images/andrew.jpg", "andrew", FRmodel)
    def verify(self, tableName : str, image_path : str, identity : str, model): # erased 'database' from prev version
        
        cursor = self.conn.cursor()
        
        encoding = img_to_encoding(image_path, model)

        query = ("SELECT encoding FROM {} WHERE name='%s'").format(tableName)
        
        cursor.execute(query, identity)
    
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
        print("Successfully disconnected from db!")


myDB = vectorDB('postgres', '2518', 'testDB', 'localhost')

myDB.createFaceTable('faces')

myDB.addFaces('faces', 'andrew', img_to_encoding("images/andrew.jpg", FRmodel))
myDB.addFaces('faces', 'danielle', img_to_encoding("images/danielle.png", FRmodel))
myDB.addFaces('faces', 'kian', img_to_encoding("images/kian.jpg", FRmodel))
myDB.addFaces('faces', 'younes', img_to_encoding("images/andrew.jpg", FRmodel))
myDB.verify('faces', 'images/andrew.jpg', 'danielle', FRmodel)

myDB.close_conn()



