from contextlib import contextmanager
from time import sleep

from selenium.webdriver.remote.webelement import WebElement

from model.request import UserInfo
from .items import RoleItem
from .modal import modal_accept_with_comment


class UsersUI(UserInfo):

    def __init__(self, app, parent: WebElement):
        self._app = app
        self._parent = parent  # веб элемент в списке пользователей (слева)
        self.name = parent.text
        self._multiple_users_ = "Все пользователи" in self.name
        self._elements = None
        self.roles = None

    def __getitem__(self, item: str) -> RoleItem:
        """Возвращаем роль пользователя по имени роли"""
        for role in self.roles:
            if role.role.name == item:
                return role
        raise Exception(f'Роли с именем "{item}" у пользователя "{self.name}" не найдено')

    def open(self):
        """Кликаем на пользователя и считываем роли (items)"""
        self._parent.click()
        sleep(1)
        self.read_items()

    def read_items(self):
        """Если нет ролей, то считываем все роли и заполняем данные пользователя"""
        if self.roles is None:
            self._elements = self.Elements(self._app)
            rows = self._elements.get_roles
            self.roles = []
            for i in range(len(rows)):
                self.roles.append(RoleItem(self._app, rows[i], i, self._multiple_users_))
            UserInfo.__init__(self, **self._elements.fio,
                              employment_full_name=self._elements.employment)

    def read_all_history(self):
        """Считываем все хистори для данного пользователя"""
        i = 0
        for role in self.roles:
            with self.scroll_to_role(i):
                role.read_history()
            i += 1

    @contextmanager
    def scroll_to_role(self, i: int):
        """контекст менеджер для скора до конкретной истории"""
        item_width = 123  # высота блока в px item от названия роли до "подробнее"
        width = item_width * i
        self._app.simulate_wheel(self._app.find_element_by_xpath("//body"), width)
        yield
        self._app.simulate_wheel(self._app.find_element_by_xpath("//body"), -width)

    def approve_all(self):
        self._elements.btn_do_all_by_name("Согласовать все").click()

    def confirm_all(self):
        self._elements.btn_do_all_by_name("Подтвердить все").click()

    def revoke_all(self):
        self._elements.btn_do_all_by_name("Отозвать все").click()

    def reject_all(self):
        self._elements.btn_do_all_by_name("Отклонить все").click()

    def specify_all(self, comment="Тестовый комментарий"):
        self._elements.btn_do_all_by_name("Уточнить все").click()
        modal_accept_with_comment(self._app, comment)

    def delegate_all(self, new_delegate: str, comment="Тестовый комментарий"):
        self._elements.btn_do_all_by_name("Делегировать все").click()
        modal_accept_with_comment(self._app, comment, new_delegate)

    def restart_all(self, comment="Тестовый комментарий"):
        self._elements.btn_do_all_by_name("Перезапустить все").click()
        modal_accept_with_comment(self._app, comment)

    def return_all(self, comment="Тестовый комментарий"):
        self._elements.btn_do_all_by_name("Вернуть все").click()
        modal_accept_with_comment(self._app, comment)

    def cancel_all(self, comment="Тестовый комментарий"):
        raise Exception("Этот метод надо написать")

    class Elements:

        def __init__(self, app):
            self._app = app
            self._role_card_ = self._get_role_card_

        @property
        def _get_role_card_(self) -> WebElement:
            xpath = '//div[@class="theme-panel roles-panel x-panel x-box-item x-panel-default"]'
            return self._app.find_element_by_xpath(xpath)

        @property
        def get_roles(self) -> list:
            xpath = './/table'
            return self._role_card_.find_elements_by_xpath(xpath)

        def btn_do_all_by_name(self, btn_name) -> WebElement:
            xpath = f'.//span[contains(text(),"{btn_name}")]'
            return self._role_card_.find_element_by_xpath(xpath)

        @property
        def fio(self) -> dict:
            """Вернет ФИО пользователя, которому назначают роли"""
            xpath = '//div[contains(@class, "roles-panel-toolbar")]//a'
            fio = self._role_card_.find_element_by_xpath(xpath).text
            if fio == "":
                return {"last_name": None, "first_name": None, "additional_name": None}
            else:
                fio = fio.split(" ")
                return {"last_name": fio[0], "first_name": fio[1], "additional_name": fio[2]}

        @property
        def employment(self) -> str:
            xpath = '//div[contains(@class, "roles-panel-toolbar")]//div[contains(@class,"x-form-item-body")]//span'
            employment = self._role_card_.find_elements_by_xpath(xpath)[0].text
            department = self._role_card_.find_elements_by_xpath(xpath)[1].text
            return department + ", " + employment
