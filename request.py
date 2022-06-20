from contextlib import contextmanager
from time import sleep
from typing import Union

from selenium.webdriver.remote.webelement import WebElement

from model.request import Request, RequestType, Status
from useful_methods.data_conversion import full_date_to_short

from .items import *
from .items import ItemUI
from .users import UsersUI
import re
from .modal import modal_accept_with_comment


class RequestUI(Request):

    def __init__(self, app):
        self._app = app
        self._elements = self.Elements(app)

        self.info = self._elements.info.split(",")[0]
        self.items = []

        super().__init__(number=int(re.findall(r"[0-9]+", self._elements.info)[0]),
                         created_date=full_date_to_short(" ".join(self._elements.info.split(",")[0].split(" ")[-3:])),
                         request_type=RequestType.get_type_by_value(self._elements.request_type),
                         initiator=self._elements.initiator,
                         status=Status.get_status_by_value(self._elements.request_status),
                         oid=None)
        self.comment = self._elements.comment

        """
        Основная логика тут
        Считываем заголовок заявки
        Определяем тип заявки
        От типа заявки инициализируем self.item
        """

        if self.type in [RequestType.revokeAssignments, RequestType.createRoleAssignments,
                         RequestType.recertifyAssignments, RequestType.changeAssignmentsValidityPeriods,
                         RequestType.legalizeViolationAssociationsExtra, RequestType.legalizeViolationAssociationsMissing]:
            self.cards = []
            self._card = None
            for element in self._elements.get_users:
                user = UsersUI(app, element)
                if user._multiple_users_:
                    self._card = user
                    self._card.read_items()
                    self.items = self._card.roles
                else:
                    self.cards.append(user)
            if self._card is None:
                self.cards[0].read_items()
                self.items = self.cards[0].roles

        elif self.type == RequestType.createUser:
            self.card = UserItem(app, self._elements.get_items[0])
            rows = self._elements.get_items
            for i in range(len(rows)):
                self.items.append(UserCardItem(self._app, rows[i], i))

        elif self.type == RequestType.createOrgunit:
            self.item = OrgUnitItem(app, self._elements.get_items[0])

        # elif self.type in [RequestType.createEmployment, RequestType.editEmployment]:
        #     self.item = EmploymentItem(app, self._elements.get_items[0])

        elif self.type == RequestType.transferPassword:
            self.card = UsersUI(app, self._elements.get_users[0])
            self.card.read_items()
            self.items = [TransferPasswordItem(app, self._elements.get_items[0])]

        elif self.type in [RequestType.enableAccount, RequestType.disableAccount]:
            rows = self._elements.get_items
            for i in range(len(rows)):
                self.items.append(AccountItem(self._app, rows[i], i))

        elif True:
            """item для других типов заявок"""
            pass

    def __getitem__(self, item) -> Union[UsersUI, ItemUI]:
        """Если есть несколько пользователей (для ролей)"""
        if (type(self.cards) is list) and (len(self.cards) > 0):
            if item == "all":
                """Вернем либо карточку "Все пользователи" или единственного пользователя"""
                card = self.cards[0] if self._card is None else self._card
                card.open()
                return card
            for user in self.cards:
                """Вернем пользователя по имени"""
                if item in user.name:
                    user.open()
                    """В items прокидываем роли ТЕКУЩЕГО открытого пользователя"""
                    self.items = user.roles
                    return user
            raise Exception(f'Пользователь с именем {item} в "{self.info}" не найден')
        elif self.items:
            """Если пользователей нет (например для аккаунтов)"""
            if item == "all":
                return self
            for _item in self.items:
                """Вернем item по его аккаунт нейму"""
                if item.lower() in _item.account_name:
                    return _item
            raise Exception(f'Аккаунт с именем {item} в "{self.info}" не найден')
        raise Exception(f"Item '{item}' не существует в карточках")

    def approve_all(self, comment="Тестовый комментарий"):
        if self.cards:
            self.__getitem__("all").approve_all()
        else:
            self._elements.btn_do_all_by_name("Согласовать все").click()
        self.send(comment)

    def confirm_all(self, comment="Тестовый комментарий"):
        if self.cards:
            self.__getitem__("all").confirm_all()
        else:
            self._elements.btn_do_all_by_name("Подтвердить все").click()
        self.send(comment)

    def complete(self):
        "Для передачи пароля"
        self.items[0].complete()
        self._elements.btn_by_name("Готово").click()
        self._app.sleep(.5)

    def revoke_all(self, comment="Тестовый комментарий"):
        if self.cards:
            self.__getitem__("all").revoke_all()
        else:
            self._elements.btn_do_all_by_name("Отозвать все").click()
        self.send(comment)

    def reject_all(self, comment="Тестовый комментарий"):
        if self.cards:
            self.__getitem__("all").reject_all()
        else:
            self._elements.btn_do_all_by_name("Отклонить все").click()
        self.send(comment)

    # Нужно ли разграничение: коммент для уточнения и коммент для финала заявки?
    def specify_all(self, comment="Тестовый комментарий"):
        if self.cards:
            self.__getitem__("all").specify_all(comment)
        else:
            self._elements.btn_do_all_by_name("Уточнить все").click()
            sleep(.05)
            modal_accept_with_comment(self._app, comment)
        self.send(comment)

    # Нужно ли разграничение: коммент для нового делага и коммент для финала заявки?
    def delegate_all(self, new_delegate: str, comment="Тестовый комментарий"):
        if self.cards:
            self.__getitem__("all").delegate_all(new_delegate, comment)
        else:
            self._elements.btn_do_all_by_name("Делегировать все").click()
            modal_accept_with_comment(self._app, comment, new_delegate)
        self.send(comment)

    def restart_all(self, comment="Тестовый комментарий"):
        if self.cards and (self.type in [RequestType.revokeAssignments, RequestType.createRoleAssignments,
                                         RequestType.recertifyAssignments]):
            self.__getitem__("all").restart_all(comment)
        else:
            self._elements.btn_do_all_by_name("Вернуть").click()
            modal_accept_with_comment(self._app, comment)
        self.send(comment)

    def cancel_all(self, comment="Тестовый комментарий"):
        self._elements.btn_do_all_by_name("Отменить заявку").click()
        sleep(.05)
        self._elements.btn_do_all_by_name("Да, продолжить").click()
        modal_accept_with_comment(self._app, comment)

    def send(self, comment="Тестовый комментарий"):
        if self.cards:
            self.__getitem__("all")
        btn_send = self._elements.btn_by_name("Далее")
        if btn_send.get_attribute("aria-disabled") == "true":
            raise Exception("Не все роли обработаны")
        else:
            btn_send.click()
            modal_accept_with_comment(self._app, comment)

    @contextmanager
    def scroll_to_item(self, i: int):
        """контекст менеджер для скора до конкретного item'а"""
        item_width = 123  # высота блока в px item от названия роли до "подробнее"
        width = item_width * i
        self._app.simulate_wheel(self._app.find_element_by_xpath("//body"), width)
        yield
        self._app.simulate_wheel(self._app.find_element_by_xpath("//body"), width)

    def read_all_history(self):
        """Считываем все хистори из item'ов"""
        i = 0
        for item in self.items:
            with self.scroll_to_item(i):
                item.read_history()
            i += 1

    class Elements:

        def __init__(self, app):
            self._app = app

        @property
        def info(self) -> str:
            xpath = '//div[contains(@class,"x-component title x-box-item x-component-default")]'
            return self._app.find_element_by_xpath(xpath).text

        @property
        def request_type(self) -> str:
            xpath = '//div[contains(text(), "Тип заявки:")]'
            return self._app.find_element_by_xpath(xpath).text.split(": ")[-1]

        @property
        def request_status(self) -> str:
            xpath = '//div[contains(text(), "Статус заявки:")]'
            return self._app.find_element_by_xpath(xpath).text.split(": ")[-1]

        @property
        def initiator(self) -> str:
            xpath = '//*[contains(@class, "pruning-line")]'
            return self._app.find_element_by_xpath(xpath).text.split(": ")[-1]

        @property
        def comment(self) -> str:
            xpath = '//*[contains(@class, "initiator-comment")]'
            comment = self._app.find_element_by_xpath(xpath).text
            return None if comment == "" else comment

        @property
        def get_users(self) -> list:
            xpath = '//div[contains(@id,"card_usersgrid")]//table//div[@class="request-user link-text"]'
            return self._app.find_elements_by_xpath(xpath)

        @property
        def get_items(self) -> list:
            xpath = '//table[.//div[contains(@class,"request-role-widget")]]'
            return self._app.find_elements_by_xpath(xpath)

        def btn_by_name(self, name) -> WebElement:
            xpath = f'//span[contains(text(), "{name}")]'
            return self._app.find_element_by_xpath(xpath)

        def btn_do_all_by_name(self, btn_name) -> WebElement:
            xpath = f'//span[contains(text(),"{btn_name}")]'
            return self._app.find_element_by_xpath(xpath)
