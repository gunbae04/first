"""
================================================================================
채팅 화면(POM) 및 생성형 AI 테스트 동기화 핵심 전략
================================================================================

Q1. 전송 버튼(SEND_BUTTON)을 찾을 때 `button:has(...)`라는 CSS 선택자를 쓴 이유는 무엇인가요?
A1. 최신 웹의 DOM 탐색 트렌드인 'CSS 가상 클래스(:has)'를 활용한 것입니다.
    기존에는 "특정 아이콘(svg)을 품고 있는 부모 버튼(button)"을 찾으려면 복잡하고 느린 XPath(`//button[descendant::svg]`)를 써야만 했습니다.
    하지만 최근 모던 브라우저들이 CSS `:has()`를 지원하기 시작하면서, XPath 없이도 훨씬 직관적이고 빠른 탐색이 가능해졌습니다.
    (단, 구형 환경에서 에러가 난다면 주석에 남겨두신 것처럼 XPath로 우회하는 것이 맞습니다.)

Q2. AI 응답을 기다릴 때 왜 단순히 클래스명만 찾지 않고 `[data-status='complete']` 속성까지 명시했나요?
A2. 헬피챗과 같은 생성형 AI(LLM)는 텍스트를 한 번에 뱉지 않고 한 글자씩 타이핑하는 '스트리밍(Streaming)' UI를 가집니다.
    만약 단순히 텍스트 박스가 화면에 나타나는 것만 기다리면, AI가 첫 글자를 치자마자 코드가 다음으로 넘어가 버려 검증에 실패(Flaky Test)합니다.
    따라서 프론트엔드 코드에 "응답이 완전히 끝났을 때 상태값을 complete로 바꿔달라"고 요구(Testability 확보)하고, 
    자동화 코드는 그 특정 DOM 상태값이 될 때까지 기다리는 것이 AI UI 테스트의 가장 완벽하고 안정적인 동기화 전략입니다.

Q3. wait_for_ai_response 함수 안에서 `assert` 문을 써서 정답이 맞는지 바로 검증하지 않는 이유는 무엇인가요?
A3. Page Object Model(POM)의 가장 엄격한 원칙인 '관심사의 분리(Separation of Concerns)' 때문입니다.
    Page 클래스는 오직 "화면과 어떻게 상호작용(Click, Type, Read)할 것인가"만 책임져야 합니다. 
    만약 여기에 `assert text == "안녕"` 이라고 검증 로직을 넣어버리면, 다른 질문을 던지는 테스트에서는 이 함수를 재사용할 수 없게 됩니다.
    조작(Action)은 Page Object가, 판단(Assertion)은 Test 스크립트가 하도록 철저히 분리해야 프레임워크가 건강하게 유지됩니다.
================================================================================
"""



"""
헬피챗 메인 채팅 화면의 UI 요소와 액션을 정의한 Page Object Model 클래스.
"""

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from .base_page import BasePage

class ChatPage(BasePage):
    """헬피챗 메시지 전송 및 응답 확인 클래스"""

    # 채팅 관련 Locators
    CHAT_INPUT = (By.CSS_SELECTOR, "textarea[name='input']") # 메시지 입력창
    SEND_BUTTON = (By.CSS_SELECTOR, "button:has(svg[data-testid='arrow-upIcon'])") # :has 실행 환경 호환성 이슈 시 XPATH로 변경하기
    
    # AI 응답 관련 Locators
    AI_MESSAGE_CONTENT = (By.CSS_SELECTOR, "div.elice-aichat__markdown[data-status='complete']") # AI의 답변 텍스트 박스

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    @allure.step("AI에게 메시지 전송: '{message}'")
    def send_message(self, message: str):
        """텍스트 영역에 메시지를 입력하고 전송 버튼을 클릭합니다."""
        self.enter_text(self.CHAT_INPUT, message)
        self.click(self.SEND_BUTTON)

    @allure.step("AI 생성 완료 응답 대기 및 텍스트 추출")
    def wait_for_ai_response(self) -> str:
        """AI의 응답이 화면에 완전히 노출될 때까지 대기하고, 해당 텍스트를 반환합니다."""
        return self.get_text(self.AI_MESSAGE_CONTENT)