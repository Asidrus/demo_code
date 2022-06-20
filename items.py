from contextlib import contextmanager

from selenium.common.exceptions import *
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from model.enum_item import EnumItem
# from model.request import ItemStatus, RequestItem, UserInfo, EmploymentInfo, OrgUnitInfo
from model.request import ItemStatus, RequestItem, UserInfo
from model.role import Role
from useful_methods.data_conversion import full_date_to_short

from .history import HistoryUI, ErrorInHistory
from .config import implicitly_wait_sec
from .modal import modal_accept_with_comment
from time import sleep, time

__all__ = [
    "RoleItem",
    "UserItem",
    "AccountItem",
    "UserCardItem",
    "TransferPasswordItem",
]

"""Базовый класс"""


class ItemUI:

    def __init__(self, app, item: WebElement, ind=0, multiple_users=False):
        self._elements = self.Elements(app, item)
        self._app = app
        self._ind = ind  # порядковый номер item'a в списке
        self._multiple_users_ = multiple_users

    @contextmanager
    def scroll_to_history(self, i: int):
        """Контекст менеджер для скоролла к i'той хистори"""
        """ тут нужен калькулятор"""
        item_width = 123  # высота блока в px item от названия роли до "подробнее"
        title_width = 180  # высота шапки таблицы в px от статуса до "кто, дата ..."
        row_width = 89  # высота одной записи истории в px
        width = item_width + title_width + row_width * i
        self._app.simulate_wheel(self._app.find_element_by_xpath("//body"), width)
        yield
        self._app.simulate_wheel(self._app.find_element_by_xpath("//body"), -width)

    # todo: избавиться от warnings
    def scroll_to_this_item(func):
        """Декоратор для скорлла к этому item'у"""
        def wrapper(self, *args, **kwargs):
            item_width = 123  # высота блока в px item от названия роли до "подробнее"
            width = item_width * self._ind
            self._app.simulate_wheel(self._app.find_element_by_xpath("//body"), width)
            func(self, *args, **kwargs)
            self._app.simulate_wheel(self._app.find_element_by_xpath("//body"), -width)

        return wrapper

    def __getitem__(self, item):
        """Получаем историю Item'а по индексу"""
        if self.history_records is None or self.history_records == []:
            self.read_history()
        return self.history_records[item]

    @scroll_to_this_item
    def read_history(self):
        """Считываем историю для данного item'а"""
        self._elements.btn_history.click()
        i = 0
        self.history_records = []
        for row in self._elements.history_rows:
            with self.scroll_to_history(i):
                self.history_records.append(HistoryUI(self._app, self._elements._item, row, self._multiple_users_))
            i += 1
        self._elements.btn_history.click()
        self.history_records = self.history_records[::-1]

    @property
    def get_status(self) -> dict:
        status = self._elements.status
        if status == ItemStatus.CLARIFICATION:
            step_name = self._app.get_hidden_text(self._elements.step_name).replace(":", "")
        else:
            element = self._elements.step_name
            if element is not None:
                step_name = self._elements.step_name.text.replace(":", "")
                step_name = None if step_name == "" else step_name
            else:
                step_name = None
        return {
            "status": status,
            "step_name": step_name,
            "approver": self._elements.approver,
            "approval_date": self._elements.appoval_date
        }

    @scroll_to_this_item
    def read_status_and_approver_from_history(self):
        if (self.status is None or self.status == ItemStatus.INCORRECT) or (self.approver is None):
            self._elements.btn_history.click()
            if self.status is None or self.status == ItemStatus.INCORRECT:
                self.status = self._elements.status_in_history
            if self.approver is None:
                self.approver = self._elements.approver_in_history
            self._elements.btn_history.click()

    @scroll_to_this_item
    def approve(self):
        self._elements.button_by_name("Согласовать").click()

    @scroll_to_this_item
    def confirm(self):
        self._elements.button_by_name("Подтвердить").click()

    @scroll_to_this_item
    def complete(self):
        self._elements.button_by_name("Выполнено").click()

    @scroll_to_this_item
    def revoke(self):
        self._elements.button_by_name("Отозвать").click()

    @scroll_to_this_item
    def reject(self):
        self._elements.button_by_name("Отклонить").click()

    @scroll_to_this_item
    def specify(self, comment="Тестовый комментарий"):
        self._elements.button_by_name("Уточнить").click()
        modal_accept_with_comment(self._app, comment)

    @scroll_to_this_item
    def delegate(self, new_delegate: str, comment="Тестовый комментарий"):
        self._elements.button_by_name("Делегировать").click()
        modal_accept_with_comment(self._app, comment, new_delegate)

    @scroll_to_this_item
    def cancel(self, comment="Тестовый комментарий"):
        self._elements.btn_cancel_item.click()
        sleep(.05)
        self._elements.btn_modal_yes_continue.click()
        modal_accept_with_comment(self._app, comment)

    @scroll_to_this_item
    def return_(self, comment="Тестовый комментарий"):
        self._elements.button_by_name("Вернуть").click()
        modal_accept_with_comment(self._app, comment)

    @scroll_to_this_item
    def recompute(self):
        with self.scroll_to_history(1):
            self._elements.btn_history.click()
            error_history = ErrorInHistory(self._app, self._elements.error_block_history)
            error_history.recompute()

    @scroll_to_this_item
    def assign_approver(self, delegate):
        with self.scroll_to_history(1):
            if "more-text-error" in self._elements.btn_history.get_attribute("class"):
                self._elements.btn_history.click()
                error_history = ErrorInHistory(self._app, self._elements.error_block_history)
                error_history.assign_approver(delegate)
            else:
                self._elements.btn_history.click()
                self._elements.btn_assign_approver.click()
                sleep(.05)
                """модалка выбор пользователя + комент"""
                search_user_field = self._app.find_element_by_xpath(
                    '//input[contains(@class, "x-form-required-field")]')
                search_user_field.clear()
                search_user_field.send_keys(delegate)
                self._app.session.wait_data_loading()
                self._app.sleep(1)
                search_user_field.send_keys(Keys.ENTER)
                self._app.sleep(1)
                self._app.session.wait_data_loading()
                self._app.find_element_by_xpath("//span[contains(text(), 'Подтвердить')]").click()
                self._app.session.wait_data_loading()

    class Elements:

        def __init__(self, app, item: WebElement):
            self._app = app
            self._item = item

        # для ролей
        @property
        def role_name(self) -> str:
            xpath = './/span[@class="role-name"]/a'
            with self._app.implicitly_wait_sec(implicitly_wait_sec):
                try:
                    return self._item.find_element_by_xpath(xpath).text
                except NoSuchElementException:
                    return None

        # <для блокировки и разблокировки УЗ>
        @property
        def account_name(self) -> str:
            xpath = './/span[@class="account-name"]'
            with self._app.implicitly_wait_sec(implicitly_wait_sec):
                try:
                    return self._item.find_element_by_xpath(xpath).text
                except NoSuchElementException:
                    return None

        @property
        def user_name(self) -> str:
            xpath = '//div[./div/span[@class="account-name"]]/div[2]'
            with self._app.implicitly_wait_sec(implicitly_wait_sec):
                try:
                    return self._item.find_element_by_xpath(xpath).text
                except NoSuchElementException:
                    return None

        @property
        def system(self) -> str:
            xpath = '//div[./div/span[@class="account-name"]]/div[3]'
            with self._app.implicitly_wait_sec(implicitly_wait_sec):
                try:
                    return self._item.find_element_by_xpath(xpath).text
                except NoSuchElementException:
                    return None

        # </для блокировки и разблокировки УЗ>

        # <статус и его данные>
        @property
        def status_block(self) -> str:
            """Возвращает xpath блока в котором лежат статус, апрувер, дата и шаг"""
            return './/div[contains(@class, "box-approve")]/div/' \
                   'div[contains(@class, "status-block") or contains(@class,"no-image-wrapper")]'

        def status_row(self, i) -> str:
            xpath = f"/div[{i}]"
            return self._item.find_element_by_xpath(self.status_block + xpath).text

        @property
        def status(self) -> EnumItem:
            """Перебором ищем статус item'а"""
            with self._app.implicitly_wait_sec(implicitly_wait_sec):
                for status in ItemStatus._status_list:
                    try:
                        xpath = f'.//div[contains(@class,"box-approve")]//div[contains(text(), "{status.value}")]'
                        self._item.find_element_by_xpath(xpath)
                        return status
                    except NoSuchElementException:
                        pass
            return ItemStatus.INCORRECT

        @property
        def status_in_history(self) -> EnumItem:
            xpath = './/div[@class="status-title-text"]'
            with self._app.implicitly_wait_sec(implicitly_wait_sec):
                try:
                    return ItemStatus.get_status_by_value(self._item.find_element_by_xpath(xpath).text)
                except NoSuchElementException:
                    return None

        @property
        def approver_in_history(self) -> str:
            xpath = './/div[contains(@class,"x-grid-view detail-grid-body x-grid-with-row-lines x-fit-item x-grid-view-default x-scroller ps")]//table//td[1]'
            with self._app.implicitly_wait_sec(implicitly_wait_sec):
                try:
                    return self._item.find_element_by_xpath(xpath).text.split(" ")[0]
                except NoSuchElementException:
                    return None

        @property
        def step_name(self) -> WebElement:
            xpath = '/div[not(@class) and not(./a)]'
            with self._app.implicitly_wait_sec(implicitly_wait_sec):
                try:
                    return self._item.find_element_by_xpath(self.status_block + xpath)
                except NoSuchElementException:
                    return None

        @property
        def approver(self) -> str:
            with self._app.implicitly_wait_sec(implicitly_wait_sec):
                try:
                    xpath = '//a'
                    approver = self._item.find_element_by_xpath(self.status_block + xpath).text.split(" ")[0]
                    return approver if approver != "" else None
                except NoSuchElementException:
                    pass
                try:
                    xpath = '//span[@class="no-assignee-text"]'
                    approver = self._item.find_element_by_xpath(self.status_block+xpath).text
                    return approver if approver != "" else None
                except NoSuchElementException:
                    return None

        @property
        def appoval_date(self) -> str:
            """Возвращает дату последнего действия (согласования и т.п.) если нет то None"""
            with self._app.implicitly_wait_sec(implicitly_wait_sec):
                try:
                    xpath = '/div[4]'
                    text_date = self._item.find_element_by_xpath(self.status_block + xpath).text
                    return full_date_to_short(text_date.split(",")[0])
                except:
                    return None

        # </статус и его данные>

        @property
        def risk(self) -> str:
            xpath = './/div[@class="risk-name-text"]'
            return self._item.find_element_by_xpath(xpath).text

        @property
        def activation(self) -> str:
            with self._app.implicitly_wait_sec(implicitly_wait_sec):
                try:
                    xpath = './/div[@class="x-container activation-text x-box-item x-container-default"]/div/div'
                    all_text = self._item.find_element_by_xpath(xpath).text
                    prev_date = self._item.find_element_by_xpath(xpath+"/span").text
                    new_date = all_text.replace(prev_date, "")
                    if new_date == "":
                        return None
                    elif "Бессрочно" in new_date:
                        return "Бессрочно"
                    else:
                        return full_date_to_short(new_date.replace(" до ", "").replace("до  ", ""))
                except NoSuchElementException:
                    return None

        @property
        def orgunit(self) -> str:
            with self._app.implicitly_wait_sec(implicitly_wait_sec):
                try:
                    xpath = './/div[@class="x-container employment-text x-box-item x-container-default"]/div/div'
                    return self._item.find_element_by_xpath(xpath).text
                except NoSuchElementException:
                    return None

        def button_by_name(self, button_name):
            xpath = f'.//span[contains(text(),"{button_name}")]'
            return self._item.find_element_by_xpath(xpath)

        @property
        def btn_cancel_item(self):
            """Кнопка отмены заявки (корзинка)"""
            xpath = './/span[contains(@class, "x-btn-icon-el x-btn-icon-el-transparent-medium x-fi fi-trash ")]'
            return self._item.find_element_by_xpath(xpath)

        @property
        def btn_modal_yes_continue(self):
            """Кнопка 'Да, продолжить' в модальном окне"""
            xpath = '//span[contains(text(), "Да, продолжить")]'
            return self._app.find_element_by_xpath(xpath)

        @property
        def btn_history(self) -> WebElement:
            xpath = './/div[contains(text(),"Подробнее")]'
            return self._item.find_element_by_xpath(xpath)

        @property
        def history_rows(self) -> list:
            xpath = './/div[@class="x-panel history-grid theme-panel x-box-item x-panel-legacy x-grid"]//div[' \
                    '@class="x-grid-view x-grid-with-row-lines x-fit-item x-grid-view-default x-scroller ps"]//tr'
            return self._item.find_elements_by_xpath(xpath)

        """для карточек с полями (создание юзера, ТУ и т.д.)"""

        def field_xpath(self, field_title) -> str:
            """xpath для блока, в котором значение и элементы меняющие его"""
            return f'.//div[.//span[contains(text(),"{field_title}")] and contains(@class,"x-table-form-item")]'

        def get_value(self, field_title, new=True) -> str:
            """
            Возвращает значение поля
            :param field_title Имя атрибута ("Дата начала работы") или его часть ("Дата начала")
            :param new default = True, возвращает новое значение, например
                case Изменение полей:
                    Работает -> Уволен
                    if new==true return "Уволен" else "Работает"
                case Создание юзера: вернет единственное новое значение
            """
            xpath = f'//div[contains(@class,"x-form-display-field")]'
            values = self._app.find_element_by_xpath(self.field_xpath(field_title) + xpath).text.split("\n")
            value = values[-1] if new else values[0]
            return value if value != "-" else None

        def is_checked(self, field_title) -> bool:
            """
            Возвращает значение чекбокса
            Usage: self._elements.is_checked("Основное трудоустройство")
            """
            xpath = f'//div[contains(@class, "checkbox") and .//label[contains(text(),"{field_title}")]]'
            return "checked" in self._app.find_element_by_xpath(xpath).get_attribute("class")

        def get_value_from_transfer_password_field(self, field_name) -> str:
            xpath = f'//div[contains(@class,"transfer-password-displayfield") and .//span[contains(text(),"{field_name}")]]/div'
            return self._app.get_hidden_text(self._item.find_element_by_xpath(xpath))
            # return self._item.find_element_by_xpath(xpath).text

        @property
        def error_block_history(self):
            xpath = ".//div[contains(@class, 'history-request-errors')]"
            return self._item.find_element_by_xpath(xpath)

        @property
        def btn_assign_approver(self) -> WebElement:
            xpath = './/span[contains(text(),"Назначить")]'
            return self._item.find_element_by_xpath(xpath)


