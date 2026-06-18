"""
================================================================================
세부 특기사항 생성 및 비동기 E2E 테스트 핵심 포인트
================================================================================

Q1. 여러 단계로 이루어진 흐름인데, 왜 [SCENARIO]가 아닌 [TC]라는 이름을 사용하나요?
A1. 개념적으로는 여러 수동 테스트 흐름을 묶은 'SCENARIO'가 맞으나, 개발 및 QA 현장에서는 다음과 같은 이유로 'TC' 라벨을 주로 사용합니다.
    1. 프레임워크의 기준: Pytest 등은 `def test_...()` 함수 하나를 무조건 1개의 'Test Case'로 카운트하고 리포트에 기록합니다.
    2. E2E 테스트의 특성: 수동 테스트는 버튼 클릭 하나를 TC로 쪼개지만, E2E 자동화에서는 '사용자의 시나리오(흐름)' 자체가 거대한 단일 TC 단위가 됩니다. (E2E Test Case == User Scenario)
    3. TMS 연동: Jira(Zephyr, Xray) 등 테스트 관리 도구와 연동할 때, 시스템이 부여하는 고유 ID(TC-1234) 규칙을 코드에 그대로 매핑하여 추적성(Traceability)을 높이기 위함입니다.
    (단, 팀 컨벤션이 SCENARIO 접두사를 쓰기로 합의되었다면 유연하게 변경할 수 있습니다.)

Q2. 이 기능에서 AI 응답을 기다릴 때 특별한 대기(Wait) 기술이 필요한 이유는 무엇인가요?
A2. 생성 요청 직후 나타나는 비동기(Asynchronous) 로딩 UI 때문입니다. 
    네트워크 속도나 서버 상태에 따라 로딩 스피너가 도는 시간이 매번 달라지므로, 고정된 시간(time.sleep)을 기다려서는 안 됩니다.
    로딩 UI 요소가 화면에서 '완전히 사라질 때까지' 동적으로 대기(Invisibility of Element)하는 고급 동기화 기술이 필요합니다.

Q3. 해피 패스(Happy Path) 외에 추가로 고려해야 할 자동화 엣지 케이스(Edge Case)는 무엇이 있나요?
A3. 실제 프로젝트 환경에서는 다음과 같은 Negative 및 Edge 케이스를 추가로 자동화하여 시스템의 방어력을 검증합니다.
    - [TC-TOOL-002] 필수 값 누락 (Negative): 과목/단원 미입력 시 올바른 에러 팝업 및 진행 차단 여부
    - [TC-TOOL-003] 모달 취소 동작 (Edge): 키워드 선택 후 '저장' 대신 '취소' 시, 폼에 반영되지 않고 초기화 상태를 유지하는지 여부
    - [TC-TOOL-004] 중복 요청 방지 (Edge): 로딩 UI가 도는 동안 다른 버튼을 클릭하여 중복 생성을 요청하지 못하도록 화면이 딤(Dim) 처리되거나 제어가 막혀있는지 여부
================================================================================
"""



"""
세부 특기사항 기능에 대한 UI 시나리오 테스트 스크립트.
"""

import allure
from pages.special_notes_page import SpecialNotesPage

# 로거 설정
from utils.logger import get_custom_logger
logger = get_custom_logger(__name__)

@allure.feature("AI 도구")
@allure.story("세부 특기사항 생성")
class TestSpecialNotes:
    """세부 특기사항 자동 생성 기능 검증 테스트 스위트"""

    # 테스트용 더미 데이터를 상단 상수로 분리
    TEST_STUDENT_NAME = "테스트학생1"

    @allure.title("[TC-TOOL-001] AI 세부 특기사항 정상 생성 확인 테스트")
    def test_generate_special_notes_success(self, authenticated_driver):
        """
        [TC-TOOL-001] (Happy Path) 단일 학생에 대한 세부 특기사항 정상 생성
        
        [목적] 교사가 수업 정보와 학생의 특성을 입력했을 때, AI가 이를 바탕으로 적절한 텍스트를 정상 생성하는지 E2E 검증한다.
        
        [Test Steps]
        1. 좌측 네비게이션 메뉴에서 '도구'를 클릭한다.
        2. 도구 목록 본문에서 '세부 특기사항' 카드를 클릭한다.
        3. '수업 정보 입력' 단계에서 지정된 [학교급, 학년, 과목, 단원]을 입력/선택하고 '다음으로' 버튼을 클릭한다.
        4. 활성화된 '학생 정보 입력 및 생성' 단계에서 '학생 이름'을 입력한다.
        5. '활동 키워드' 입력칸을 클릭하여 모달창을 호출한다.
        6. 모달창 내 '학습 태도' 아코디언을 열고 '수업 집중도 높음' 칩(Chip)을 선택한 뒤 '저장'을 클릭한다.
        
        [Expected Result]
        - 생성 요청 직후 나타난 로딩 UI가 완전히 사라진 후, 선택한 키워드 문맥("집중", "태도" 등)이 포함된 AI 텍스트가 출력되어야 한다.
        """
        # 페이지 객체 초기화
        notes_page = SpecialNotesPage(authenticated_driver)
        
        # [Step 1, 2] 메뉴 이동
        logger.info("'도구 > 세부 특기사항' 메뉴로 이동합니다.")
        notes_page.navigate_to_tool()

        # 테스트 격리(Isolation)를 위한 기존 데이터 강제 초기화
        logger.info("테스트 환경의 무결성을 위해 기존 입력 내역을 초기화합니다.")
        notes_page.reset_input_history()
        
        # [Step 3] 수업 정보 폼 입력 및 진행
        logger.info("수업 정보(학교급: 초등학교, 학년: 1학년, 과목: 국어, 단원: 1)를 입력하고 다음으로 넘어갑니다.")
        notes_page.fill_class_info_and_next(school_level="초등학교", grade="1학년", subject="국어", unit="1")
        
        # [Step 4, 5, 6] 학생 정보 입력 및 키워드 모달 제어
        logger.info(f"학생 이름 '{self.TEST_STUDENT_NAME}' 입력 및 '수업 집중도 높음' 키워드를 선택합니다.")
        notes_page.fill_student_and_select_keyword(student_name=self.TEST_STUDENT_NAME)
        
        # 비동기 대기 (로딩 사라질 때까지 대기)
        logger.info("AI가 특기사항을 생성하는 동안 대기합니다 (최대 30초)...")
        generated_text = notes_page.wait_for_ai_generation()
        
        # 결과 로깅
        logger.info(f"🎉 최종 AI 생성 결과: {generated_text}")
        
        # [기대 결과 검증 - Assertion]
        # 1. 텍스트가 정상적으로 반환되었는지 (비어있지 않은지)
        assert generated_text is not None, "생성된 텍스트가 없습니다."
        assert len(generated_text) > 10, "생성된 텍스트가 비정상적으로 짧습니다."
        
        # 2. 핵심 키워드가 문맥에 제대로 반영되었는지 (선택한 칩에 따른 예상 단어 검증)
        assert "집중" in generated_text or "태도" in generated_text, f"기대하는 키워드가 포함되지 않았습니다. (생성된 문구: {generated_text})"
   
   # @allure.title("[TC-TOOL-002] ......")
   # def test_...

   # @allure.title("[TC-TOOL-003] ......")
   # def test_...

   # @allure.title("[TC-TOOL-004] ......")
   # def test_...