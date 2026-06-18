"""
================================================================================
온보딩(약관 동의) 화면 및 숨겨진 UI 요소 제어 기법
================================================================================

Q1. 체크박스를 클릭할 때 부모 클래스의 click() 메서드를 쓰지 않고 JavaScript(JS) 클릭을 사용한 이유는 무엇인가요?
A1. MUI(Material-UI), React 등 최신 프론트엔드 프레임워크의 특성 때문입니다.
    이런 프레임워크들은 예쁜 디자인을 위해 실제 HTML `<input type='checkbox'>` 태그를 투명하게(opacity: 0) 만들거나 숨기고, 
    그 위에 가짜 이미지(svg)나 <span> 태그를 덮어씌워 렌더링합니다. 
    이때 Selenium의 일반 click()을 사용하면 "다른 요소가 클릭을 가로챘다(ElementClickInterceptedException)"며 에러가 발생합니다.
    따라서 브라우저의 DOM에 직접 접근하여 이벤트를 강제로 발생시키는 `execute_script("arguments[0].click();")`를 
    사용하는 것이 가장 확실하고 견고한 우회(Workaround) 방법입니다.

Q2. 체크박스를 찾을 때 요소 대기 조건을 `element_to_be_clickable`이 아닌 `presence_of_element_located`로 둔 이유는 무엇인가요?
A2. Q1의 이유와 이어집니다. 실제 `<input>` 태그가 시각적으로 숨겨져 있거나 크기가 0x0으로 설정되어 있으면, 
    Selenium은 이 요소가 화면에 '보이지 않는다(Not Visible)'고 판단하여 `element_to_be_clickable` 대기 조건에서 영원히 실패(Timeout)합니다.
    따라서 "눈에 보이든 안 보이든, HTML DOM 트리 구조 안에 존재하기만 하면 가져와라"라는 의미의 
    `presence_of_element_located`를 사용하여 요소를 찾은 뒤 JS로 클릭하는 콤보를 사용하는 것입니다.

Q3. 약관 동의는 계정당 최초 1회만 발생하는데, 이 페이지 코드는 어떻게 활용되나요?
A3. E2E 테스트는 '상태(State)'에 매우 민감합니다. 
    이 클래스 자체는 약관 동의를 수행하는 기능만 정의해 두고, 실제 호출하는 곳(`conftest.py`나 `test_login.py`)에서 
    `try-except` 블록으로 감싸서 사용합니다. 이렇게 '상태 의존성'을 분리하여 설계하면, 
    신규 계정이든 기존 계정이든 코드 수정 없이 멱등성(Idempotence, 몇 번을 실행해도 동일한 결과를 보장)을 갖는 프레임워크가 완성됩니다.
================================================================================
"""



"""
최초 로그인 시 나타나는 약관 동의 및 온보딩 화면을 처리하는 클래스.
"""

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage

class SignupPage(BasePage):
    """약관 동의 및 계정 생성 프로세스 처리 클래스"""

    # MUI 체크박스 및 버튼 Locators
    AGREE_ALL_CHECKBOX = (By.CSS_SELECTOR, "input[type='checkbox']") # 체크박스 여러 개 생기면 위험. 추천 ex: form#signup-form input[type='checkbox']
    CREATE_ACCOUNT_BUTTON = (By.CSS_SELECTOR, "button[form='signup-form']")

    def __init__(self, driver: WebDriver):
        super().__init__(driver) # 부모 클래스의 driver, wait 초기화 활용

    @allure.step("약관 동의 및 계정 생성 완료")
    def agree_and_submit(self):
        """약관 동의 체크(JS 클릭) 및 제출 버튼 클릭"""
        # 1. Agree All 체크박스 (일반 클릭이 안 될 경우를 대비해 JavaScript Click 사용)
        agree_checkbox = self.wait.until(EC.presence_of_element_located(self.AGREE_ALL_CHECKBOX))
        self.driver.execute_script("arguments[0].click();", agree_checkbox)
        
        # 2. 부모 클래스의 click 메서드를 활용하여 간결하게 작성
        self.click(self.CREATE_ACCOUNT_BUTTON)