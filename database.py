import psycopg2 # make sure to pip install psycopg2 for postgreSQL
import pickle   # install pickle --> to be deleted when vectordb is done



conn = psycopg2.connect(user="postgres", password='2518',
                        host='localhost', database='FaceDetect')
print("Connection established")

conn.set_session(autocommit=True)

cursor = conn.cursor()

cursor.execute(
    """
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


    DROP TABLE IF EXISTS faces;

    CREATE TABLE IF NOT EXISTS faces (
        id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        name VARCHAR(255) NOT NULL,
        encoding BYTEA NOT NULL
    )
    """
)
print("'faces' table created")


def add_faces_to_db(name, encoding):
    add_faces = ("INSERT INTO FACES "
                "(name, encoding) "
                "VALUES (%s, %s)")
    
    pickled_encoding = pickle.dumps(encoding) # dumps() serialises an object
    
    data_faces = (name, pickled_encoding)

    cursor.execute(add_faces, data_faces)

'''
# how to add to face table
add_faces_to_db('andrew', img_to_encoding("images/andrew.jpg", FRmodel))
add_faces_to_db('kian', img_to_encoding("images/kian.jpg", FRmodel))
add_faces_to_db('danielle', img_to_encoding("images/danielle.png", FRmodel))
add_faces_to_db('younes', img_to_encoding("images/younes.jpg", FRmodel))

print("Added faces to db")

'''

def verify(image_path, identity, model): # erased 'database' from prev version

    conn = psycopg2.connect(user="postgres", password='2518',
                        host='localhost', database='FaceDetect')
    
    conn.set_session(autocommit=True)
    cursor = conn.cursor()

    
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
    return dist, door_open



cursor.close()
conn.close()