"""Классы для разных типов заявок"""


class RoleItem(RequestItem, ItemUI):

    def __init__(self, app, parent: WebElement, ind, multiple_users=True):
        ItemUI.__init__(self, app, parent, ind, multiple_users)
        RequestItem.__init__(self, role=Role(name=self._elements.role_name),
                             system=None, account_name=None,  # Не None для раз/блок аккаунтов
                             activation_date=self._elements.activation,
                             **self.get_status
                             )
        """
        фикс для тестов 
        test_approver_clarifies_two_request_items_verify_request_by_initiator
        test_clarify_request_to_block_account_in_inform_sys
        issue: в UI в для item'а в статусе "на уточнении" step_name is hidden,
        однако для блокировки аккаунта мы сравнивание step_name, поэтому мы всегда
        считываем hidden текст, но для ролей в статусе "на уточнении" мы его обнуляем
        """
        if self.status == ItemStatus.CLARIFICATION:
            self.step_name = None


class UserCardItem(RequestItem, ItemUI):
    def __init__(self, app, parent: WebElement, ind, multiple_users=True):
        ItemUI.__init__(self, app, parent, ind, multiple_users)
        RequestItem.__init__(self,
                             system=None, account_name=None,  # Не None для раз/блок аккаунтов
                             activation_date=self._elements.activation,
                             **self.get_status
                             )


