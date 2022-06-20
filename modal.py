"""
Сюда вынесено модальное окно, чтобы можно было легко выпилить
и заменить на новый класс
"""

def modal_accept_with_comment(app, comment="Тестовый комментарий", new_delegate=None):
    app.sleep(.05)
    modal = app.find_element_by_xpath('//div[contains(@class,"confirm-window")]')
    app.sleep(.05)
    if new_delegate:
        modal.find_element_by_xpath('.//input').send_keys(new_delegate)
        app.session.wait_data_loading()
        app.find_element_by_xpath(f'//li//div[contains(text(), "{new_delegate}")]').click()
        app.sleep(.1)
    modal.find_element_by_xpath('.//textarea').send_keys(comment)
    app.sleep(.05)
    modal.find_element_by_xpath(f'.//span[contains(text(),"Подтвердить")]').click()
    # app.sleep(.05)
    app.session.wait_data_loading()

"""Пожалуй, сохраню это здесь"""
# from root_dir_path import ROOT_DIR
# from selenium.webdriver.remote.webelement import WebElement
#
# def simulate_wheel(element: WebElement, deltaY=120, offsetX=0, offsetY=0):
#     with open(ROOT_DIR + r"\fixture\simulate_wheel.js", "r", encoding="UTF-8") as file:
#         wheel_js = file.read()
#     error = element._parent.execute_script(wheel_js, element, deltaY, offsetX, offsetY)
#     if error:
#         raise Exception(error)
