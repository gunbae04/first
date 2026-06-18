"""
================================================================================
conftest.py 핵심 아키텍처 및 Pytest 생명주기(Lifecycle) 제어
================================================================================

Q1. conftest.py는 무슨 파일이며, 왜 여기에 로그인이나 브라우저 셋업 코드를 모아두나요?
A1. conftest.py는 Pytest 프레임워크에서 환경 설정과 픽스처(Fixture)를 전역적으로 공유하는 중심 관제탑입니다.
    만약 100개의 테스트 파일마다 브라우저를 띄우고 로그인하는 코드를 중복해서 넣는다면 유지보수가 불가능해집니다.
    이를 conftest.py에 모아두고 필요한 테스트에만 주입(Injection)받아 사용하게 하면(DRY 원칙),
    실제 테스트 코드(test_*.py)에는 순수하게 '검증 로직'만 남길 수 있어 가독성과 관리 효율이 극대화됩니다.

Q2. 테스트가 실패했을 때 Jira 티켓이 자동 생성되고, 종료 시 Slack 알림이 가는 원리가 무엇인가요?
A2. Pytest의 강력한 '훅(Hook)' 기능 덕분입니다.
    pytest_runtest_makereport나 pytest_sessionfinish 같은 훅 함수들은 테스트가 실행되고 종료되는 
    생명주기(Lifecycle)의 특정 시점을 가로채서(Intercept) 우리가 원하는 동작을 끼워 넣을 수 있게 해줍니다.
    이를 통해 개별 테스트 스크립트에 "실패하면 스크린샷 찍어"라는 코드를 일일이 넣지 않아도, 
    프레임워크 레벨에서 에러를 감지하고 3rd-party 툴(Jira, Slack)과 완벽하게 연동되는 무인 파이프라인을 구축할 수 있습니다.

Q3. 주석 처리된 'API 쿠키 인젝션 기반 빠른 로그인'은 언제 사용하는 건가요?
A3. E2E 테스트의 가장 큰 단점인 '느린 실행 속도'와 'UI 불안정성(Flakiness)'을 극복하기 위한 최적화 기법입니다.
    UI로 직접 아이디/비밀번호를 치고 로그인하는 과정은 브라우저 렌더링을 기다려야 하므로 수 초가 걸리지만, 
    API로 토큰을 받아 브라우저 쿠키에 직접 찔러 넣으면(Inject) 0.1초 만에 로그인 상태를 만들 수 있습니다. 
    핵심 UI 테스트(로그인 폼 자체 검증)를 제외한 나머지 모든 기능 테스트(채팅, 특기사항 등)는 이 방식을 사용하여 
    전체 CI/CD 파이프라인 실행 시간을 획기적으로 단축시킬 수 있습니다.
================================================================================
"""



"""
프로젝트 전역에서 사용되는 Pytest Fixture 설정 파일.
WebDriver 초기화 및 Allure 후처리 담당.
"""

import os
import pytest
import requests
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

from config.config import BASE_UI_URL, BASE_API_URL, TEST_USER, DEFAULT_API_TIMEOUT
from pages.login_page import LoginPage
from pages.signup_page import SignupPage

# 로거 설정
from utils.logger import get_custom_logger
logger = get_custom_logger(__name__)

# Hook 파일들을 Pytest에 등록 (확장자 .py 생략, 점(.)으로 경로 표기)
pytest_plugins = [
    "tests.plugins.hook_jira",
    "tests.plugins.hook_slack"
]

####### [참고] WebDriver 매니저 관련 설명
# webdriver_manager 사용 여부는 프로젝트 상황에 따라 다릅니다.
# Selenium 4.6+ 부터는 Selenium Manager가 내장되어서 chromedriver를 자동 관리하지만, 명시적으로 webdriver_manager를 사용할 수도 있습니다.
# 과거에 ChromeDriver를 직접 설치/버전관리해야 했을 때 많이 사용했습니다.
# 최근에는 보통 제거하는 추세입니다만 아직 아래 경우에는 webdriver_manager를 쓰기도 합니다.
#  - 회사 내부망이라 Selenium Manager 다운로드 차단
#  - 특정 ChromeDriver 버전 고정 필요
#  - CI/CD 환경에서 드라이버 버전 통제 필요
#  - 오래된 Selenium 버전 유지 프로젝트
# from webdriver_manager.chrome import ChromeDriverManager # pip install webdriver-manager 필요
####### 그래서 요즘은 대부분 아래처럼만 씁니다.
# from selenium import webdriver