class UserItem(UserInfo, ItemUI):
    def __init__(self, app, parent: WebElement):
        ItemUI.__init__(self, app, parent)

        UserInfo.__init__(self, last_name=self._elements.get_value("Фамилия"),
                          first_name=self._elements.get_value("Имя"),
                          additional_name=self._elements.get_value("Отчество"),
                          birth_date=full_date_to_short(self._elements.get_value("Дата рождения")),
                          date_from=full_date_to_short(self._elements.get_value("Дата начала работы")),
                          hr_status=self._elements.get_value("Кадровый статус"),
                          user_type=self._elements.get_value("Тип пользователя"),
                          contract_number=self._elements.get_value("Табельный номер"),
                          manager=self._elements.get_value("Руководитель"),
                          region=self._elements.get_value("Регион"),
                          city=self._elements.get_value("Город"),
                          office=self._elements.get_value("Офис"),
                          last_name_eng=self._elements.get_value("Фамилия (англ.)"),
                          first_name_eng=self._elements.get_value("Имя (англ.)"),
                          additional_name_eng=self._elements.get_value("Отчество (англ.)"),
                          employment_full_name=self._elements.get_value(
                              "Компания, подразделение, должность").replace(" > ", ", "))


class AccountItem(RequestItem, ItemUI):
    def __init__(self, app, item: WebElement, ind=0):
        ItemUI.__init__(self, app, item, ind)
        RequestItem.__init__(self,
                             system=self._elements.system,
                             account_name=self._elements.account_name,
                             **self.get_status)


