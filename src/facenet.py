# facenet encoder and verification module
# from kaggle project https://www.kaggle.com/code/joshuabritz/face-verification-and-recognition/edit

import keras
import numpy as np
from matplotlib import pyplot as plt
from src import cropper
from tensorflow import subtract

def load_model(model_path):
    layer = keras.layers.TFSMLayer(model_path, call_endpoint="serving_default")
    model = keras.Sequential([layer])

    print("model loaded...")

    return model

def img_to_encoding(img: np.ndarray, model):
    # img = keras.preprocessing.image.load_img(img_path, target_size=(160, 160))
    # cropping first face seen

    img = cropper.extract_face(img)
    img = np.around(np.array(img) / 255.0, decimals=12) 
    
    x_train = np.expand_dims(img, axis=0) # add a dimension of 1 as first dimension
    embedding = model.predict_on_batch(x_train)
    mag = np.linalg.norm(embedding["Bottleneck_BatchNorm"][0])
    return embedding["Bottleneck_BatchNorm"] / mag

def save_face(img_path: str, name: str, Database, model: keras.Model):
    # save to vector database...?
    # crop and then encode

    img = plt.imread(img_path)
    img = cropper.extract_face(img)

    encoding = img_to_encoding(img, model)

    Database[name] = encoding

def verify(img_path: str, identity: str, database, model: keras.Model, threshold=0.7):
    # performs facial verification by querying the db.
    
    img = plt.imread(img_path)
    img = cropper.extract_face(img)

    plt.imshow(img)
    plt.show()

    encoding = img_to_encoding(img, model)
    dist = np.linalg.norm(subtract(database[identity], encoding))

    if dist < threshold:
        print("It's " + str(identity) + ", welcome in!")
        door_open = True
    else:
        print("It's not " + str(identity) + ", please go away")
        door_open = False
    return dist, door_open