# =========================================================
# [1] UI 자동화 관련 Fixture: WebDriver
# =========================================================
@pytest.fixture(scope="function")
def driver():
    """
    각 테스트 함수마다 Selenium WebDriver를 초기화하고 브라우저 세션을 시작함.
    테스트 종료 후 브라우저를 닫음(Teardown).
    """
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080") # CI 환경에서는 window-size로 고정해야 함
    # options.add_argument("--headless")  # CI/CD 환경용 - Jenkins 등 서버 (GUI 없이) 실행 시 활성화

    ####### [참고] WebDriver 매니저 관련 설명
    # WebDriver 매니저를 통해 드라이버 자동 설치 및 실행
    # from selenium.webdriver.chrome.service import Service
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # driver.implicitly_wait(10)
    ####### 그래서 요즘은 대부분 아래처럼만 씁니다.
    driver = webdriver.Chrome(options=options)

    yield driver
    # 테스트가 끝나면 브라우저를 닫기 (Teardown)
    # 예외가 발생해도 무시하고 넘어가도록 처리하여, 드라이버가 남아있는 경우에도 시스템 리소스 누수 방지
    # (참고) CI/CD 환경에서는 브라우저가 남아있는 경우, Jenkins 관리자가 주기적으로 프로세스를 정리하는 스크립트 실행
    try:
        driver.quit()
    except Exception as e:
        logger.warning(f"WebDriver 종료 중 예외 발생: {e}")

# =========================================================
# [2] 공통 환경 설정 Fixture
# =========================================================
@pytest.fixture
def base_url():
    return BASE_UI_URL

@pytest.fixture
def api_base_url():
    return BASE_API_URL

@pytest.fixture
def test_user():
    return TEST_USER

# # =========================================================
# # [3-1] 사전 조건(Pre-condition) 특화 Fixture
# # UI 로그인 -> 매번 로그인
# # =========================================================
# @pytest.fixture(scope="function")
# def authenticated_driver(driver, base_url, test_user):
#     """UI 로그인이 완료된 상태의 WebDriver 제공."""
#     login_page = LoginPage(driver, base_url)
#     signup_page = SignupPage(driver)
    
#     # 1. 헬피챗 접속 및 로그인
#     login_page.open()
#     login_page.login(test_user["id"], test_user["pw"])
    
#     # 2. 온보딩 예외 처리
#     try:
#         signup_page.agree_and_submit()
#     except TimeoutException:
#         pass
        
#     # 3. 로그인 성공 검증 (실패 시 여기서 테스트 중단)
#     assert login_page.is_login_successful() is True, "Fixture 사전 조건 설정 실패: 로그인 불가"
#     return driver # 로그인이 완료된 브라우저 객체를 반환


import json
import time

# =========================================================
# [3-2] 파일 기반 세션 캐싱 및 쿠키 인젝션 픽스처
# UI 로그인 -> 쿠키 인젝션 기반 빠른 로그인
# =========================================================
@pytest.fixture(scope="function")
def authenticated_driver(driver, base_url, test_user):
    """
    [최적화] 세션 파일을 읽어와 쿠키를 인젝션하여 로그인을 우회합니다.
    파일이 없거나 만료(30분)된 경우에만 UI 로그인을 수행하고 새 쿠키를 추출해 파일로 저장합니다.
    """
    # 안전한 절대 경로 생성 (현재 파일 위치 기준으로 최상단 .pytest_cache 접근)
    project_root = Path(__file__).resolve().parent.parent
    cache_dir = project_root / ".pytest_cache"
    session_file = cache_dir / "elice_session.json"
    
    SESSION_VALID_DURATION = 1800  # 세션 유효 기간: 30분 (초 단위)
    valid_cookie = None

    # ---------------------------------------------------------
    # 1단계: 세션 파일 존재 여부 및 만료 시간(TTL) 검사
    # ---------------------------------------------------------
    if session_file.exists():
        with open(session_file, "r") as f:
            try:
                session_data = json.load(f)
                # 현재 시간 - 저장된 시간 < 30분 인지 확인
                if time.time() - session_data.get("timestamp", 0) < SESSION_VALID_DURATION:
                    valid_cookie = session_data.get("cookie_value")
                    logger.info("✅ 유효한 세션 캐시 발견! UI 로그인을 생략하고 인젝션을 시도합니다.")
                else:
                    logger.info("⏱️ 세션 캐시가 만료되었습니다(30분 경과). 새로 UI 로그인을 수행합니다.")
            except json.JSONDecodeError:
                logger.warning("⚠️ 세션 파일이 손상되었습니다. 새로 UI 로그인을 수행합니다.")

    # ---------------------------------------------------------
    # 2단계-A: 캐시가 유효하다면 -> 쿠키 인젝션으로 0.1초 쾌속 로그인
    # ---------------------------------------------------------
    if valid_cookie:
        # 쿠키를 심으려면 먼저 해당 도메인에 1회 접근해야 함
        driver.get(base_url) 
        
        driver.add_cookie({
            "name": "eliceSessionKey",
            "value": valid_cookie,
            "domain": ".elice.io" # 실제 쿠키의 도메인(개발자 도구 Application 탭 확인)
        })
        
        # 쿠키 주입 후 우리가 원하는 메인 서비스 URL로 이동
        driver.get(f"{base_url}/ai-helpy-chat")
        
        # (선택) 온보딩 화면이 뜨는지 가볍게 체크 후 패스
        try:
            SignupPage(driver).agree_and_submit()
        except TimeoutException:
            pass

    # ---------------------------------------------------------
    # 2단계-B: 캐시가 없거나 만료되었다면 -> 정석 UI 로그인 후 쿠키 추출/저장
    # ---------------------------------------------------------
    else:
        logger.info("▶️ 실제 브라우저를 띄워 UI 로그인을 진행합니다...")
        login_page = LoginPage(driver, base_url)
        login_page.open()
        login_page.login(test_user["id"], test_user["pw"])
        
        try:
            SignupPage(driver).agree_and_submit()
        except TimeoutException:
            pass
            
        assert login_page.is_login_successful() is True, "UI 로그인에 실패했습니다."
        
        # [핵심] 로그인 성공 직후 브라우저에서 쿠키를 가져와서 저장
        cookies = driver.get_cookies()
        elice_cookie = next((c["value"] for c in cookies if c["name"] == "eliceSessionKey"), None)
        
        if elice_cookie:
            # 폴더가 없으면 생성 (Pathlib 활용)
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # JSON 형태로 쿠키 값과 생성 시간(timestamp)을 저장
            with open(session_file, "w") as f:
                json.dump({
                    "cookie_value": elice_cookie,
                    "timestamp": time.time()
                }, f)
            logger.info("💾 새 세션 쿠키를 파일에 성공적으로 캐싱했습니다. 다음 테스트부터 속도가 빨라집니다.")

    return driver


