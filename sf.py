# from pyfactorybridge import API
from satisfactory_api_client import SatisfactoryAPI
from satisfactory_api_client.data import MinimumPrivilegeLevel


# Connect to the Satisfactory server
def connect(ip, port):
    return SatisfactoryAPI(host=ip, port=port)


# Login into the Satisfactory server an check for Admin access rights
def login(api, pwd):
    api.password_login(MinimumPrivilegeLevel.ADMINISTRATOR, password=pwd)
    return api.verify_authentication_token()


# def test(ip, port, passwd):
# sf = API(address=f"{ip}:{port}", password=passwd)
# try:
# print(sf.get_server_health())
# print(sf.get_server_options())
# print(sf.save_game("Test"))
# except:
# print("error")
