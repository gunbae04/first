"""
================================================================================
로그인 테스트 시나리오의 핵심 설계 포인트
================================================================================

Q1. 온보딩(약관 동의) 화면 처리에 왜 try-except(TimeoutException)를 사용했나요?
A1. E2E 테스트에서는 '사용자의 상태(초기 가입자 vs 기존 가입자)'에 따라 화면 흐름이 달라지는 경우가 많습니다.
    만약 무조건 약관 동의 버튼을 클릭하도록 하드코딩하면, 기존 계정으로 테스트할 때 버튼을 찾지 못해 에러(ElementNotFound 등)가 발생합니다.
    따라서 명시적 대기(Explicit Wait)를 사용해 요소가 나타나기를 기다리되, 지정된 시간 내에 나타나지 않으면(TimeoutException)
    "아, 이 계정은 이미 약관 동의를 완료한 기존 계정이구나"라고 판단하고 자연스럽게 다음 단계로 넘어가도록(pass) 처리하는 것입니다.
    이러한 '방어적 프로그래밍(Defensive Programming)' 기법은 자동화 스크립트의 안정성(Robustness)을 크게 높여줍니다.

Q2. 테스트 코드에 @pytest.mark.ui, api, smoke, regression 같은 마커(태그)를 분류해서 붙이는 이유는 무엇인가요?
A2. CI/CD 파이프라인에서 한정된 리소스와 시간을 효율적으로 쓰기 위해,
    '테스트 계층'과 '실행 목적'에 따라 원하는 테스트만 골라서 실행(Selective Execution)하기 위함입니다.

    [1. 실행 목적(전략)에 따른 분류]
    * Smoke Test (스모크 테스트):
      시스템의 가장 핵심적이고 치명적인 기능(P0)만 빠르게 점검합니다.
      로그인이 안 되면 다른 모든 기능(채팅, 설정 등)을 테스트할 수 없으므로, 정상 로그인 성공 케이스는 반드시 Smoke Test에 포함되어야 합니다.
      배포 직후에 5분 내로 빠르게 돌려볼 때 사용합니다.
    * Regression Test (회귀 테스트):
      예외 케이스(잘못된 비밀번호, 미가입 계정 등)를 포함하여 시스템의 엣지(Edge) 케이스를 검증합니다.
      전체 기능이 정상 작동하는지 확인하기 위해 주로 매일 새벽, 시간이 오래 걸리는 전체 파이프라인에서 실행되도록 분류합니다.

    [2. 테스트 계층(Layer)에 따른 분류]
    * UI Test:
      브라우저를 직접 띄우고 사용자의 실제 동작(클릭, 입력)을 모사하여 프론트엔드부터 백엔드까지 전체(E2E) 인프라를 검증합니다.
      실행 속도가 상대적으로 느리고 인프라 환경의 영향을 많이 받습니다.
    * API Test:
      화면(UI)을 거치지 않고 서버의 API 엔드포인트를 직접 호출하여 데이터의 정합성과 비즈니스 로직을 눈보다 빠르게(0.1초 단위) 검증합니다.
      향후 API 자동화가 추가될 때 UI 테스트와 분리하여 돌리기 위해 사용합니다.
================================================================================
"""



"""
로그인 기능에 대한 UI 시나리오 테스트 스크립트.
"""
import pytest
import allure
from selenium.common.exceptions import TimeoutException
from pages.login_page import LoginPage
from pages.signup_page import SignupPage

# 로거 설정
from utils.logger import get_custom_logger
logger = get_custom_logger(__name__)

@allure.feature("인증 기능")
@allure.story("로그인 및 온보딩")
class TestLogin:
    """로그인 프로세스 검증 테스트 스위트"""

    @pytest.mark.smoke  
    @pytest.mark.ui
    @allure.title("[TC-LOGIN-001] 로그인 및 온보딩 통합 성공 테스트")
    def test_login_and_onboarding_success(self, driver, base_url, test_user):
        """
        [TC-LOGIN-001] 로그인 및 온보딩 통합 성공 테스트
        
        1. 로그인 정보 입력 및 Login 클릭
        2. 최초 로그인인 경우 약관 동의 절차 수행 (예외 처리 포함)
        3. 최종적으로 메인 서비스 URL 진입 여부 검증
        """
        # 1. Page Object(객체) 초기화
        login_page = LoginPage(driver, base_url)
        signup_page = SignupPage(driver)
        
        # 2. 헬피챗 접속
        login_page.open()
        
        # 3. 로그인 정보 입력 및 실행 (공통 픽스처에서 주입받은 계정 사용)
        login_page.login(test_user["id"], test_user["pw"])
        
        # 4. 온보딩(약관 동의) 화면 처리 
        # - 최초 로그인인 경우 약관 동의 화면이 노출되므로 이를 처리함
        # - 이미 가입된 계정이라 약관 동의 화면이 나타나지 않으면 TimeoutException을 잡고 통과시킴
        try:
            signup_page.agree_and_submit()
            logger.info("최초 로그인: 온보딩 약관 동의를 완료했습니다.")
        except TimeoutException:
            logger.info("기존 계정: 약관 동의 화면을 건너뛰고 메인으로 진입합니다.")
        
        # 5. 최종 결과 검증
        # - 온보딩을 거쳤든 안 거쳤든, 최종적으로 메인 화면의 고유 URL 경로에 정상 진입하는지 확인
        is_success = login_page.is_login_successful()
        assert is_success is True, "로그인 완료 후 메인 페이지(/ai-helpy-chat) 진입에 실패했습니다."

    # @pytest.mark.regression 
    # def test_login_failure_cases(self, driver, base_url, invalid_user):
    #     # ... 테스트 코드 ...
    #     pass