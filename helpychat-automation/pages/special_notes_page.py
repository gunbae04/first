"""
================================================================================
복잡한 프론트엔드 UI(MUI, 인라인 에디터) 제어 및 동기화 기법
================================================================================

Q1. 드롭다운을 선택할 때 Selenium의 기본 `Select()` 클래스를 쓰지 않고 커스텀 헬퍼 함수(`select_mui_dropdown`)를 만든 이유는 무엇인가요?
A1. 최신 프론트엔드 프레임워크(MUI, React 등)는 디자인 커스텀을 위해 표준 `<select>` HTML 태그 대신 `<div>`와 `<ul>/<li>` 태그를 조합해 가짜(Custom) 드롭다운을 렌더링하기 때문입니다.
    표준 태그가 아니므로 Selenium의 내장 `Select()` 기능을 사용할 수 없습니다. 따라서 '1. 콤보박스 클릭해서 열기 -> 2. 텍스트와 매칭되는 리스트 요소 클릭 -> 3. 드롭다운 메뉴 사라짐 대기'라는 
    3단계 액션을 하나의 헬퍼 함수로 묶어(Wrapping) 코드의 중복을 막고 재사용성을 높인 것입니다.

Q2. 학생 이름을 입력할 때, 바로 `<textarea>`에 `enter_text`를 하지 않고 `<p>` 태그(STUDENT_NAME_DISPLAY)를 먼저 클릭하는 이유는 무엇인가요?
A2. 이 화면이 '인라인 에디터(Click-to-Edit)' UI 패턴을 사용하기 때문입니다.
    평소에는 `<textarea>`가 숨겨져(hidden) 있거나 DOM 트리에 아예 존재하지 않다가, 화면의 특정 텍스트 영역(`<p>`)을 클릭해야만 실제 입력창이 활성화됩니다.
    만약 비활성화 상태에서 무작정 텍스트를 입력(send_keys)하려 하면 `ElementNotInteractableException` 에러가 발생합니다. 
    따라서 사용자의 실제 마우스 행동 패턴과 완벽하게 동일하게 '표시 영역 클릭 -> 입력창 활성화 대기 및 타이핑 -> 저장 버튼 클릭' 순서로 구현해야 합니다.

Q3. `reset_input_history` 함수를 만들어 테스트가 시작될 때마다 화면 초기화를 수행하는 이유는 무엇인가요?
A3. 자동화 테스트의 제1원칙인 '테스트 격리(Test Isolation)'를 프론트엔드(UI) 레벨에서 보장하기 위함입니다.
    이전 테스트가 중간에 실패하여 화면에 쓰레기 데이터(Residual Data)가 남아있을 경우, 다음번 테스트가 이 데이터 때문에 엉뚱한 곳에서 연쇄적으로 실패(Cascading Failure)할 위험이 큽니다.
    API를 통해 DB를 초기화하는 것이 가장 좋지만, 여의치 않다면 이렇게 UI 상의 초기화 버튼을 눌러 항상 '백지상태(Clean State)'를 강제로 만든 후 메인 시나리오를 시작하는 것이 견고한 프레임워크의 비결입니다.
================================================================================
"""



"""
세부 특기사항 도구 페이지의 UI 요소와 액션을 정의한 POM 클래스.
"""

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
from .base_page import BasePage

