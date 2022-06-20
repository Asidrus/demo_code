# from model.request import EmploymentInfo, UserInfo, OrgUnitInfo
from model.request import UserInfo
from .request import RequestUI


__all__ = [
    "RequestUI",
    # "EmploymentInfo",
    "UserInfo",
    # "OrgUnitInfo"
]

"""
usage:

from forms.objects.requests import *

request = RequestUI(app)

info = UserInfo(last_name="Новый",
                first_name="Пупс",
                additional_name="Игнатович",
                birth_date="01.02.1980",
                date_from="15.03.2022",
                hr_status="Работает",
                user_type="Тест")


"assert список не пустой, напечатать список расхождений"

assert not info == request.item, info == request.item

"Получить все поля истории"
print(request["A2ghkfhaieiagabh Исмаил Ибрагимович"]["AD Replicator"][0].__dict__)

"или все у пользователя"
print([history.__dict__ for history in request["A2uhkfhaieiagfdc Исмаил Ибрагимович"]["AD Replicator"][:]])

"хистори у всех пользователей роли"
print([history.__dict__ for history in request["all"]["AD Replicator"][:]])

"для всех пользователей"
request["all"].reject_all()

"для каждого отдельно"
request["Маленькая Фея"].delegate_all("Дора")
request["Олененок Бэмби"].reject_all()

"Отклонить конкретную роль для конкретного юзера"
request["Олененок Бэмби"]["Администратор ИТ"].reject()

"Согласовать конкретную роль для всех"
request["all"]["Администратор ИТ"].approve()

"отправляем запрос"
request.send("Комментарий")


"""
