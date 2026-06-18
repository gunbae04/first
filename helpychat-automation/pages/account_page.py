"""
================================================================================
계정 관리 페이지(POM)의 핵심 화면 제어 기술
================================================================================

Q1. go_to_account_settings 함수에서 window_handles를 이용해 창을 전환하는 이유는 무엇인가요?
A1. 웹 사이트에서 링크가 '새 탭(target="_blank")'으로 열릴 때, 사람의 눈에는 새 창이 바로 보이지만
    Selenium의 내부 제어권(Focus)은 여전히 원래 있던 첫 번째 탭에 머물러 있기 때문입니다.
    따라서 명시적으로 "가장 마지막에 새로 열린 탭(handles[-1])으로 제어권을 넘겨라(switch_to.window)"라고 
    코드를 작성하지 않으면, 새 창에 있는 요소를 찾지 못해 NoSuchElementException 에러가 발생하게 됩니다.

Q2. 연필 아이콘(EDIT_PW_BUTTON)을 찾을 때 왜 복잡한 XPath를 사용했나요?
A2. 계정 관리 화면에는 이메일 수정, 전화번호 수정 등 똑같이 생긴 '연필 아이콘' 버튼이 여러 개 존재할 수 있습니다.
    단순히 클래스명이나 태그로 찾으면 엉뚱한 버튼을 클릭할 위험이 있습니다.
    따라서 "//div[p[contains(text(), '********')]]//button" 처럼 
    "화면에 '********'(비밀번호 마스킹) 텍스트를 가진 영역 바로 옆에 있는 버튼을 찾아라"라고 
    구조적/문맥적 관계를 맺어주면(Relative Locator), UI 디자인이 바뀌어도 절대 깨지지 않는 매우 견고한 자동화가 됩니다.

Q3. change_password 메서드에 submit=True 라는 파라미터를 둔 이유는 무엇인가요?
A3. 단 하나의 메서드로 정상 테스트(Positive)와 예외 테스트(Negative)를 모두 소화하기 위함입니다.
    정상적인 비밀번호를 입력할 때는 마지막에 '완료' 버튼을 눌러야 하지만, 
    8자리 미만 등 규칙에 어긋나는 비밀번호를 입력하는 예외 테스트에서는 버튼 자체가 비활성화되어 누를 수가 없습니다.
    이때 테스트 스크립트에서 submit=False 옵션을 주면, 에러 없이 텍스트 입력까지만 하고 빠져나오므로 
    Page Object의 코드 중복을 획기적으로 줄이고 재사용성을 높일 수 있습니다.
================================================================================
"""



"""
계정 관리 페이지의 UI 요소와 액션을 정의한 POM 클래스.
"""

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from .base_page import BasePage

class AccountPage(BasePage):
    # 1. 프로필 드롭다운 메뉴 관련
    PROFILE_AVATAR = (By.CSS_SELECTOR, "button.MuiAvatar-root")      # 사람 아이콘
    ACCOUNT_MENU = (By.CSS_SELECTOR, "a[href*='accounts.elice.io']") # 계정 관리 메뉴

    # 2. 계정 정보 화면 관련
    # 비밀번호 항목 옆의 연필 아이콘 (SVG 아이콘을 포함하는 버튼)
    EDIT_PW_BUTTON = (By.XPATH, "//div[p[contains(text(), '********')]]//button")
    
    # 3. 비밀번호 변경 폼 관련
    CURRENT_PW_INPUT = (By.NAME, "password")                   # 기존 비밀번호
    NEW_PW_INPUT = (By.NAME, "newPassword")                    # 새 비밀번호
    CONFIRM_PW_INPUT = (By.NAME, "confirmPassword")            # 새 비밀번호 확인
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit']") # 완료 버튼
    
    # 4. 검증 메시지 관련 로케이터
    SUCCESS_SNACKBAR = (By.ID, "notistack-snackbar")       # 성공 알림창(Snackbar) 로케이터
    INPUT_ERROR_MESSAGE = (By.CSS_SELECTOR, "p.Mui-error") # 입력 폼 에러 메시지 로케이터 (공통)

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    @allure.step("계정 관리 탭으로 이동")
    def go_to_account_settings(self):
        """메인 화면에서 프로필 아이콘을 눌러 계정 관리 화면으로 이동합니다."""
        self.click(self.PROFILE_AVATAR)
        self.click(self.ACCOUNT_MENU)

        # Selenium의 제어권을 새로 열린 탭으로 이동
        self.wait.until(lambda d: len(d.window_handles) > 1) # 1. 브라우저의 탭이 2개 이상 뜰 때까지 대기
        handles = self.driver.window_handles                 # 2. 현재 열려있는 모든 탭의 ID(Handle) 목록을 가져옴
        self.driver.switch_to.window(handles[-1])            # 3. 리스트의 맨 마지막 요소([-1]), 즉 가장 최근에 새로 열린 탭으로 제어권 이동
        self.wait_for_url_contains("accounts.elice.io")      # 4. 새 창이 완전히 로딩될 때까지 대기

    @allure.step("비밀번호 변경 폼 작성 및 제출")
    def change_password(self, current_pw: str, new_pw: str, submit: bool = True):
        """기존 비밀번호와 새 비밀번호를 입력하여 변경을 시도합니다."""
        self.click(self.EDIT_PW_BUTTON) # 연필 아이콘 클릭
        
        # 입력창에 각각 타이핑
        self.enter_text(self.CURRENT_PW_INPUT, current_pw)
        self.enter_text(self.NEW_PW_INPUT, new_pw)
        self.enter_text(self.CONFIRM_PW_INPUT, new_pw) # 확인란에도 동일한 새 비밀번호 입력
        
        if submit:
            self.click(self.SUBMIT_BUTTON) # 완료 클릭
    
    def get_success_message(self) -> str:
        """비밀번호 변경 완료 후 화면 좌측 하단에 나타나는 토스트(알림창)의 텍스트를 반환합니다."""
        return self.get_text(self.SUCCESS_SNACKBAR)

    def get_input_error_message(self) -> str:
        """입력창 하단에 나타나는 붉은색 에러 텍스트를 반환합니다."""
        return self.get_text(self.INPUT_ERROR_MESSAGE)