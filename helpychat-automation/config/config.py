"""
================================================================================
환경 변수 관리 및 Fail-Fast 원칙
================================================================================

Q1. 왜 비밀번호나 API 토큰 같은 값을 코드에 직접 적지 않고 `.env` 파일과 `os.getenv`를 사용하나요?
A1. '보안(Security)'과 '환경의 이식성(Portability)' 때문입니다.
    비밀번호가 하드코딩된 코드가 Git(GitLab/GitHub 등)에 올라가면 심각한 보안 사고로 이어집니다.
    또한, 로컬 PC에서는 `.env` 파일을 읽어서 실행하지만, 실제 CI/CD 파이프라인(Jenkins, GitLab CI/CD, GitHub Actions)에서는 
    서버에 미리 등록해 둔 환경 변수를 주입받아 테스트를 실행합니다. 즉, 코드를 한 줄도 바꾸지 않고 
    로컬과 서버 환경 양쪽에서 안전하게 자동화를 돌리기 위한 필수 아키텍처입니다.

Q2. `if not TEST_USER["id"]... raise ValueError` 처럼 초반에 에러를 발생시키는 이유는 무엇인가요?
A2. '빠른 실패(Fail-Fast)' 원칙을 적용한 것입니다.
    만약 필수 환경 변수가 빠져있는데도 이 검증 로직이 없다면, 프레임워크는 일단 무작정 크롬 브라우저를 띄우고 
    사이트에 접속한 뒤에야 "어? 아이디가 없네?" 하고 에러를 뱉게 됩니다. 이는 귀중한 테스트 시간과 서버 리소스를 낭비합니다.
    실행 즉시 설정 오류를 잡아내어 즉각 테스트를 중단시키는 방어적 프로그래밍 기법입니다.

Q3. BASE_UI_URL과 BASE_API_URL을 굳이 따로 분리한 이유는 무엇인가요?
A3. E2E 테스트(프론트엔드)와 API 테스트(백엔드)의 타겟 서버가 다를 수 있기 때문입니다.
    실무에서는 종종 프론트엔드는 Staging(운영 직전) 서버를 띄워두고, 백엔드는 Dev(개발) 서버의 API를 
    바라보도록 크로스(Cross)로 연결해서 테스트하는 등 환경 조합이 다양하게 발생하므로 URL을 각각 분리하여 관리해야 유연합니다.
================================================================================
"""



import os
from dotenv import load_dotenv

# .env 파일을 읽어서 OS 환경 변수로 메모리에 로드 (로컬에서만 사용)
load_dotenv()

# =========================================================
# 테스트 기본 정보 및 설정
# =========================================================
BASE_UI_URL = "https://qaproject.elice.io"
BASE_API_URL = "https://dev-v2-community-api.dev.elicer.io"

# UI 자동화 테스트 시 요소 로딩을 기다리는 기본 명시적 대기 시간 (초)
DEFAULT_WAIT_TIME = 10
# API 통신 시 서버의 응답을 기다리는 최대 시간 (초)
DEFAULT_API_TIMEOUT = 10

TEST_USER = {
    "id": os.getenv("TEST_USER_ID"), # 환경 변수에 설정 - HelpyChat 아이디
    "pw": os.getenv("TEST_USER_PW")  # 환경 변수에 설정 - HelpyChat 비밀번호
}

if not TEST_USER["id"] or not TEST_USER["pw"]:
    raise ValueError(
        "TEST_USER_ID 또는 TEST_USER_PW 환경 변수가 설정되지 않았습니다."
    )

# =========================================================
# Jira 연동 설정
# =========================================================
JIRA_URL = os.getenv("JIRA_BASE_URL")            # 환경변수에 설정 - Jira 주소
JIRA_EMAIL = os.getenv("JIRA_EMAIL")             # 환경변수에 설정 - Jira 이메일
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")     # 환경변수에 설정 - Jira API 토큰
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY") # 환경변수에 설정 - 티켓을 생성할 프로젝트 키

# =========================================================
# Slack 연동 설정
# =========================================================
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")