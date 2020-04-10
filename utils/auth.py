import vk as vk1
import vk_api


class Auth(object):
    def __init__(self, login=None, password=None, auth_handler=False, token=None):
        self.login = login
        self.password = password
        self.auth_handler = auth_handler
        self.token = token

    def ImplicitFlow(self):
        def auth_handler():
            """ При двухфакторной аутентификации вызывается эта функция.
            """
            # Код двухфакторной аутентификации
            key = input("Enter authentication code: ")
            # Если: True - сохранить, False - не сохранять.
            remember_device = True
            return key, remember_device

        if self.auth_handler is True:
            self.auth_handler = auth_handler
        vk_session = vk_api.VkApi(
            self.login, self.password,
            # функция для обработки двухфакторной аутентификации
            auth_handler=self.auth_handler)
        try:
            vk_session.auth()
            return vk_session.get_api()
        except vk_api.AuthError as error_msg:
            print(error_msg)
            quit()

    def Client_credentials_flow(self):
        try:
            session = vk1.Session(access_token=self.token)  # Авторизация
            return vk1.API(session)
        except Exception as e:
            print(e)
            quit()