# # =========================================================
# # [3-3] 사전 조건(Pre-condition) 특화 Fixture
# # API 로그인 -> 쿠키 인젝션 기반 빠른 로그인
# # =========================================================
# @pytest.fixture(scope="function")
# def authenticated_driver(driver, base_url, auth_token):
#     """
#     [사전 조건: API 쿠키 인젝션 기반 빠른 로그인]
#     UI 로딩을 기다리지 않고, API로 발급받은 세션 토큰을 브라우저 쿠키에 직접 주입하여
#     빠르게(ex:0.1초) 로그인된 상태로 만듬.
#     """
#     # 1. 쿠키를 세팅하기 위해 해당 도메인에 먼저 1회 접근
#     # 로그인 화면으로 리다이렉트 되더라도 일단 접속.
#     driver.get(base_url)
    
#     # 2. 브라우저 쿠키에 API로 받아온 토큰(auth_token)을 직접 주입함.
#     driver.add_cookie({
#         "name": "eliceSessionKey",
#         "value": auth_token,
#         "domain": ".elice.io" # 쿠키 탭에 명시된 도메인
#     })
    
#     # 3. 쿠키 주입 후, 우리가 진짜로 테스트할 메인 채팅 화면으로 이동.
#     # 브라우저는 방금 넣은 쿠키를 서버로 보내므로, 서버는 "아, 로그인된 유저구나!" 하고 통과시킴.
#     driver.get(f"{base_url}/ai-helpy-chat")
    
#     # 4. 최초 로그인 계정일 경우 노출되는 온보딩(약관 동의) 처리
#     from pages.signup_page import SignupPage
#     from selenium.common.exceptions import TimeoutException

#     try:
#         SignupPage(driver).agree_and_submit()
#     except TimeoutException:
#         pass # 이미 약관 동의를 한 기존 계정은 스킵

#     # 5. 로그인 성공 여부 최종 검증 로직 추가 (URL 기반 확인)
#     from selenium.webdriver.support.ui import WebDriverWait
#     from selenium.webdriver.support import expected_conditions as EC

#     WebDriverWait(driver, 10).until(EC.url_contains("ai-helpy-chat"))

#     return driver

# # API 자동화 관련 Fixture: 인증 토큰 및 세션
# @pytest.fixture(scope="session")
# def auth_token():
#     """테스트 세션 시작 시 단 한 번 로그인하여 API 인증용 Bearer 토큰 획득."""
#     login_url = f"{BASE_API_URL}/login"  # 실제 API 명세의 로그인 엔드포인트 확인 필요 (가정)
#     payload = {
#         "username": TEST_USER["id"],
#         "password": TEST_USER["pw"]
#     }
#     response = requests.post(
#         login_url,
#         json=payload,
#         timeout=DEFAULT_API_TIMEOUT
#     )
#     if response.status_code == 200:
#         return response.json().get("access_token")
#     else:
#         # 로그인 실패 시 테스트 중단을 위해 예외 발생
#         # (만약 로그인 API가 아직 미구현이라면 수동으로 토큰을 입력하도록 유도 가능)
#         pytest.fail(f"로그인 실패! 상태 코드: {response.status_code}")

# @pytest.fixture(scope="function")
# def api_session(auth_token):
#     """인증 헤더가 포함된 requests.Session 객체 제공."""
#     session = requests.Session()
#     session.headers.update({
#         "Authorization": f"Bearer {auth_token}",
#         "Content-Type": "application/json",
#         "x-elice-org-name-short": "elice"  # 명세서에 포함된 필수 헤더 예시
#     })
#     yield session
#     session.close()