"""
================================================================================
채팅 및 AI 응답 테스트 시나리오의 핵심 설계 포인트
================================================================================

Q1. 테스트 데이터를 코드 안에 하드코딩하지 않고 CSV 파일(chat_messages.csv)로 분리한 이유는 무엇인가요?
A1. 이를 '데이터 주도 테스트(DDT, Data-Driven Testing)' 기법이라고 부릅니다.
    테스트 코드는 로직(동작 흐름)만 담당하고, 테스트할 값(데이터)은 외부 파일로 분리해야 합니다.
    이렇게 분리해 두면 새로운 질문 케이스가 100개 추가되더라도 파이썬 코드는 단 한 줄도 수정할 필요가 없습니다. 
    개발 지식이 없는 기획자나 수동 QA 담당자도 엑셀(CSV) 파일만 수정하여 자동화 테스트 커버리지를 늘릴 수 있다는 엄청난 장점이 있습니다.

Q2. @pytest.mark.parametrize 데코레이터는 어떤 역할을 하나요?
A2. Pytest에서 DDT를 구현하기 위한 강력한 기능입니다. 
    load_chat_test_data() 함수가 CSV 파일에서 10줄의 데이터를 읽어오면, 이 데코레이터가 알아서 
    동일한 테스트 함수(test_send_chat_and_receive_response)를 10번 반복 실행해 줍니다.
    실행 리포트(Allure)에서도 각 데이터 행이 개별적인 독립된 테스트 케이스로 깔끔하게 기록됩니다.

Q3. AI 응답 결과를 검증할 때 왜 정확한 문자열 일치(==)를 쓰지 않고 핵심 키워드(in) 포함 여부만 검증하나요?
A3. 헬피챗과 같은 생성형 AI(LLM)는 동일한 질문에도 매번 미세하게 다른 문장으로 답변을 생성하는 '비결정적(Non-deterministic)' 특성을 가집니다.
    기존 웹 QA처럼 "응답 텍스트 == 예상 텍스트" 방식으로 검증하면 문장 부호 하나만 달라도 테스트가 실패하는 극심한 불안정성(Flakiness)을 겪게 됩니다.
    따라서 AI 테스트 자동화에서는 문맥을 해치지 않는 선에서 '반드시 포함되어야 할 핵심 키워드'가 들어있는지를 검증하는 것이 가장 실용적이고 안정적인 접근법입니다.
================================================================================
"""



"""
헬피챗 채팅 전송 및 AI 응답 기능에 대한 UI 시나리오 테스트 스크립트.
"""

import csv
import pytest
import allure
from pathlib import Path
from pages.chat_page import ChatPage

# 로거 설정
from utils.logger import get_custom_logger
logger = get_custom_logger(__name__)

def get_project_root() -> Path:
    """
    현재 파일 위치부터 상위 디렉토리로 올라가며 pytest.ini 파일이 있는 
    프로젝트 루트 경로를 동적으로 탐색합니다.
    """
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "pytest.ini").exists():
            return parent
    return current_path.parents[2] # Fallback

def load_chat_test_data():
    """data/chat_messages.csv 파일에서 테스트 시나리오 데이터를 읽어옵니다."""
    
    # 1. 동적 경로 탐색 함수를 통해 프로젝트 루트 디렉토리(pytest.ini 위치)를 가져옵니다.
    # (CI/CD 서버 환경이 바뀌거나 터미널 실행 위치가 달라져도 절대 경로를 잃어버리는 현상 100% 차단)
    base_dir = get_project_root()

    # 2. 루트 폴더에서 'data', 'chat_messages.csv' 폴더/파일을 조합
    csv_file_path = base_dir / "data" / "chat_messages.csv"

    test_cases = []
    # 3. 계산된 동적 절대 경로(csv_file_path)를 사용하여 파일 오픈
    with open(csv_file_path, "r", encoding="utf-8") as f:
        # 첫 줄을 헤더(Key)로 인식하여 딕셔너리 형태로 읽음
        reader = csv.DictReader(f)
        for row in reader:
            test_cases.append(row)

    return test_cases

@allure.feature("채팅 기능")
@allure.story("메시지 전송 및 응답")
class TestChat:

    @allure.title("데이터 주도 테스트(DDT) - AI 응답 및 핵심 키워드 검증")
    # 🎯 CSV 데이터 배열을 주입하여 데이터 개수만큼 테스트 케이스가 자동 생성됩니다.
    @pytest.mark.parametrize("scenario", load_chat_test_data())
    def test_send_chat_and_receive_response(self, authenticated_driver, scenario):
        """
        [DDT 시나리오] 외부 데이터 파일을 기반으로 다중 문맥 질문에 대한 AI 정합성을 검증합니다.
        """
        chat_page = ChatPage(authenticated_driver)
        
        test_message = scenario["message"]
        expected_keyword = scenario["expected_keyword"]
        scenario_id = scenario["scenario_id"]

        logger.info(f"[{scenario_id}] AI에게 메시지를 전송합니다: '{test_message}'")
        chat_page.send_message(test_message)
        
        response_text = chat_page.wait_for_ai_response()
        logger.info(f"[{scenario_id}] AI 응답 수신 완료: '{response_text}'")
        
        # 기본 응답 검증
        assert response_text is not None, f"[{scenario_id}] AI 응답 요소를 찾을 수 없습니다."
        assert len(response_text.strip()) > 0, f"[{scenario_id}] AI 응답 텍스트가 비어있습니다."
        
        # 🎯 핵심 문맥 검증: 각 질문에 맞는 기대 키워드가 답변에 포함되어 있는지 검증
        assert expected_keyword in response_text, (
            f"[{scenario_id}] 결함 발견: AI 답변에 기대 키워드 '{expected_keyword}'가 포함되지 않았습니다. "
            f"(실제 답변: {response_text})"
        )