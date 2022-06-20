from time import sleep

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from model.request import HistoryRecord, HistoryRecordDecision
from .config import implicitly_wait_sec


class HistoryUI(HistoryRecord):

    def __init__(self, app, parent: WebElement, row: WebElement, multiple_users=False):
        """
        :param row - WebElement <tr> в таблице истории
        :param multiple_users True если заявка для нескольких пользователей, False - для одного
        """
        self._app = app
        self._parent = parent
        self._elements = self.Elements(app, row, multiple_users)
        self._multiple_users_ = multiple_users

        self.time = self._elements.time

        """для кого заявка, если заявка для нескольких пользователей"""
        self.for_whom = self._elements.for_whom if self._multiple_users_ else None

        super().__init__(initiator=self._elements.initiator,
                         step_name=self._elements.step_name,
                         # date=_elements.date,
                         comment=self._elements.comment,
                         decision=HistoryRecordDecision.get_decision_by_value(self._elements.decision),
                         next_approver=self._elements.next_approver)

    def assign_approver(self, delegate):
        self._elements.btn_assign_approver.click()
        sleep(.05)
        """модалка выбор пользователя + комент"""
        search_user_field = self._app.find_element_by_xpath('//input[contains(@class, "x-form-required-field")]')
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

        def __init__(self, app, item: WebElement, multiple_users=False):
            self._app = app
            self._item = item
            """Вводим offset (сдвиг) на одну колонку для заявок на несколько пользователей"""
            self.offset = 1 if multiple_users else 0

        @property
        def initiator(self) -> str:
            xpath = '(.//td)[1]/div/div'
            return self._item.find_element_by_xpath(xpath).text.split(" ")[0]

        @property
        def step_name(self) -> str:
            xpath = '(.//td)[1]/div/span'
            return self._item.find_element_by_xpath(xpath).text.replace(":", "")

        @property
        def date(self) -> str:
            xpath = '(.//td)[2]/div/div'
            return self._item.find_element_by_xpath(xpath).text.replace(",", "")

        @property
        def time(self) -> str:
            xpath = '(.//td)[2]/div/div[2]'
            return self._item.find_element_by_xpath(xpath).text

        @property
        def for_whom(self) -> str:
            xpath = '(.//td)[3]/div'
            return self._item.find_element_by_xpath(xpath).text

        @property
        def decision(self) -> str:
            xpath = f'(.//td)[{4 + self.offset}]/div/div'
            return self._item.find_element_by_xpath(xpath).text

        @property
        def next_approver(self) -> str:
            """
            если элемент найден, то возвращаем его, если нет то None
            для кейсов 'Отправил на уточнение инициатору Administrator inRights'
            где мы вернем Administrator inRights"""
            xpath = f'(.//td)[{4 + self.offset}]/div/div[2]'
            with self._app.implicitly_wait_sec(implicitly_wait_sec):
                try:
                    return self._item.find_element_by_xpath(xpath).text.split(" ")[0]
                except NoSuchElementException:
                    return None

        @property
        def comment(self) -> str:
            xpath = f'(.//td)[{5 + self.offset}]'
            _comment_ = self._item.find_element_by_xpath(xpath).text
            return _comment_ if _comment_ != "" else None

        @property
        def btn_assign_approver(self) -> WebElement:
            xpath = './/span[contains(text(),"Назначить")]'
            return self._item.find_element_by_xpath(xpath)


class ErrorInHistory:
    def __init__(self, app, item: WebElement):
        self._app = app
        self._item = item
        self._elements = self.Elements(self._app, item)

    def recompute(self):
        self._elements.btn_rerun.click()
        self._app.session.wait_data_loading()

    def assign_approver(self, delegate):
        self._elements.btn_assign_approver.click()
        sleep(.05)
        """модалка выбор пользователя + комент"""
        search_user_field = self._app.find_element_by_xpath('//input[contains(@class, "x-form-required-field")]')
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

        @property
        def error_block(self) -> str:
            xpath = ".//div[@class='x-fi fi-attention-delta-slim image-error']"
            return self._item.find_element_by_xpath(xpath).text

        @property
        def tip_block(self) -> str:
            xpath = ".//div[@class='x-component text-box x-box-item x-component-default']"
            return self._item.find_element_by_xpath(xpath).text

        @property
        def btn_rerun(self) -> WebElement:
            xpath = ".//span[contains(text(), 'Перезапустить')]"
            return self._item.find_element_by_xpath(xpath)

        @property
        def btn_assign_approver(self) -> WebElement:
            xpath = ".//span[contains(text(), 'Назначить')]"
            return self._item.find_element_by_xpath(xpath)