# class EmploymentItem(EmploymentInfo, ItemUI):
#     def __init__(self, app: Application, parent: WebElement):
#         ItemUI.__init__(self, app, parent)
#         get = lambda name: self._elements.get_value(name)
#         EmploymentInfo.__init__(self, position_full_path=get("Компания, подразделение, должность"),
#                                 contract_number=get("Табельный номер"),
#                                 hire_date=get("Дата начала работы"),
#                                 fire_date=get("Дата увольнения"),
#                                 status=get("Кадровый статус"),
#                                 user_type=get("Тип пользователя"),
#                                 manager=get("Руководитель"),
#                                 is_default_emp=self._elements.is_checked("Основное трудоустройство"),
#                                 region=get("Регион"),
#                                 city=get("Город"),
#                                 office=get("Офис"))


# # todo: переделать на from model.unit import Orgunit
# class OrgUnitItem(OrgUnitInfo, ItemUI):
#     def __init__(self, app, parent: WebElement):
#         ItemUI.__init__(self, app, parent)
#         get = lambda name: self._elements.get_value(name)
#         OrgUnitInfo.__init__(self, full_name=get("Полное название"),
#                              short_name=get("Краткое название"),
#                              parent_unit=get("Родительское подразделение"),
#                              manager=get("Руководитель"),
#                              responsible=get("Ответственный"))


class TransferPasswordItem(RequestItem, ItemUI):
    def __init__(self, app, parent: WebElement):
        ItemUI.__init__(self, app, parent)
        RequestItem.__init__(self,
                             system=self._elements.get_value_from_transfer_password_field("Система"),
                             account_name=self._elements.get_value_from_transfer_password_field("Имя учетной записи"),
                             password=self._elements.get_value_from_transfer_password_field("Пароль"),
                             **self.get_status)
        self.approver = self._elements.approver
        self.read_status_and_approver_from_history()