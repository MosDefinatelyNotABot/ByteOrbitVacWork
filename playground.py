from src import facenet

MODEL_PATH = "facenet_model/model/"

def main():

    Database = {}

    FRmodel = facenet.load_model(MODEL_PATH)

    facenet.save_face("photo0.jpg", "Josh", Database, FRmodel)

    dist, doorOpen = facenet.verify("photo0.jpg", "Josh", Database, FRmodel)
    print(dist, doorOpen)
    dist, doorOpen = facenet.verify("photo1.jpg", "Josh", Database, FRmodel)
    print(dist, doorOpen)
    dist, doorOpen = facenet.verify("photo2.jpg", "Josh", Database, FRmodel)
    print(dist, doorOpen)
    dist, doorOpen = facenet.verify("photo3.jpg", "Josh", Database, FRmodel)
    print(dist, doorOpen)
    dist, doorOpen = facenet.verify("photo4.jpg", "Josh", Database, FRmodel)
    print(dist, doorOpen)
    dist, doorOpen = facenet.verify("photo5.jpg", "Josh", Database, FRmodel)
    print(dist, doorOpen)
    dist, doorOpen = facenet.verify("photo6.jpg", "Josh", Database, FRmodel)
    print(dist, doorOpen)
    
    
if __name__ == "__main__":
    main()