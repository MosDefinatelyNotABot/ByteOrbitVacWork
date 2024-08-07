# postgreSQL database to store faces (name & img_encoding)


import psycopg2 # make sure to pip install psycopg2 for postgreSQL & downloaded postgreSQL on your machine
                # also make sure your postgreSQL is running if running locally
from psycopg2 import sql
from pgvector.psycopg2 import register_vector   # pip install pgvector
import pickle 
import numpy as np  # pip instll numpy



class vectorDB:

    # myDB = vectorDB('postgres', '2518', 'FaceDetect', 'localhost')
    def __init__(self, user : str, password : str, database : str, host = 'localhost'): # if host not given, uses localhost
        self.user = user
        self.password = password    # probably not the safest approach to get pw ??
        self.database = database
        self.host = host

        self.conn = psycopg2.connect(user=self.user, password=self.password, host=self.host)
        
        print("Connection established :)")

        self.conn.set_session(autocommit=True)
    
        cursor = self.conn.cursor()

        cursor.execute(sql.SQL("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s"), [database]) # checks if db with this name exists

        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))  # ensures no duplicate DB is created
            print("Database: {} successfully created!".format(database))
        else:
            print("Successfully connected to database: {}!".format(database))

        # cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        # CREATE EXTENSION IF NOT EXISTS vector ## still need to work on this
        # register_vector(self.conn) 
        
        

    
    # myDB.createFaceTable()
    # tableName is set to 'Faces'
    def createFaceTable(self):

        cursor = self.conn.cursor()

        # might be good idea to make it optional to delete existing Faces table
        cursor.execute("DROP TABLE IF EXISTS Faces CASCADE")    # deletes table if exists
        cursor.execute("DROP TABLE IF EXISTS Encoding")
        

        # id uuid PRIMARY KEY DEFAULT uuid_generate_v4() // if SERIAL PRIMARY KEY not sufficient; CREATE EXTENSION in that case
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Faces(
            id VARCHAR(8) PRIMARY KEY,
            firstName VARCHAR(255) NOT NULL,
            lastName VARCHAR(255) NOT NULL
            )
            """
        )

        cursor.execute( # table to store encoding for each face
            """
            CREATE TABLE Encoding(
            id VARCHAR(8) REFERENCES Faces,
            encoding BYTEA NOT NULL
            )
            """
        )

        # CREATE TABLE Logging  # to store who is in/out
        

        print("Successfully created tables: Faces and Encoding!")

        cursor.close()


    # myDB.addFaces('andrew', 'tate', img_to_encoding('images/andrew.jpg', FRmodel))
    def addFaces(self, firstName : str, lastName : str, encoding : np):  # otherwise take image_path : str rather than encoding
    
        cursor = self.conn.cursor()

        addFace = ("INSERT INTO Faces (id, firstName, lastName) VALUES (%s, %s, %s)")


        # id is created uniquely using 5 letters of full name & 3 digit number (000)
        id = lastName[0] + lastName[-1]
        if len(firstName) < 3:
            id += firstName + 'X'
        else:
            id += firstName[0] + firstName[1] + firstName[2]

        cursor.execute("SELECT COUNT(*) FROM Faces WHERE id LIKE %s", (id + '%',))
        count = cursor.fetchone()[0]
        #print(f"Number of rows where name starts with '{id}': {count}")

        # if there are people with same id, check if it's same person
        # for now, we assume if their full names match, it's the same person. but this needs to be changed
        if count > 0:
            cursor.execute("SELECT id FROM Faces WHERE id LIKE %s AND firstName = %s AND lastName = %s", 
                           (id + '%', firstName, lastName))
            matchingRows = cursor.fetchall()

            if matchingRows:
                print("There is already a person with the same id and full name.")
                # don't add them to Faces table; only add the encoding
                for row in matchingRows:
                    id = row[0]
                    print("{}'s id: {}".format(firstName, id))
                
        else:
            print("ID matches found, but no one with the same full name.")
            # proceed to add their face to Faces table

            count += 1  # 001 is the first person with that id
            if count < 10:      # this block assumes that there won't be more than 999 people with same id
                id += "00" + str(count)
            elif count < 100:
                id += "0" + str(count)
            else:
                id += str(count)
            #print("{}'s id is: ".format(firstName) + id)

            cursor.execute(addFace, (id, firstName, lastName))
            print("Successfully added {} with id: {} to db!".format(firstName, id))


        # now add pickledEncoding
        pickledEncoding = pickle.dumps(encoding) # dumps() serialises an object

        addEncoding = ("INSERT INTO Encoding (id, encoding) VALUES (%s, %s)")
        encodingQuery = (id, pickledEncoding)
        
        cursor.execute(addEncoding, encodingQuery)
        print("Successfully added {}'s encoding to db!".format(firstName))

        cursor.close()


    # myDB.verify('images/andrew.jpg', 'andrew tate', FRmodel)
    def verify(self, image_path : str, identity : str, model):
        identity = identity.split()
        firstName = identity[0]
        lastName = identity[1]

        cursor = self.conn.cursor()
        
        encoding = img_to_encoding(image_path, model)

        # we are still assuming people with same full names are one person
        cursor.execute("SELECT id FROM Faces WHERE firstName=%s AND lastName=%s", (firstName, lastName))
        result = cursor.fetchone()

        try:
            if result:
                # if person exists on db, get their id
                id = result[0]
                print("{} found with id: {}".format(identity, id))

                query = ("SELECT encoding FROM Encoding WHERE id={}".format(id))
                cursor.execute(query)
        
                unpickledEncoding = pickle.loads(cursor.fetchone()[0])     # back to numpy

                dist = np.linalg.norm(tf.subtract(unpickledEncoding, encoding))
                
                if dist < 0.7:
                    print("It's " + str(identity) + ", welcome in!")
                    door_open = True

                    # add (face) to Logging

                else:
                    print("It's not " + str(identity) + ", please go away")
                    door_open = False


                return dist, door_open
            else:
                print("{} not found on db :( Add the face first before verification.".format(identity))
       
        except psycopg2.Error as e:
            print("Error executing query:", e)
            self.conn.rollback()

        cursor.close()


    #def numOfFaces(self):

        
    
        
    # myDB.close_conn()
    def close_conn(self):
        self.conn.close()
        print("Successfully disconnected from db!")


