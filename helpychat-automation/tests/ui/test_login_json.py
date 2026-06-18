"""
================================================================================
네거티브 테스트(Negative Test)와 JSON 데이터 연동의 핵심
================================================================================

Q1. data/users.json 파일에서 비정상 계정 데이터를 읽어와 테스트하는 이유는 무엇인가요?
A1. '데이터 주도 테스트(DDT)' 기법을 예외 케이스(Negative Case)에 적용한 것입니다.
    로그인 실패 케이스(형식 오류, 미가입, 비밀번호 틀림 등)는 무수히 많습니다. 이를 일일이 코드(함수)로 작성하면 중복이 심해집니다.
    따라서 파이썬 코드에는 '로그인 실패 확인'이라는 단 하나의 로직만 남겨두고, 다양한 에러 조건들은 JSON 파일에서 
    동적으로 주입받아 반복 실행(@pytest.mark.parametrize)하게 만들면 프레임워크의 유지보수성이 극대화됩니다.

Q2. 정상 동작을 확인하는 것(Positive Test) 외에, 실패를 확인하는 네거티브 테스트는 왜 중요한가요?
A2. 사용자가 항상 기획자가 의도한 대로만 시스템을 사용하지 않기 때문입니다.
    기능이 정상 작동하는지 확인하는 것(해피 패스)도 중요하지만, 잘못된 값이나 악의적인 접근이 발생했을 때 
    시스템이 뻗지 않고(Crash 방지) '안전하게 접근을 차단하는지' 검증하는 것은 시스템 보안과 안정성의 핵심입니다.

Q3. 온보딩(약관 동의) 화면 처리에 왜 try-except(TimeoutException)를 사용했나요?
A3. 테스트 계정의 상태(초기 가입자 vs 기존 가입자)에 따라 노출되는 화면이 다르기 때문입니다.
    무조건 약관 동의를 누르도록 코딩하면 기존 계정 테스트 시 에러가 발생합니다. 명시적 대기(Explicit Wait)를 사용해 
    요소가 나타나길 기다리고, 시간 내에 안 나타나면(TimeoutException) "아, 기존 계정이구나" 하고 유연하게 
    다음 단계로 넘어가게(pass) 만드는 '방어적 프로그래밍' 기법입니다.
================================================================================
"""



"""
로그인 기능에 대한 UI 시나리오 테스트 스크립트.
"""

import json
import pytest
import allure
from pathlib import Path
from selenium.common.exceptions import TimeoutException
from pages.login_page import LoginPage
from pages.signup_page import SignupPage

# 로거 설정
from utils.logger import get_custom_logger
logger = get_custom_logger(__name__)

def load_invalid_user_data():
    """data/users.json 파일에서 비정상 로그인 테스트용 데이터를 읽어옵니다."""
    # 상대 경로의 함정(FileNotFoundError)을 방지하기 위해 동적 절대 경로 적용
    # 현재 파일 위치(tests/ui/test_login_json.py)에서 3단계 위(프로젝트 루트)로 이동 후 data 폴더 접근
    base_dir = Path(__file__).resolve().parent.parent.parent
    json_file_path = base_dir / "data" / "users.json"

    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # invalid_users 하위의 계정 정보 리스트만 추출
        return list(data["invalid_users"].values())

@allure.feature("인증 기능")
@allure.story("로그인 및 온보딩")
class TestLogin:

    @pytest.mark.smoke  
    @pytest.mark.ui
    @allure.title("[TC-LOGIN-001] 로그인 및 온보딩 통합 성공 테스트")
    def test_login_and_onboarding_success(self, driver, base_url, test_user):
        """
        [TC-LOGIN-001] 정상 계정 로그인 및 최초 온보딩 완료 후 메인 페이지 진입을 검증합니다.
        """
        login_page = LoginPage(driver, base_url)
        signup_page = SignupPage(driver)
        
        login_page.open()
        login_page.login(test_user["id"], test_user["pw"])
        
        try:
            signup_page.agree_and_submit()
            logger.info("최초 로그인: 온보딩 약관 동의를 완료했습니다.")
        except TimeoutException:
            logger.info("기존 계정: 약관 동의 화면을 건너뛰고 메인으로 진입합니다.")
        
        is_success = login_page.is_login_successful()
        assert is_success is True, "로그인 완료 후 메인 페이지(/ai-helpy-chat) 진입에 실패했습니다."


    @pytest.mark.regression
    @allure.title("로그인 실패 예외 케이스 검증 (Negative Test)")
    # JSON의 예외 계정 목록을 주입받아 반복 검증합니다.
    @pytest.mark.parametrize("invalid_user", load_invalid_user_data())
    def test_login_failure_cases(self, driver, base_url, invalid_user):
        """
        [Negative Test] 잘못된 형식이나 가입되지 않은 계정 입력 시 비정상 진입이 완전히 차단되는지 검증합니다.
        """
        login_page = LoginPage(driver, base_url)
        
        login_page.open()
        # 비밀번호는 무의미하므로 더미 값 입력
        logger.info(f"예외 테스트 진행: 잘못된 계정 '{invalid_user['id']}'로 로그인을 시도합니다.")
        login_page.login(invalid_user["id"], "dummy_password123!")
        
        # 메인 페이지 진입 실패 여부 검증
        is_success = login_page.is_login_successful()
        assert is_success is False, f"결함 발견: 실패해야 하는 계정({invalid_user['id']})이 시스템에 로그인되었습니다."
        
        logger.info(f"검증 완료: 예상대로 시스템 진입이 안전하게 차단되었습니다.")