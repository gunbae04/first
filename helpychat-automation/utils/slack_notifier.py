"""
================================================================================
Slack Webhook 연동 및 알림 파이프라인 설계 전략
================================================================================

Q1. 복잡한 Slack Bot API를 사용하지 않고 Webhook(웹훅) 방식을 사용하는 이유는 무엇인가요?
A1. '단방향 푸시(Push)' 알림에 최적화된 가장 가볍고 확실한 방법이기 때문입니다.
    웹훅은 고유한 URL 하나만 있으면 별도의 복잡한 인증(OAuth)이나 세션 유지 없이 즉시 메시지를 쏠 수 있습니다. 
    Jenkins나 GitLab CI/CD, GitHub Actions 같은 CI/CD 서버에서 테스트가 끝난 직후,
    팀원들에게 결과를 빠르게 브로드캐스팅하는 용도로 가장 널리 쓰이는 표준 방식입니다.

Q2. 테스트가 실패할 때마다 실시간으로 알림을 보내지 않고, 모든 테스트가 끝난 후 '요약(Summary)'을 보내는 이유는 무엇인가요?
A2. 개발 조직의 치명적인 문제인 '알림 피로도(Alert Fatigue)'를 방지하기 위함입니다.
    만약 100개의 테스트 중 50개가 연쇄 실패했을 때 슬랙 메시지가 50번 연속으로 울린다면, 팀원들은 스트레스를 받아 해당 채널의 알림을 꺼버리게 됩니다(Mute). 
    따라서 에러 로그와 스크린샷은 조용히 Jira 티켓과 Allure 리포트에 모아두고, 슬랙으로는 "총 몇 개 중 몇 개가 실패했습니다"라는 정제된 요약본 딱 하나만 보내는 것이 시니어 QA의 협업 매너입니다.

Q3. 슬랙 전송 코드에 `try-except` 예외 처리를 꼼꼼하게 해둔 이유는 무엇인가요?
A3. '주객전도'를 막기 위해서입니다. 
    우리의 메인 목적은 '테스트 검증'이지 '슬랙 발송'이 아닙니다. 만약 슬랙 서버가 일시적으로 다운되거나 Webhook URL이 잘못되어 에러가 났을 때, 
    예외 처리가 없다면 멀쩡하게 성공한 전체 E2E 테스트 프로세스 자체가 '실패(Failed)'로 처리되어 CI/CD 파이프라인이 멈춰버립니다. 
    이러한 '비핵심 로직의 실패가 핵심 로직에 영향을 주지 않도록(Graceful Degradation)' 방어벽을 쳐둔 것입니다.
================================================================================
"""



"""
Slack Webhook을 이용해 테스트 결과를 채널에 전송하는 유틸리티.
"""

import requests
from config.config import SLACK_WEBHOOK_URL, DEFAULT_API_TIMEOUT

# 로거 설정
from utils.logger import get_custom_logger
logger = get_custom_logger(__name__)

def send_slack_message(message: str):
    """Slack Webhook을 통해 텍스트 메시지를 전송합니다."""
    if not SLACK_WEBHOOK_URL:
        logger.warning("⚠️ SLACK_WEBHOOK_URL이 설정되지 않아 슬랙 알림을 생략합니다.")
        return

    headers = {'Content-Type': 'application/json'}
    payload = {'text': message}

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            headers=headers,
            timeout=DEFAULT_API_TIMEOUT
        )
        if response.status_code == 200:
            logger.info("📢 [Slack 발송 성공] 테스트 결과 알림을 슬랙으로 전송했습니다.")
        else:
            logger.error(f"❌ [Slack 발송 실패] 상태 코드: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ [Slack 통신 에러] {e}")

def send_test_summary(total: int, passed: int, failed: int, duration: float):
    """테스트 세션 종료 후 요약 리포트를 구성하여 슬랙으로 전송합니다."""
    # [가시성 최적화] 실패 여부에 따라 헤더 아이콘을 동적으로 변경하여 가독성을 높입니다.
    status_icon = "🟢 *[SUCCESS]*" if failed == 0 else "🔴 *[FAILED]*"
    
    message = (
        f"📊 *E2E 자동화 테스트 실행 결과* {status_icon}\n"
        f"-----------------------------------------\n"
        f"• *총 테스트 수:* {total} 개\n"
        f"• *✅ 통과:* {passed} 개\n"
        f"• *🚨 실패:* {failed} 개\n"
        f"• *⏱️ 소요 시간:* {duration:.2f} 초\n"
        f"-----------------------------------------\n"
        f"자세한 결함 내역은 *Jira 보드* 및 *Allure 리포트*를 확인해 주세요! 🚀"
    )
    
    send_slack_message(message)