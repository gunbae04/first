"""
================================================================================
계정 관리 테스트 시나리오 및 E2E 아키텍처 핵심 설계 포인트
================================================================================

Q1. TC-ACC-001 실행 시 로그인을 한 김에, 창을 닫지 않고 TC-ACC-002, TC-ACC-003까지 쭉 이어서 테스트하면 훨씬 빠르지 않을까요?
A1. 속도 면에서는 빠를 수 있지만, 자동화에서는 '테스트 독립성(Test Independence)' 원칙을 지켜야 합니다.
    이를 위해 매 테스트마다 브라우저 세션과 데이터를 완전히 분리하는 '테스트 격리(Test Isolation)' 환경을 구성합니다.
    만약 1개의 시나리오로 묶어서 실행하다가 1번 과정에서 예기치 못한 에러가 발생한다면,
    뒤에 있는 2번, 3번 테스트 코드나 기능에 문제가 없는데도 불구하고 앞선 에러 때문에 '연쇄 실패(Cascading Failure)'를 겪게 됩니다.
    이렇게 되면 나중에 리포트를 볼 때, 진짜로 결함이 있는 곳이 어디인지 원인(Root Cause)을 추적하기가 매우 힘들어집니다.
    따라서 모든 테스트 케이스는 항상 '초기화된 깨끗한 환경'에서 독립적으로 시작(setUp)하고 종료(tearDown)되어야 합니다.

Q2. 그럼 앞선 테스트의 결과물(예: 게시글 작성)이 있어야만 다음 테스트(예: 게시글 수정/삭제)를 진행할 수 있는 상황은 어떻게 하나요?
A2. 앞선 UI 테스트의 결과물에 의존하는 것은 '데이터 종속성(Data Dependency)' 문제를 발생시켜 병렬 테스트를 불가능하게 만듭니다.
    현업에서는 이를 해결하기 위해 백엔드 API나 DB를 적극 활용합니다. 
    테스트 시작 전(setUp)에 API를 호출하여 필요한 사전 데이터(테스트용 게시글 등)를 빠르게(ex: 0.1초) 셋업해 두고, 
    그 데이터 위에서 UI 테스트(수정/삭제 등)를 독립적으로 수행하는 방식(API Injection)이 가장 강력하고 권장되는 아키텍처입니다.

Q3. 지금 작성한 TC-ACC-001, 002, 003은 단위(Unit) 테스트인가요, 통합(Integration) 테스트인가요?
A3. 이 코드는 단위 테스트도, 통합 테스트도 아닙니다. 정확한 명칭은 'E2E(End-to-End) UI 기능 테스트(Functional Test)'입니다.
    개발자가 작성하는 단위 테스트는 특정 함수(로직) 하나만을 고립시켜 검증하며, 통합 테스트는 주로 프론트엔드 UI 없이 서버(API)와 DB의 연결을 검증합니다.
    반면 우리가 작성한 E2E UI 기능 테스트는 브라우저를 직접 띄우고 사용자의 행동을 그대로 따라가며,
    프론트엔드 -> 백엔드 -> DB까지 모든 인프라가 정상적으로 연동되어 요구사항(기능)을 충족하는지 종합적으로 검증합니다.
================================================================================
"""



"""
계정 관리 기능에 대한 UI 시나리오 테스트 스크립트.
"""

import allure
from pages.account_page import AccountPage
# 슬랙 설정
from utils.slack_notifier import send_slack_message
# 로거 설정
from utils.logger import get_custom_logger
logger = get_custom_logger(__name__)

