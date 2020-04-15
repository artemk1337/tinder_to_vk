"""
private - login, password and other
"""
import vk_api
import re
import io
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from PIL import Image, ImageDraw
import requests
from tqdm import tqdm
import psycopg2
import sqlite3


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


data_base.reset_db()
data_base.create_db()


if __name__ == '__main__':
    vk = Auth(login=Login, password=Password, auth_handler=True).ImplicitFlow()
    counter = 0
    aligned, ids, link, sex = [], [], [], []

    parser = ParsePageVK(5, 4, 50, mtcnn)
    for i in (range(1, 10000)):
        counter += parser.get_albums(vk, i, 1000, aligned, ids, link, sex)
        print("id -", i, "persons -", counter)
        if counter >= parser.max_faces_before_save:
            data_base.save_db(aligned, ids, link, sex)
            counter = 0
            aligned, ids, link, sex = [], [], [], []

    data_base.save_db(aligned, ids, link, sex)





