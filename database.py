# postgreSQL database to store faces (name & img_encoding)


import psycopg2 # make sure to pip install psycopg2 for postgreSQL & downloaded postgreSQL on your machine
                # also make sure your postgreSQL is running if running locally
from psycopg2 import sql
from pgvector.psycopg2 import register_vector   # pip install pgvector
import pickle 
import numpy as np  # pip instll numpy



class vectorDB:

    # connects to db
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
        cursor.execute( # table to store ID and name
            """
            CREATE TABLE IF NOT EXISTS Faces(
            id VARCHAR(8) PRIMARY KEY,
            firstName VARCHAR(255) NOT NULL,
            lastName VARCHAR(255) NOT NULL,
            thumbnail BYTEA NOT NULL
            )
            """
        )

        cursor.execute( # table to store encoding for each face; can have multiple encodings per ID (face)
            """
            CREATE TABLE Encoding(
            id VARCHAR(8) REFERENCES Faces,
            encoding BYTEA NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )

        cursor.execute( # table to store events
            """
            CREATE TABLE Events(
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )
        

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


    # if identity exists on db, it verifies. Otherwise says it doesn't exist.
    # myDB.verify('images/andrew.jpg', 'andrew tate', FRmodel)
    def verify(self, image_path : str, identity : str, model):
        fullName = identity.split()
        firstName = fullName[0]
        lastName = fullName[1]

        cursor = self.conn.cursor()
        
        encoding = img_to_encoding(image_path, model)

        # we are still assuming people with same full names are one person
        cursor.execute("SELECT id FROM Faces WHERE firstName=%s AND lastName=%s", (firstName, lastName))
        result = cursor.fetchone()

        try:
            if result:
                # if person exists on db, get their id
                id = result[0]
                print("{} found with id: {}".format(firstName, id))

                query = ("SELECT encoding FROM Encoding WHERE id='{}'".format(id))
                cursor.execute(query)
        
                unpickledEncoding = pickle.loads(cursor.fetchone()[0])     # back to numpy

                dist = np.linalg.norm(tf.subtract(unpickledEncoding, encoding))
                
                if dist < 0.7:
                    print("It's " + str(identity) + ", welcome in!")
                    door_open = True

                    # add (face) to Events

                else:
                    print("It's not " + str(identity) + ", please go away")
                    door_open = False

                    # add (UNKNOWN) to Events


                return dist, door_open
            else:
                print("{} not found on db :( Add the face first before verification.".format(identity))
       
        except psycopg2.Error as e:
            print("Error executing query:", e)
            self.conn.rollback()

        cursor.close()

    

    # prints/returns the number of registered faces
    def numOfFaces(self):
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Faces")
        count = cursor.fetchone()[0]

        print("There are {} faces on Faces table.".format(count))
        #return count   # uncomment depending on how the function gets used

        cursor.close()



    # returns dictionary of encodings for all the registered faces
    # encodings are the most recently added one for each face
    def fetchEncodings(self):
        cursor = self.conn.cursor()

        try:
            # Execute the CTE query to get the most recent encoding for each ID
            cursor.execute(
                """
                WITH RankedEncodings AS (
                    SELECT 
                        id, 
                        encoding, 
                        ROW_NUMBER() OVER (PARTITION BY id ORDER BY timestamp DESC) AS rn
                    FROM Encoding
                )
                SELECT id, encoding
                FROM RankedEncodings
                WHERE rn = 1;
                """
            )
            
            # Fetch all results
            results = cursor.fetchall()
            
            result = {}
            for row in results:
                id, encoding = row
                unpickledEncoding = pickle.loads(encoding)     # back to numpy
                result[id] = unpickledEncoding

            return result

        except psycopg2.Error as e:
            print("Error executing query:", e)
            self.conn.rollback()

        cursor.close()

    
    # returns dictionary of encodings for all the registered faces
    def fetchEncodingOf(self, identity : str):
        cursor = self.conn.cursor()

        fullName = identity.split()
        firstName = fullName[0]
        lastName = fullName[1]

        cursor.execute("SELECT id FROM Faces WHERE firstName=%s AND lastName=%s", (firstName, lastName))
        results = cursor.fetchone()
        try:
            if results:
                # if person exists on db, get their id
                id = results[0]
                print("{} found with id: {}".format(firstName, id))

                query = ("SELECT encoding FROM Encoding WHERE id='{}'".format(id))
                cursor.execute(query)

                encoding = cursor.fetchone()[0]
                unpickledEncoding = pickle.loads(encoding)     # back to numpy

                result = {}
                result[id] = unpickledEncoding

                return result

        except psycopg2.Error as e:
            print("Error executing query:", e)
            self.conn.rollback()

        cursor.close()
        
    
        
    # myDB.close_conn()
    def close_conn(self):
        self.conn.close()
        print("Successfully disconnected from db!")


# using the functions
myDB = vectorDB('postgres', '2518', 'FaceDetect', 'localhost')

myDB.createFaceTable()

myDB.addFaces('min', 'kim', img_to_encoding("images/min.jpg", FRmodel))
myDB.addFaces('min', 'kim', img_to_encoding("images/min2.jpg", FRmodel))
myDB.addFaces('danielle', 'jean', img_to_encoding("images/danielle.png", FRmodel))
#myDB.addFaces('kian', 'vanrensburg', img_to_encoding("images/kian.jpg", FRmodel))
#myDB.addFaces('younes', 'lee', img_to_encoding("images/andrew.jpg", FRmodel))

myDB.numOfFaces()
#myDB.fetchEncodings()   # returns dictionary
#myDB.fetchEncodingOf('min kim') # returns dictionary

myDB.verify('images/min.jpg', 'min kim', FRmodel)
#myDB.verify('faces', 'images/min2.jpg', 'min', FRmodel)

myDB.close_conn()

"""
# output from the above code

Connection established :)
Successfully connected to database: FaceDetect!
Successfully created tables: Faces and Encoding!
ID matches found, but no one with the same full name.
Successfully added min with id: kmmin001 to db!
Successfully added min's encoding to db!
There is already a person with the same id and full name.
min's id: kmmin001
Successfully added min's encoding to db!
ID matches found, but no one with the same full name.
Successfully added danielle with id: jndan001 to db!
Successfully added danielle's encoding to db!
There are 2 faces on Faces table.
min found with id: kmmin001
It's min kim, welcome in!
Successfully disconnected from db!
"""
