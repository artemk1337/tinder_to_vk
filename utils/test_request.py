import requests
import vk_api
from bs4 import BeautifulSoup
import pprint as pp



def auth_handler():
    """ При двухфакторной аутентификации вызывается эта функция.
    """
    # Код двухфакторной аутентификации
    key = input("Enter authentication code: ")
    # Если: True - сохранить, False - не сохранять.
    remember_device = True
    return key, remember_device


with requests.Session() as session:
    vk_session = vk_api.VkApi(
        Login, Password,
        # функция для обработки двухфакторной аутентификации
        auth_handler=auth_handler,
        session=session)

    try:
        vk_session.auth()
        api = vk_session.get_api()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        quit()

    page = session.get('https://vk.com/id2')
    if page.status_code != 200:
        quit()
    soup = BeautifulSoup(page.text, "html.parser")
    pp.pprint(soup)
    # print(soup)
    print(soup.findAll('div', class_='page_avatar_wrap'))