class SpecialNotesPage(BasePage):
    # =======================================================================
    # 1. 네비게이션 및 메뉴 진입
    # =======================================================================
    MENU_TOOLS = (By.CSS_SELECTOR, "a[href*='/tools']")
    TOOL_SPECIAL_NOTES = (By.XPATH, "//p[text()='세부 특기사항']")

    RESET_BUTTON = (By.XPATH, "//button[contains(., '입력 내역 초기화')]")
    RESET_CONFIRM_BUTTON = (By.XPATH, "//div[@role='dialog']//button[text()='초기화 하기']")

    # =======================================================================
    # 2. 수업 정보 입력 폼
    # =======================================================================
    # 학교급 (Dropdown)
    SCHOOL_LEVEL_DROPDOWN = (By.XPATH, "//div[input[@name='school_level']]//*[@role='combobox']")
    # 학년 (Dropdown)
    GRADE_DROPDOWN = (By.XPATH, "//div[input[@name='grade']]//*[@role='combobox']")
    # 과목 (Input)
    SUBJECT_INPUT = (By.CSS_SELECTOR, "div[name='subject'] input")
    # 단원 (Input)
    UNIT_INPUT = (By.CSS_SELECTOR, "input[name='unit']")
    # 다음으로 (Button)
    NEXT_BUTTON = (By.CSS_SELECTOR, "button[type='submit'][form='student_evaluation']")

    # =======================================================================
    # 3. 학생 정보 입력 및 키워드 모달
    # =======================================================================
    # 인라인 에디터 패턴 (Click-to-Edit) 로케이터
    # (1) 평상시 보여지는 <p> 태그 (텍스트 에리어가 숨겨진 바로 그 테이블 셀(td) 안의 p 태그를 찾음)
    STUDENT_NAME_DISPLAY = (By.CSS_SELECTOR, "td:has(textarea[placeholder='이름을 입력해주세요.']) p[role='button']")
    # (2) 클릭 후 나타나는 실제 입력창
    STUDENT_NAME_TEXTAREA = (By.CSS_SELECTOR, "textarea[placeholder='이름을 입력해주세요.']")
    # (3) 이름 입력 후 누르는 전용 '저장' 버튼 (모달창의 저장 버튼과 겹치지 않도록 해당 td 내부로 범위를 제한)
    STUDENT_NAME_SAVE_BTN = (By.XPATH, "//td[.//textarea[@placeholder='이름을 입력해주세요.']]//*[text()='저장']")

    KEYWORD_PLACEHOLDER = (By.XPATH, "//span[contains(text(), '키워드를 선택해주세요.')]")
    
    ACCORDION_ATTITUDE = (By.XPATH, "//p[text()='학습 태도']")
    CHIP_HIGH_FOCUS = (By.XPATH, "//span[text()='수업 집중도 높음']")
    MODAL_SAVE_BUTTON = (By.XPATH, "//button[text()='저장']") # //button[normalize-space()='저장']   # //div[@role='dialog']//button[contains(., '저장')]

    # =======================================================================
    # 4. AI 생성 로딩 및 결과 검증
    # =======================================================================
    # 로딩 중일 때 나타나는 텍스트 요소
    LOADING_SPINNER = (By.XPATH, "//td[last()]//span[@role='progressbar']")
    # 생성이 완료된 후 나타나는 결과 텍스트 영역
    RESULT_TEXT_AREA = (By.XPATH, "//td[last()]//p[@role='button']")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    @allure.step("도구 > 세부 특기사항 메뉴 이동")
    def navigate_to_tool(self):
        self.click(self.MENU_TOOLS)
        self.click(self.TOOL_SPECIAL_NOTES)

    # 초기화 전용 헬퍼 함수
    @allure.step("이전 데이터 초기화(Reset)")
    def reset_input_history(self):
        """
        기존에 작성된 데이터가 남아있어 테스트가 꼬이는 것을 방지하기 위해 폼을 초기화합니다.
        여기서는 기존 데이터가 삭제되므로 주의가 필요합니다.
        """
        try:
            # 1. 우측 상단의 '입력 내역 초기화' 텍스트 버튼 클릭 시도
            self.click(self.RESET_BUTTON)
            
            # 2. MUI 모달창이 뜨면 '초기화 하기' 빨간색 버튼 클릭
            self.click(self.RESET_CONFIRM_BUTTON)
            
            # 3. 모달창이 닫히고 UI가 안정화될 시간 대기
            self.wait_until_invisible((By.XPATH, "//div[@role='dialog']"))
        except TimeoutException:
            # 버튼이 없거나 클릭할 수 없는 상태라면 (이미 폼이 비어있음) 무시하고 넘어감
            pass

    # MUI 드롭다운 제어를 위한 전용 헬퍼 함수 추가
    @allure.step("MUI 드롭다운 선택: '{option_text}'")
    def select_mui_dropdown(self, dropdown_locator: tuple, option_text: str):
        """MUI Select 박스를 클릭하여 열고, 주어진 텍스트와 일치하는 옵션을 클릭합니다."""
        # 1. 콤보박스 클릭해서 메뉴 펼치기
        self.click(dropdown_locator)
        # 2. 펼쳐진 메뉴 안에서 원하는 텍스트를 가진 요소 찾아서 클릭하기
        option_locator = (By.CSS_SELECTOR, f"li[data-value='{option_text}']")
        self.click(option_locator)
        # 드롭다운 메뉴가 화면에서 완전히 사라질 때까지 대기
        self.wait_until_invisible((By.CSS_SELECTOR, "ul[role='listbox']"))

    @allure.step("수업 정보 입력 및 다음 이동")
    def fill_class_info_and_next(self, school_level: str, grade: str, subject: str, unit: str):
        """수업 정보를 순차적으로 입력하고 다음 단계로 이동합니다."""
        # 1. 학교급 선택
        self.select_mui_dropdown(self.SCHOOL_LEVEL_DROPDOWN, school_level)
        # 2. 학년 선택
        self.select_mui_dropdown(self.GRADE_DROPDOWN, grade)
        # 3. 과목 선택
        self.enter_text(self.SUBJECT_INPUT, subject)
        # 4. 단원 입력
        self.enter_text(self.UNIT_INPUT, unit)
        # 5. 다음으로 이동
        self.click(self.NEXT_BUTTON)

    @allure.step("학생 정보 및 키워드 모달 입력")
    def fill_student_and_select_keyword(self, student_name: str):
        """학생 이름을 입력하고 키워드 모달을 열어 키워드를 선택합니다."""
        # 1. 인라인 에디터 활성화 (p 태그 클릭)
        self.click(self.STUDENT_NAME_DISPLAY)
        
        # 2. textarea에 텍스트 입력
        # (BasePage의 enter_text가 내부적으로 내용을 지우고 쓰기 때문에 초기값 '1**'이 깔끔하게 지워집니다)
        self.enter_text(self.STUDENT_NAME_TEXTAREA, student_name)
        
        # 3. 이름 저장 버튼 클릭 (에디터 닫기)
        self.click(self.STUDENT_NAME_SAVE_BTN)
        
        # 4. 키워드 모달 제어
        self.click(self.KEYWORD_PLACEHOLDER)
        self.click(self.ACCORDION_ATTITUDE)
        self.click(self.CHIP_HIGH_FOCUS)
        self.click(self.MODAL_SAVE_BUTTON)

    @allure.step("AI 텍스트 생성 비동기 대기")
    def wait_for_ai_generation(self) -> str:
        """AI 생성이 완료될 때까지 대기하고 생성된 텍스트를 반환합니다."""
        # 1단계: 스피너가 나타날 때까지 대기 (기본 10초 적용)
        # (네트워크가 너무 빠르거나, 이미 스피너가 돌기 시작한 경우를 대비해 짧은 예외 처리)
        try:
            self.wait_for_visible(self.LOADING_SPINNER)
        except TimeoutException:
            pass 
        
        # 2단계: 스피너가 화면에서 '완전히 사라질 때까지' 대기 (최대 30초)
        # 텍스트가 무엇이든 상관없이 빙글빙글 도는 UI가 끝나는 시점을 정확히 캐치합니다.
        self.wait_until_invisible(self.LOADING_SPINNER, timeout=30)

        # 3단계: 결과 텍스트 읽어오기(기본 10초 적용)
        return self.get_text(self.RESULT_TEXT_AREA)