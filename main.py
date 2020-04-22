"""
private - login, password and other
"""

from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from tqdm import tqdm

# from PIL import Image, ImageDraw
# import requests
# import vk_api
# import re
# import io
# import psycopg2
# import sqlite3
# import time
# from scipy.linalg import norm
# import numpy as np
# from bs4 import BeautifulSoup

from utils.auth import Auth
from utils.parser import ParsePageVK
from utils._bd import DataBase
from private import\
    Login, Password, Token,\
    database, user, password, host, port


# Try to use GPU. Else cpu.
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
# Import MTCNN
mtcnn = MTCNN(image_size=160, keep_all=True)
resnet = InceptionResnetV1(pretrained='vggface2').eval()
DB_type = "Postegre"


data_base = DataBase(DB_type, device, resnet)



def reset_db_():
    data_base.reset_db()
    data_base.create_db()
    print("Success reset DataBase")


if __name__ == '__main__':
    # reset_db_()
    vk = Auth(login=Login, password=Password, auth_handler=False).ImplicitFlow()
    counter = 0
    aligned, ids, link, sex = [], [], [], []

    parser = ParsePageVK(30, 25, 50, mtcnn)
    print("Start parse")
    for i in id_:
        counter += parser.get_albums(vk, i, 1000, aligned, ids, link, sex)
        print("id -", i, "persons -", counter)
        if counter >= parser.max_faces_before_save:
            data_base.save_db(aligned, ids, link, sex)
            counter = 0
            aligned, ids, link, sex = [], [], [], []
    if ids:
        data_base.save_db(aligned, ids, link, sex)
    print("Finish parse")


def start_parse(id_=None):
    vk = Auth(login=Login, password=Password, auth_handler=False).ImplicitFlow()
    counter = 0
    aligned, ids, link, sex = [], [], [], []

    parser = ParsePageVK(30, 25, 50, mtcnn)
    print("Start parse")
    for i in id_:
        counter += parser.get_albums(vk, i, 1000, aligned, ids, link, sex)
        print("id -", i, "persons -", counter)
        if counter >= parser.max_faces_before_save:
            data_base.save_db(aligned, ids, link, sex)
            counter = 0
            aligned, ids, link, sex = [], [], [], []
    if ids:
        data_base.save_db(aligned, ids, link, sex)
    print("Finish parse")


def find_person(path):
    from PIL import Image
    DB_type = "Postegre"
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    mtcnn = MTCNN(image_size=160, keep_all=True)
    resnet = InceptionResnetV1(pretrained='vggface2').eval()
    img = Image.open(path)
    x_aligned, prob = mtcnn(img, save_path=None, return_prob=True)
    embeddings = resnet(x_aligned[:1]).detach().cpu().numpy()
    print(embeddings.shape)
    return data_base.find_person(embeddings[0])
