"""
================================================================================
Pytest Hook을 활용한 결함 트래킹 자동화 핵심 원리
================================================================================

Q1. 개별 테스트 코드 안에 try-except를 넣지 않고, 왜 Pytest Hook(pytest_runtest_makereport)을 사용하나요?
A1. '관심사의 분리'와 '전역 통제'를 위해서입니다.
    만약 100개의 테스트 스크립트마다 실패 시 스크린샷을 찍고 Jira에 올리는 코드를 중복해서 넣는다면 코드가 매우 지저분해집니다.
    Pytest Hook은 테스트의 생명주기(Lifecycle)를 뒤에서 조용히 가로채는(Intercept) 관제탑 역할을 합니다. 
    따라서 테스트 코드는 '순수한 검증'에만 집중하고, 실패 시의 후처리(스크린샷, 티켓팅)는 프레임워크 레벨에서 일괄적이고 우아하게 처리할 수 있습니다.

Q2. 에러 메시지를 추출할 때 복잡한 정규표현식(re.sub)을 사용하여 외계어 같은 코드를 지우는 이유는 무엇인가요?
A2. 콘솔에 출력되는 에러 로그에는 글자 색상을 입히기 위한 'ANSI 이스케이프 코드(색상 코드)'가 포함되어 있기 때문입니다.
    이 텍스트를 그대로 Jira로 전송하면, Jira는 색상 코드를 인식하지 못해 화면에 깨진 문자열(외계어)을 그대로 노출하게 됩니다. 
    따라서 정규표현식으로 순수한 텍스트만 깔끔하게 정제하여 전송하는 디테일이 필요합니다.

Q3. 에러 메시지 길이를 1,000자(MAX_LOG_LENGTH)로 제한한 이유는 무엇인가요?
A3. '방어적 프로그래밍(Defensive Programming)'의 일환입니다.
    웹 페이지 전체 소스코드나 거대한 API 응답 에러가 로그에 찍힐 경우, 그 길이가 수만 자를 넘어갈 수 있습니다. 
    이를 그대로 Jira API에 쏘게 되면, Payload 용량 초과로 서버가 요청을 거부(HTTP 400 Bad Request)하여 정작 중요한 버그 티켓이 생성되지 않는 대참사가 발생합니다. 
    따라서 핵심 에러만 잘라서 보내고, 전체 로그는 Allure 리포트 링크를 통해 확인하도록 유도하는 것이 매우 안정적인 설계입니다.
================================================================================
"""



"""
Jira 자동 티켓팅 및 Allure 리포트 후처리를 담당하는 Pytest Hook
"""
import os
import pytest
import allure
import re
from utils.jira_client import create_jira_bug_ticket, attach_image_to_jira
from config.config import BASE_UI_URL

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """테스트 실패 시 Allure 및 Jira에 스크린샷과 로그 전송."""
    outcome = yield
    rep = outcome.get_result()
    
    # 테스트 실행(call) 중 실패(failed)한 경우에만 동작
    if rep.when == "call" and rep.failed:
        # 1. WebDriver 객체 가져오기 (픽스처 이름 기준)
        driver = item.funcargs.get("driver") or item.funcargs.get("authenticated_driver") or item.funcargs.get("logged_in_driver")
        
        if driver:
            # 2. 스크린샷 캡처
            screenshot_bytes = driver.get_screenshot_as_png()
            
            # 3. Allure 리포트에 스크린샷 첨부
            allure.attach(screenshot_bytes, name="Failure_Screenshot", attachment_type=allure.attachment_type.PNG)
            
            # 4. 에러 메시지 정제 (ANSI 색상 코드 제거)
            test_name = item.name
            raw_error = str(call.excinfo.value) if call.excinfo else "알 수 없는 에러"
            clean_error_message = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', raw_error)
            
            # 5. 에러 메시지가 너무 길 경우 1,000자로 제한하여 API 거절 방지
            MAX_LOG_LENGTH = 1000
            if len(clean_error_message) > MAX_LOG_LENGTH:
                clean_error_message = clean_error_message[:MAX_LOG_LENGTH] + "\n\n... (에러 로그가 너무 길어 생략되었습니다. 전체 로그는 하단의 Allure 리포트 링크를 확인해 주세요.)"
            
            # 6. CI/CD 서버 환경 변수에서 Allure 리포트 URL 가져오기 (없을 경우 로컬 텍스트 출력)
            report_url = os.getenv("ALLURE_REPORT_URL", "로컬 실행 (URL 없음)")
            
            # 7. Jira 티켓 데이터(제목, 내용) 구성
            summary = f"[자동화 버그] {test_name} 테스트 실패"
            description = (
                f"UI 자동화 테스트 실행 중 결함이 발견되었습니다.\n\n"
                f"* 🌐 실행 환경:* Chrome / Base URL: {item.funcargs.get('base_url', BASE_UI_URL)}\n"
                f"* 📝 테스트 케이스:* {test_name}\n\n"
                f"*🚨 발생한 에러 메시지:*\n"
                f"{{code:python}}\n{clean_error_message}\n{{code}}\n\n" # Jira 코드블록 적용
                f"📊 *Allure 전체 로그 및 리포트 확인:* [{report_url}|{report_url}]\n\n"
                f"자세한 화면 캡처는 본 티켓의 *첨부파일*을 확인해 주세요."
            )
            
            # 8. Jira API 호출 (Jira 티켓 먼저 생성)
            issue_key = create_jira_bug_ticket(summary, description)
            
            # 9. 티켓 생성이 성공했다면, Jira API 호출 및 스크린샷 첨부
            if issue_key:
                attach_image_to_jira(issue_key, screenshot_bytes)