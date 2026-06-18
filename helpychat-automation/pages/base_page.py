"""
================================================================================
BasePage 클래스 및 POM(Page Object Model) 설계의 핵심
================================================================================

Q1. 왜 Selenium의 기본 기능인 `driver.find_element().click()`을 직접 쓰지 않고 BasePage를 만들어 감싸서(Wrapping) 사용하나요?
A1. '코드 재사용성'과 '유지보수성'을 극대화하기 위함입니다. (DRY 원칙 - Don't Repeat Yourself)
    실제 E2E 스크립트에서 클릭이나 타이핑을 하기 전에는 항상 "요소가 화면에 뜰 때까지 기다리는(Wait)" 방어적 코드가 동반되어야 합니다.
    만약 수백 개의 테스트 스크립트마다 `WebDriverWait(driver, 10).until(...)` 코드를 중복해서 작성한다면 코드가 매우 지저분해집니다.
    따라서 BasePage라는 부모 클래스에 대기(Wait) 로직이 포함된 `click`, `enter_text` 메서드를 단 한 번만 정의해 두고,
    모든 자식 페이지(LoginPage, ChatPage 등)가 이를 상속받아 편하게 호출만 하도록 아키텍처를 설계하는 것입니다.

Q2. time.sleep(3) 처럼 무조건 3초를 기다리는 방식을 쓰지 않고, 왜 명시적 대기(Explicit Wait)를 사용하나요?
A2. 자동화 테스트의 '속도'와 '안정성' 두 마리 토끼를 모두 잡기 위해서입니다.
    - time.sleep(고정 대기): 요소가 0.1초 만에 나타나도 무조건 3초를 기다려야 하므로 전체 파이프라인 속도가 엄청나게 느려집니다.
    - Explicit Wait(명시적 대기): "최대 10초까지 기다리되, 그전에 요소가 나타나면 즉시 다음 코드를 실행하라"는 스마트한 방식입니다. 
      네트워크 지연이나 렌더링 속도 차이로 인해 발생하는 'Flaky Test(어쩔 땐 통과하고 어쩔 땐 실패하는 테스트)'를 방지하는 가장 강력한 무기입니다.

Q3. 각 메서드 위에 붙은 `@allure.step(...)`은 무슨 역할을 하나요?
A3. 실행 리포트(Allure)를 시각적으로 구조화해 주는 데코레이터입니다.
    이 데코레이터를 붙여두면, 테스트가 실패했을 때 단순히 "에러 발생!"이라고 찍히는 것이 아니라,
    "1. 로그인 탭으로 이동 -> 2. 아이디 입력 -> 3. 비밀번호 입력 -> 4. 클릭(여기서 실패!)" 처럼 
    사용자의 액션 스텝(Step)이 리포트에 상세히 기록되어 디버깅 속도를 비약적으로 높여줍니다.
================================================================================
"""



"""
모든 Page Object가 상속받는 최상위 부모 클래스.
공통 동작(클릭, 입력, 텍스트 추출 등)과 명시적 대기를 래핑합니다.
"""

import allure
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config.config import DEFAULT_WAIT_TIME

class BasePage:
    """모든 페이지 객체의 부모 클래스"""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, DEFAULT_WAIT_TIME) # 프로젝트 표준 기본 대기 시간(10초)

    @allure.step("클릭: {locator}")
    def click(self, locator: tuple):
        """요소가 클릭 가능해질 때까지 대기 후 클릭합니다."""
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    @allure.step("텍스트 입력: {locator} -> '{text}'")
    def enter_text(self, locator: tuple, text: str):
        """요소가 화면에 보일 때까지 대기 후 텍스트를 입력합니다."""
        element = self.wait_for_visible(locator)
        element.clear()
        element.send_keys(text)

    @allure.step("텍스트 추출: {locator}")
    def get_text(self, locator: tuple) -> str:
        """요소가 화면에 보일 때까지 대기 후 텍스트를 반환합니다."""
        element = self.wait_for_visible(locator)
        return element.text
    
    @allure.step("요소 사라짐 대기: {locator} (최대 {timeout}초)")
    def wait_until_invisible(self, locator: tuple, timeout: int = 10):
        """
        요소가 화면에서 완전히 사라질 때까지 지정된 시간(기본 10초)만큼 대기합니다.
        주의: 여기서 쓰이는 타이머는 __init__의 self.wait과 별개인 '일회용 타이머'입니다.
        """
        # 기본 10초를 무시하고, 인자로 받은 10초짜리 새로운 대기 객체(custom_wait)를 생성!
        custom_wait = WebDriverWait(self.driver, timeout)
        # invisibility_of_element_located: hidden, detached, removed, display:none, opacity:0 등 모든 '보이지 않는 상태'를 포괄적으로 감지
        custom_wait.until(EC.invisibility_of_element_located(locator))
    
    @allure.step("URL 변경 대기: '{text}' 포함 여부")
    def wait_for_url_contains(self, text: str):
        """현재 브라우저의 URL에 특정 텍스트가 포함될 때까지 대기합니다."""
        self.wait.until(EC.url_contains(text))
    
    @allure.step("요소 노출 대기: {locator}")
    def wait_for_visible(self, locator: tuple):
        """요소가 화면에 렌더링되어 시각적으로 보일 때까지 대기하고, 해당 요소를 반환합니다."""
        return self.wait.until(EC.visibility_of_element_located(locator))