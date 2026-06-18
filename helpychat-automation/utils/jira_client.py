"""
================================================================================
Jira REST API 연동 및 결함 관리 자동화의 가치
================================================================================

Q1. 테스트가 실패했을 때 수동으로 버그를 등록하지 않고, Jira API로 티켓을 자동 생성하면 어떤 장점이 있나요?
A1. 결함의 '추적성(Traceability)' 확보와 '업무 효율성'의 극대화입니다.
    E2E 테스트가 수백 개로 늘어나면 사람이 리포트를 보고 일일이 Jira에 복사-붙여넣기 하는 것 자체가 엄청난 낭비입니다.
    이를 자동화하면 결함이 발견된 즉시 정확한 에러 로그와 스크린샷이 담긴 티켓이 생성되므로, 
    수동 등록 누락으로 인한 '결함 방치'를 막고 개발팀에게 실시간으로 무결한 디버깅 정보를 피드백할 수 있습니다.
    이는 DevOps 파이프라인에서 지속적 통합/배포(CI/CD)를 가능하게 하는 시니어 QA의 핵심 역량입니다.

Q2. 파일 첨부 API에서 `headers = {"X-Atlassian-Token": "no-check"}`를 명시한 이유는 무엇인가요?
A2. Atlassian(Jira 사) 보안 정책인 'XSRF(교차 사이트 요청 위조) 방어막'을 통과하기 위한 규격입니다.
    Jira 첨부파일 API는 브라우저가 아닌 외부 스크립트에서 파일 업로드 요청이 들어올 때, 
    악의적인 변조 요청이 아님을 증명하기 위해 이 특수한 헤더를 강제합니다. 
    만약 이 헤더를 누락하면 데이터 형식이 완벽하더라도 서버가 요청을 거절하므로, API 명세서(Spec)의 세부 조건을 꼼꼼히 확인하는 습관이 중요합니다.

Q3. 스크린샷을 찍을 때 하드디스크에 파일로 저장하지 않고 `image_bytes`(바이트) 데이터로 주고받는 이유는 무엇인가요?
A3. 입출력(I/O) 성능 최적화와 CI/CD 인프라 리소스 관리 때문입니다.
    스크린샷을 로컬 파일(`error.png`)로 쓰고 다시 읽어오는 방식은 디스크 잔여 용량 문제를 유발하고, 
    동시에 여러 테스트가 돌 때 파일 접근 권한 충돌(File Lock)이 일어날 수 있습니다.
    메모리 상에 뜬 바이너리 데이터 그대로를 `requests.post(files=...)` 폼 데이터로 감싸 전송하는 것이 
    가장 깔끔하고 리소스를 낭비하지 않는 설계입니다.
================================================================================
"""



import requests
from requests.auth import HTTPBasicAuth
from config.config import JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY, DEFAULT_API_TIMEOUT

# 로거 설정
from utils.logger import get_custom_logger
logger = get_custom_logger(__name__)

# =========================================================
# [7] Jira API 연동 헬퍼 함수
# =========================================================
def create_jira_bug_ticket(summary, description):
    """Jira REST API를 호출하여 버그 이슈 자동 생성."""
    url = f"{JIRA_URL}/rest/api/2/issue"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    # Jira 티켓 생성 규격(Payload)
    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Bug"}, # Jira에 'Bug' 또는 '버그' 이슈 타입이 존재해야 함
            "labels": ["Automation", "UI-Test"]
        }
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            auth=auth,
            timeout=DEFAULT_API_TIMEOUT
        )
        if response.status_code == 201:
            issue_key = response.json().get("key")
            logger.info(f"🚨 [JIRA 연동 성공] 티켓 자동 생성 완료: {JIRA_URL}/browse/{issue_key}")
            return issue_key # 스크린샷 첨부를 위해 생성된 티켓 번호를 반환
        else:
            logger.error(f"❌ [JIRA 연동 실패] 응답 코드: {response.status_code}, 상세: {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ [JIRA 통신 에러] API 호출 중 문제가 발생했습니다: {e}")
        return None

def attach_image_to_jira(issue_key, image_bytes):
    """생성된 Jira 이슈에 스크린샷 이미지 첨부."""
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}/attachments"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {"X-Atlassian-Token": "no-check"} # Jira 첨부파일 API의 핵심: 이 헤더가 없으면 404 에러 발생
    files = {"file": ("error_screenshot.png", image_bytes, "image/png")}  # 메모리에 있는 스크린샷 데이터(image_bytes)를 파일 형태로 포장해서 전송
    
    try:
        response = requests.post(
            url,
            headers=headers,
            auth=auth,
            files=files,
            timeout=DEFAULT_API_TIMEOUT + 10 # 파일 업로드는 일반 텍스트 API보다 오래 걸릴 수 있으므로, 기본 타임아웃에 10초를 더 줌 (+10)
        )
        if response.status_code == 200:
            logger.info(f"📎 [JIRA 첨부 성공] 스크린샷 이미지가 티켓에 정상 업로드되었습니다.")
        else:
            logger.error(f"❌ [JIRA 첨부 실패] 상태 코드: {response.status_code}, 상세: {response.text}")
    except Exception as e:
        logger.error(f"❌ [JIRA 첨부 에러] {e}")