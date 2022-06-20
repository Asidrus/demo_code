import json
from json import JSONDecodeError
""" ... """


class BaseModel:
    def __eq__(self, other) -> list:
        errors = []
        for key in other.__dict__.keys():
            if type(self.__dict__[key]) is list:
                res = []
                if type(other.__dict__[key]) is list:
                    ac = sorted(self.__dict__[key].copy())
                    ex = sorted(other.__dict__[key].copy())
                    for i in range(len(ex)):
                        try:
                            _res = ac[0] == ex[0]
                            if (type(_res) is bool) and not _res:
                                res.append({"expected": ex[0], "actual": ac[0]})
                            elif (type(_res) is list) and _res:
                                res.append({str(ex[0]).replace('"', "'"): _res})
                            ex.remove(ex[0])
                            ac.remove(ac[0])
                        except IndexError:
                            res.append({"expected": ex[0], "actual": "None (В actual списке нет этого элемента, или он лишний в expected"})
                            ex.remove(ex[0])
                    res.extend({"expected": item.__dict__, "actual": "None (В actual списке нет этого элемента, или он лишний в expected"} for item in ex)
                    res.extend({"expected": "None (В expected списке нет этого элемента, или он лишний в actual", "actual": item.__dict__} for item in ac)
                else:
                    errors.append({key: {"expected": other.__dict__[key], "actual": self.__dict__[key]}})
            else:
                res = self.__dict__[key] == other.__dict__[key]
            if type(res) is list:
                if res:
                    errors.append({key: res})
            elif type(res) is bool:
                if not res:
                    errors.append({key: {"expected": other.__dict__[key], "actual": self.__dict__[key]}})
        return errors

    def __repr__(self) -> str:
        """
        :param _repr_list_: список выводимых параметров или str("all") выводить все
        :param _encapsulation_: "public" | "protected". Default is "protected"

        :return: str
        """
        keys = self.__dict__.keys()
        values = self.__dict__
        keys = filter(
            lambda x: not (x.startswith("_") and (values.get("_encapsulation_") in [None, "protected"])), keys)
        keys = filter(
            lambda x: not ((type(values.get("_repr_list_")) is list) and (x not in values["_repr_list_"])), keys)

        res = {}
        for key in keys:
            try:
                res[key] = json.loads(repr(values[key]))
            except JSONDecodeError:
                # res[key] = repr(self.__dict__[key])
                res[key] = str(self.__dict__[key])
        return json.dumps(res, indent=3, ensure_ascii=False)

    def __str__(self):
        """
        :param _str_list_: список выводимых параметров или str("all") выводить все
        :param _encapsulation_: "public" | "protected". Default is "protected"

        :return: str
        """
        keys = self.__dict__.keys()
        values = self.__dict__
        keys = filter(
            lambda x: not (x.startswith("_") and (values.get("_encapsulation_") in [None, "protected"])), keys)
        keys = filter(
            lambda x: not ((type(values.get("_str_list_")) is list) and (x not in values["_str_list_"])), keys)

        res = {}
        for key in keys:
            try:
                res[key] = json.loads(str(values[key]))
            except JSONDecodeError:
                res[key] = str(self.__dict__[key])
        return json.dumps(res, ensure_ascii=False)


class Status:
    _status_list = []
    BEING_APPROVED = EnumItem("BEING_APPROVED", "На согласовании", _status_list)
    COMPLETE = EnumItem("COMPLETE", "Выполнено", _status_list)
    """ ... """


class ItemStatus:
    _status_list = []
    PENDING = EnumItem("PENDING", "В ожидании", _status_list)
    FOR_APPROVING = EnumItem("FOR_APPROVING", "На согласовании", _status_list)
    """ ... """


class ActionOnRequestItems:
    _list = []
    APPROVE = EnumItem("approved", "Согласовать", _list)
    REJECT = EnumItem("rejected", "Отклонить", _list)
    DELEGATE = EnumItem("delegated", "Делегировать", _list)
    CLARIFIED = EnumItem("clarified", "Уточнить", _list)
    REPLIED = EnumItem("replied", "Вернуть", _list)
    """ ... """


class RequestType:
    _type_list = []
    revokeAssignments = EnumItem("REVOKE_ASSIGNMENTS", "Отзыв ролей", _type_list)
    createRoleAssignments = EnumItem("CREATE_ROLE_ASSIGNMENTS", "Назначение ролей", _type_list)
    """ ... """


class Request(BaseModel):

    def __init__(self, number: int = None, created_date=None, request_type=RequestType.UNDEFINED,
                 status=Status.UNDEFINED, initiator=None, oid=None, card=None):
        self.number = number
    """ ... """


class RequestItem(BaseModel):
    def __init__(self, role=None, system=None, account_name=None, approver: str = None, step_name=None,
                 approval_date=None, activation_date=None, status=Status.UNDEFINED, password=None):
        self.role = role
        self.system = system
        """ ... """


class HistoryRecordDecision:
    _decision_list = []
    request_assigned_on = EnumItem("request.assignedOn", "Назначен согласующим", _decision_list)
    request_delegated_to = EnumItem("request.delegatedTo", "Делегировано на", _decision_list)
    """ ... """


class HistoryRecord(BaseModel):
    def __init__(self, initiator=None, step_name=None, decision=HistoryRecordDecision.UNDEFINED,
                 comment=None, next_approver=None, date=None):
        if initiator is None:
            self.initiator = 'inRights'
        else:
            self.initiator = initiator
    """ ... """


class UserInfo(BaseModel):
    def __init__(self, last_name=None, first_name=None, additional_name=None, birth_date=None, date_from=None,
                 hr_status=None, user_type=None, contract_number=None, manager=None, region=None, city=None,
                 office=None, last_name_eng=None, first_name_eng=None, additional_name_eng=None,
                 employment_full_name=None):
        self.last_name = last_name
        self.first_name = first_name
        """ ... """

