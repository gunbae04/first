"""
================================================================================
채팅 전송 및 AI 응답 테스트의 핵심 설계 포인트
================================================================================

Q1. 테스트 함수 내부에 로그인하는 코드가 전혀 없는데, 어떻게 채팅 테스트가 가능한가요?
A1. Pytest의 강력한 기능인 'Fixture(픽스처)'를 활용해 `authenticated_driver`를 주입(Injection)받았기 때문입니다.
    E2E 테스트에서는 '사전 조건(Pre-condition)' 셋업과 '메인 검증 로직'을 철저히 분리해야 합니다. 
    공통 픽스처가 브라우저를 띄우고 로그인까지 마친 완벽한 상태의 driver를 넘겨주므로, 본 스크립트에서는 
    오직 '채팅 기능' 이라는 본연의 목적에만 100% 집중하여 코드를 작성할 수 있습니다.

Q2. AI 응답을 검증할 때 왜 정확한 답변 일치(==)를 확인하지 않고, 텍스트가 비어있지 않은지(len > 0)만 확인하나요?
A2. 헬피챗과 같은 LLM(대형 언어 모델) 기반 AI는 동일한 질문에도 매번 미세하게 다른 문장을 생성하는 '비결정적(Non-deterministic)' 특성이 있습니다.
    기존 웹 QA처럼 `assert response == "특정 문자열"` 방식을 사용하면, AI가 조사 하나만 다르게 대답해도 테스트가 실패(Flaky Test)하게 됩니다.
    따라서 이 단계의 테스트는 AI 답변의 '내용 품질'을 평가하는 것이 아니라, '사용자의 입력이 서버로 전송되고, AI의 응답이 UI 화면에 정상적으로 렌더링되는가'를 확인하는 시스템 파이프라인(E2E) 점검에 목적을 둡니다.

Q3. 함수 위에 붙은 @allure.feature, @allure.story 데코레이터는 무슨 역할을 하나요?
A3. 코드 레벨의 테스트를 기획자, PM 등 비개발 직군도 쉽게 읽을 수 있는 '시각적 리포트(Allure)'로 구조화하기 위한 라벨링 작업입니다.
    현업에서 사용하는 애자일(Agile) 보드나 테스트 관리 시스템(TMS)의 에픽(Epic) - 피처(Feature) - 스토리(Story) 계층 구조와 
    자동화 코드를 1:1로 매핑하여, 결함이 발생했을 때 어느 기획 단위에서 문제가 생겼는지 추적성(Traceability)을 극대화합니다.
================================================================================
"""



"""
헬피챗 채팅 전송 및 AI 응답 기능에 대한 UI 시나리오 테스트 스크립트.
"""

import allure
from pages.chat_page import ChatPage

# 로거 설정
from utils.logger import get_custom_logger
logger = get_custom_logger(__name__)

@allure.feature("채팅 기능")
@allure.story("메시지 전송 및 응답")
class TestChat:
    """채팅 기능 검증 테스트 스위트"""

    @allure.title("[TC-CHAT-001] 정상 로그인 사용자 AI 응답 확인 테스트")
    def test_send_chat_and_receive_response(self, authenticated_driver): # 'authenticated_driver'를 주입받기
        """
        [TC-CHAT-001] 정상적으로 로그인한 사용자는 헬피챗에서 메시지를 전송하고 AI의 응답을 받을 수 있어야 한다.
        """
        # 1. Page Object 초기화 (로그인 픽스처 주입)
        chat_page = ChatPage(authenticated_driver)
        
        # 2. 테스트 액션(Test Action): 메시지 전송
        # 사전 조건(로그인)은 픽스처가 대신 해주므로 바로 메인 로직 시작
        test_message = "소프트웨어 QA에 대해 10글자 이내로 짧게 설명해줘."
        chat_page.send_message(test_message)
        
        # 3. 검증(Assertion): AI 응답 대기 및 확인
        response_text = chat_page.wait_for_ai_response()
        
        # [참고] Jira 연동 테스트 시 아래 주석을 풀고 강제 에러 발생시키기!
        # assert response_text == "일부러 틀리는 텍스트", "Jira 테스트용 강제 에러"
        
        # 응답이 정상적으로 돌아왔는지 확인 (빈 문자열이 아님을 검증)
        assert response_text, "AI 응답 요소를 찾을 수 없습니다."
        assert len(response_text.strip()) > 0, "AI 응답 텍스트가 비어있습니다."
        
        logger.info(f"전송한 메시지: {test_message}")
        logger.info(f"AI 응답 내용: {response_text}")