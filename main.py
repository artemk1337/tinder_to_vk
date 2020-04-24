"""
private - login, password and other
"""

import torch

from facenet_pytorch import MTCNN, InceptionResnetV1
from utils._bd import DataBase
from utils.CNN_parse import FinderVK, ResetDB, ParsePageVK
from telegram_bot.bot import TelegramBot
from utils.auth import Auth
from private import (LOGIN_VK, PASSWORD_VK,
    TOKEN_TG, REQUEST_KWARGS, ADMINS_TG, PASSWORD_TG)


# Try to use GPU. Else cpu.
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
# Import MTCNN
mtcnn = MTCNN(image_size=160, keep_all=True)
resnet = InceptionResnetV1(pretrained='vggface2').eval()
DB_type = "Postegre"


# init classes
class_data_base = DataBase("Postegre", device, resnet)
class_finder_vk = FinderVK("Postegre", mtcnn, resnet, class_data_base)
class_reset_db = ResetDB(class_data_base)
class_auth_vk = Auth(login=LOGIN_VK,
                     password=PASSWORD_VK,
                     auth_handler=True)
class_parse_vk = ParsePageVK(class_auth_vk.ImplicitFlow(),
                             class_auth_vk.vk_session,
                             class_data_base, mtcnn, max_last_photos=30,
                             max_faces=10, min_faces_before_save=15)
class_tg_bot = TelegramBot(class_finder_vk,
                           class_reset_db,
                           class_parse_vk,
                           TOKEN=TOKEN_TG, REQUEST_KWARGS=REQUEST_KWARGS,
                           admins_id=ADMINS_TG, password_admin=PASSWORD_TG)


if __name__ == "__main__":
    print("Trying to start bot")
    class_tg_bot.start_bot()
    # class_parse_vk.start_parsing(123)


"""
def get_members(groupid, VKapi):
    first = VKapi.groups.getMembers(group_id=groupid, v=5.92) # Первое выполнение метода
    data = first["items"]  # Присваиваем переменной первую тысячу id
    count = first["count"] // 1000  # Присваиваем переменной количество тысяч участников
    # С каждым проходом цикла смещение offset увеличивается на тысячу
    # и еще тысяча id добавляется к нашему списку.
    for i in range(1, count + 1):
        data = data + VKapi.groups.getMembers(group_id=groupid,
                                              v=5.92,
                                              offset=i*1000)["items"]
    return data


VKapi = class_auth_vk.ImplicitFlow()
res = get_members('over_hear_fu', VKapi)
print(res)
import pickle

with open("ids.txt", 'wb') as f:
    pickle.dump(res, f)

with open("ids.txt", 'rb') as f:
    l = pickle.load(f)
"""


