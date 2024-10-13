# from pyfactorybridge import API
from satisfactory_api_client import SatisfactoryAPI
from satisfactory_api_client.data import MinimumPrivilegeLevel


def connect(ip, port):
    return SatisfactoryAPI(host=ip, port=port)


def login(api, pwd):
    api.password_login(MinimumPrivilegeLevel.ADMINISTRATOR, password=pwd)
    api.verify_authentication_token()


def options(api, ctx):
    return api.get_server_options()


# def test(ip, port, passwd):
# sf = API(address=f"{ip}:{port}", password=passwd)
# try:
# print(sf.get_server_health())
# print(sf.get_server_options())
# print(sf.save_game("Test"))
# except:
# print("error")