@allure.feature("계정 관리")
@allure.story("비밀번호 변경")
class TestAccount:
    
    # 1회성 더미 데이터(Boundary Values)를 클래스 상수로 분리하여 가독성 향상
    TEMP_VALID_PW = "TemporaryPw123!"       # 임시로 변경할 8자리 이상, 특수문자 포함 비밀번호

    WRONG_CURRENT_PW = "wrong_password123!" # 틀린 현재 비밀번호
    VALID_NEW_PW = "NewValidPw123!@"        # 규칙에 맞는 새 비밀번호

    INVALID_FORMAT_PW = "short1!"           # 규칙 위반 (8자리 미만)

    @allure.title("[TC-ACC-001] 비밀번호 정상 변경 및 원상복구 테스트")
    def test_change_password_and_restore(self, authenticated_driver, test_user):
        """
        [시나리오]
        1. 우측 상단 프로필 > 계정 관리 진입
        2. 비밀번호 변경(연필) 클릭 후 새로운 비밀번호로 변경
        3. (Teardown) 다음 테스트를 위해 다시 원래 비밀번호로 원상복구
        """
        account_page = AccountPage(authenticated_driver)
        
        original_pw = test_user["pw"]

        try:
            # Step 1: 계정 관리 페이지 이동 (새 탭 전환 포함)
            logger.info("계정 관리 페이지로 이동합니다.")
            account_page.go_to_account_settings()

            # Step 2: 비밀번호 변경 실행
            logger.info(f"비밀번호 변경 시도합니다.") # 비밀번호 로깅 금지
            account_page.change_password(current_pw=original_pw, new_pw=self.TEMP_VALID_PW)
            
            # Step 3: 비밀번호 변경 후 성공 텍스트가 뜨는지 확인
            success_text = account_page.get_success_message()
            logger.info(f"알림창 확인: {success_text}")
            
            # 텍스트에 "저장되었습니다"가 포함되어 있는지 검증 (다국어나 띄어쓰기 등 미세한 차이 방지)
            assert "저장되었습니다" in success_text, f"비밀번호 변경 실패 알림: 예상과 다름 ({success_text})"
            
        finally:
            # 🧹 Step 3: 원상복구 (Rollback) - 테스트가 실패하더라도 무조건 실행됨
            logger.info("다음 테스트를 위해 비밀번호를 원상복구(Rollback) 합니다.")
            try:
                # 지금은 비밀번호가 TEMP_VALID_PW로 바뀐 상태이므로, 이를 입력하여 original_pw로 되돌립니다.
                account_page.change_password(current_pw=self.TEMP_VALID_PW, new_pw=original_pw)
            except Exception as e:
                # critical 로그로 기록하고, 슬랙으로 관리자에게 즉각적인 긴급 알림 전송 (예외 발생시키지 않고 Swallow(삼킴) 처리)
                logger.critical(f"치명적 문제: 테스트 계정 비밀번호 원상복구 실패! 계정이 오염되었습니다. (상세: {e})")
                slack_alert = (
                    f"🚨 *[긴급: 테스트 계정 오염 발생]* 🚨\n"
                    f"• *테스트명:* `TC-ACC-001` (비밀번호 변경)\n"
                    f"• *내용:* 테스트 후 원래 비밀번호로 복구(Rollback)하는 과정에서 에러가 발생했습니다.\n"
                    f"• *상태:* 현재 테스트 계정의 비밀번호가 임시 비밀번호(`{self.TEMP_VALID_PW}`)로 남아있을 수 있습니다. 수동 복구가 필요합니다!"
                )
                send_slack_message(slack_alert)

    @allure.title("[TC-ACC-002] 실패: 현재 비밀번호 불일치 검증")
    def test_change_password_fail_wrong_current_pw(self, authenticated_driver, test_user):
        account_page = AccountPage(authenticated_driver)

        logger.info("계정 관리 페이지로 이동합니다.")
        account_page.go_to_account_settings()

        logger.info("틀린 현재 비밀번호를 입력하여 변경을 시도합니다.")
        # 틀린 비번 + 올바른 새 비번 입력
        account_page.change_password(current_pw=self.WRONG_CURRENT_PW, new_pw=self.VALID_NEW_PW)
        
        # 에러 메시지 검증
        error_text = account_page.get_input_error_message()
        logger.info(f"에러 메시지 확인: {error_text}")
        assert "현재 비밀번호가 일치하지 않습니다" in error_text

    @allure.title("[TC-ACC-003] 실패: 새 비밀번호 규칙 위반 검증")
    def test_change_password_fail_invalid_new_pw_format(self, authenticated_driver, test_user):
        account_page = AccountPage(authenticated_driver)
        
        original_pw = test_user["pw"]   # 올바른 현재 비밀번호

        logger.info("계정 관리 페이지로 이동합니다.")
        account_page.go_to_account_settings()

        logger.info("규칙에 어긋나는 새 비밀번호를 입력하여 변경을 시도합니다.")
        # 올바른 현재 비번 + 규칙에 어긋나는 새 비번 입력, 완료 버튼이 비활성화이므로 클릭 시도 생략 (submit=False)
        account_page.change_password(current_pw=original_pw, new_pw=self.INVALID_FORMAT_PW, submit=False)
        
        # 에러 메시지 검증
        error_text = account_page.get_input_error_message()
        logger.info(f"에러 메시지 확인: {error_text}")
        assert "영문, 숫자, 특수문자를 포함해 8자 이상" in error_text