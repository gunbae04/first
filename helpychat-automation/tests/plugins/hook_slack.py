"""
================================================================================
Pytest Hook을 활용한 테스트 세션 통계 및 알림 자동화
================================================================================

Q1. 왜 개별 테스트가 끝날 때마다 슬랙을 보내지 않고, `pytest_sessionfinish` 훅을 사용하나요?
A1. '알림 피로도(Alert Fatigue)'를 방지하고 전체 파이프라인의 '요약 지표'를 제공하기 위함입니다.
    100개의 테스트 중 50개가 실패했다고 해서 50번의 알림이 연속으로 울리면 팀원들은 스트레스를 받아 해당 채널을 무음(Mute) 처리하게 됩니다. 
    따라서 세션 종료 훅을 이용해 모든 테스트가 끝난 직후, 전체 결과가 정제된 요약본 하나만 브로드캐스팅하는 것이 협업에 가장 이상적인 방식입니다.

Q2. `reporter.stats.get('error')`와 `failed`를 구분해서 합산하는 이유는 무엇인가요?
A2. Pytest의 상태 관리 구조를 정확히 반영하기 위함입니다.
    `failed`는 테스트 코드 본문(call)의 검증(assert) 로직에서 실패한 것을 의미하고,
    `error`는 브라우저를 띄우거나 로그인을 하는 사전 준비(setup/fixture) 단계에서 시스템 크래시가 난 것을 의미합니다. 
    발생 원인은 다르지만 파이프라인 관점에서는 둘 다 '해결해야 할 결함'이므로, 이 둘을 합산(`total_failed`)하여 정확한 실패 지표를 팀에 보고해야 합니다.

Q3. 통계를 수집할 때 왜 직접 변수를 만들어 카운트하지 않고 `terminalreporter` 플러그인을 가져와서 사용하나요?
A3. 프레임워크의 '안정성'과 '정확성' 때문입니다.
    전역 변수를 사용해 직접 성공/실패 횟수를 카운트하면 추후 병렬 테스트(xdist) 환경을 도입할 때 숫자가 꼬이거나 누락될 위험이 매우 큽니다. 
    반면 `terminalreporter`는 Pytest 코어 시스템이 직접 관리하는 내부 통계 객체이므로, 어떤 복잡한 환경에서도 100% 정확한 실행 결과를 보장합니다.
================================================================================
"""



"""
테스트 세션 시작/종료 통계를 수집하고 Slack으로 알림을 전송하는 Pytest Hook
"""
import time
from utils.slack_notifier import send_test_summary

def pytest_sessionstart(session):
    """테스트 세션이 시작될 때 실행. 전체 소요 시간 측정을 위해 시작 시간을 기록합니다."""
    session.start_time = time.time()

def pytest_sessionfinish(session, exitstatus):
    """모든 테스트 세션이 종료된 직후 실행. 전체 통계를 수집하여 슬랙으로 전송합니다."""
    # Pytest의 내부 Reporter 플러그인을 가져와서 통계를 추출합니다.
    reporter = session.config.pluginmanager.get_plugin('terminalreporter')
    
    if reporter:
        passed = len(reporter.stats.get('passed', []))
        failed = len(reporter.stats.get('failed', []))
        error = len(reporter.stats.get('error', []))     # Setup(Fixture) 단계에서 발생한 에러
        skipped = len(reporter.stats.get('skipped', []))
        
        total_failed = failed + error
        total = passed + total_failed + skipped
        
        # 총 소요 시간 계산
        duration = time.time() - getattr(session, 'start_time', time.time())
        
        # Slack 발송
        send_test_summary(total=total, passed=passed, failed=total_failed, duration=duration)