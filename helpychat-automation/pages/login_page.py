"""
================================================================================
로그인 페이지(POM)의 핵심 검증 전략
================================================================================

Q1. LoginPage의 __init__ 메서드에서 `base_url`을 인자로 받는 이유는 무엇인가요?
A1. E2E 자동화 스크립트는 개발 서버(Dev), 스테이징 서버(Staging), 실서버(Prod) 등 다양한 환경에서 동일하게 동작해야 합니다.
    만약 클래스 내부에 URL(예: "https://dev.elice.io")을 하드코딩해 두면, 서버 환경이 바뀔 때마다 코드를 모두 수정해야 합니다.
    따라서 환경 변수(.env)나 conftest.py에서 주입해 주는 `base_url`을 인자로 받아 동적으로 처리하게 설계하는 것이 
    자동화 프레임워크의 기본 원칙입니다.

Q2. 로그인 성공 여부를 판단(is_login_successful)할 때, 특정 요소(버튼, 로고 등)가 나타나는지 확인하지 않고 URL(url_contains)을 확인하는 이유는 무엇인가요?
A2. 요소 기반 검증보다 URL 기반 검증이 UI 변경에 훨씬 강건(Robust)하기 때문입니다.
    만약 "로그인 성공 후 나타나는 프로필 아이콘"으로 성공을 판단하게 짰다고 가정해 봅시다. 
    다음날 프론트엔드 개발자가 프로필 아이콘의 클래스명이나 구조를 변경하면, 로그인은 잘 되었음에도 불구하고 
    자동화 코드는 요소를 찾지 못해 실패(False Negative)하게 됩니다.
    반면 라우팅 경로(URL)는 웬만해서는 바뀌지 않는 시스템 아키텍처의 영역이므로, 
    "url_contains('ai-helpy-chat')" 처럼 URL로 페이지 전환 성공 여부를 판단하는 것이 가장 안정적인 검증 방식입니다.

Q3. is_login_successful 메서드에서 TimeoutException을 잡아서 False를 리턴하는 구조는 어떤 이점이 있나요?
A3. '단일 메서드 다중 목적(Reusability)'을 달성하기 위함입니다.
    이 구조 덕분에 해당 메서드는 성공하는 케이스(Positive Test)뿐만 아니라, 
    일부러 틀린 비밀번호를 입력해서 로그인이 실패해야만 하는 케이스(Negative Test)에서도 공용으로 사용할 수 있습니다.
    (예: assert is_login_successful() == False)
================================================================================
"""



"""
로그인 페이지의 UI 요소와 액션을 정의한 Page Object Model 클래스.
"""

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
from .base_page import BasePage

class LoginPage(BasePage):
    """헬피챗 로그인 화면 조작 및 검증 클래스"""

    # 로그인 폼 관련 Locators
    LOGIN_ID_INPUT = (By.CSS_SELECTOR, "input[name='loginId']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[name='password']")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")

    def __init__(self, driver: WebDriver, base_url: str):
        super().__init__(driver) # 부모 클래스의 driver, wait 초기화 활용
        self.base_url = base_url

    @allure.step("로그인 페이지 접속")
    def open(self):
        """로그인 페이지 주소로 브라우저 이동 (비로그인 상태면 로그인 화면으로 리다이렉트 됨을 가정)"""
        self.driver.get(self.base_url)

    @allure.step("계정 정보 입력 및 로그인 시도")
    def login(self, login_id: str, password: str):
        """ID와 비밀번호를 입력하고 로그인 시도"""
        self.enter_text(self.LOGIN_ID_INPUT, login_id) # ID 입력
        self.enter_text(self.PASSWORD_INPUT, password) # 비밀번호 입력
        self.click(self.LOGIN_BUTTON)                  # 로그인 버튼 클릭

    @allure.step("로그인 성공 여부(URL 기반) 확인")
    def is_login_successful(self) -> bool:
        """로그인 성공 후 URL에 메인 경로가 포함되었는지 확인"""
        try:
            # 1단계: URL 주소 기반 확인 (가장 추천하는 방식)
            # 로그인 성공 후 도달하는 메인 URL 경로가 나타날 때까지 대기
            self.wait_for_url_contains("ai-helpy-chat")
            
            # 2단계: 실제 서비스 화면이 그려졌는지 추가 확인 (URL만으로 끝내면 race condition 생길 수 있음)
            self.wait_for_visible((By.CSS_SELECTOR, "button > svg[data-testid='PersonIcon']"))
            return True
        except TimeoutException:
            return False