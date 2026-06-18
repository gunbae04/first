```markdown
> ================================================================================
> **README 문서화 및 E2E 프레임워크 설계 철학**
> ================================================================================
> 
> **Q1. 코드를 잘 짜면 되지, 왜 이렇게 길고 상세한 README.md 문서가 필수적인가요?**
> A1. 실제 프로젝트 환경에서 '온보딩(Onboarding) 비용 최소화'와 '프로젝트 표준화'를 달성하기 위함입니다. 
> 팀에 신규 QA 엔지니어나 개발자가 합류했을 때, 코드를 일일이 뜯어보지 않아도 이 문서 하나만 보고 5분 만에 본인 PC에 테스트 환경을 구축할 수 있어야 합니다.
> 훌륭한 코드는 잘 쓰인 문서(Documentation)와 결합될 때 비로소 진정한 엔터프라이즈급 인프라가 됩니다.
>
> **Q2. 왜 리포팅 도구로 기본 Pytest-HTML이 아닌, 셋팅이 다소 복잡한 Allure를 사용하나요?**
> A2. '비개발 직군(기획자, PM, 디자이너)과의 원활한 소통'을 위해서입니다.
> 텍스트 위주의 단순한 리포트는 개발자들만 이해할 수 있습니다. 반면 Allure는 테스트 성공률 트렌드, 각 시나리오의 스텝(Step)별 실행 내역,
> 실패 시 캡처된 화면 등을 시각적인 대시보드로 제공하므로, 전사적인 품질 지표를 공유하는 데 가장 이상적인 도구입니다.
> 
> **Q3. Jira 티켓팅 자동화가 이 파이프라인에 포함된 이유는 무엇인가요?**
> A3. '결함 생애주기 관리(Defect Lifecycle Management)'를 자동화하기 위함입니다.
> 테스트 실행 후 에러 로그와 스크린샷을 사람이 일일이 복사해서 Jira에 올리는 것은 비효율적입니다.
> 프레임워크가 실패를 감지한 즉시 Jira Software의 해당 'Project(프로젝트)' 보드에 버그 티켓을 자동 생성하고 증거를 첨부하도록 구축해 두면,
> 누락 없는 완벽한 결함 추적이 가능해집니다.
> ================================================================================
```



# 🤖 HelpyChat QA Automation Framework

본 프로젝트는 HelpyChat 서비스의 품질을 보증하기 위해 구축된 **End-to-End (E2E) UI 테스트 자동화 프레임워크**입니다. 
Page Object Model(POM) 디자인 패턴을 기반으로 작성되었으며, 환경/데이터/유틸리티의 완벽한 모듈화, Allure 리포트 생성 및 Jira 자동 결함 트래킹 기능을 포함한 파이프라인을 경험할 수 있도록 구성되었습니다.

---

## 🏗️ Architecture & Tech Stack
* **Language**: Python 3.10+
* **Testing Framework**: Pytest
* **Browser Automation**: Selenium WebDriver
* **Reporting**: Allure Framework
* **CI/CD Integration**: Jira REST API (Auto Bug Ticketing)

---

## 📁 Directory Structure

```text
helpychat-automation/
├── config/                 # ⚙️ 환경 및 전역 변수 설정 (BASE_URL, JIRA 계정 등)
│   └── config.py           
├── data/                   # 💾 테스트 데이터 분리 (계정 정보, 시나리오 데이터 등)
│   ├── users.json          
│   └── chat_messages.csv   
├── pages/                  # 🖥️ Page Object Model (화면별 UI 로케이터 및 액션)
│   ├── base_page.py        
│   └── ...                 
├── tests/                  # 🧪 실제 테스트 케이스 (도메인별 분리)
│   ├── conftest.py         # 🎯 Pytest 전역 공유 픽스처 및 훅 설정 파일
│   ├── ui/                 # 프론트엔드 E2E UI 시나리오 테스트
│   └── api/                # 백엔드 API 통합 테스트 (추가 확장 예정)
├── utils/                  # 🛠️ 공통 유틸리티 (Jira 자동 티켓팅 헬퍼 등)
│   └── jira_client.py      
├── logs/                   # 📝 실행 로그 저장 폴더 (Git 추적 제외)
├── reports/                # 📊 Allure 테스트 결과 리포트 원시 데이터 (Git 추적 제외)
├── .env                    # 민감 정보 (Jira API 토큰, 비밀번호 등)
├── .gitignore              # Git 추적 제외 목록
├── pytest.ini              # Pytest 실행 및 로깅 환경 설정
├── requirements.txt        # 파이썬 패키지 의존성 목록
└── README.md               # 프로젝트 실행 가이드 및 아키텍처 설명
```

---

## 🛠️ 환경 셋팅 및 실행 가이드 (Getting Started)

본 프로젝트를 로컬 PC에서 실행하기 위해서는 파이썬 패키지 외에도 리포트 생성을 위한 추가 환경 구성이 필요합니다. 아래 순서대로 터미널에 입력하여 셋팅을 진행해 주세요.

### 1. 필수 패키지 설치
UI 자동화 제어, API 통신, 리포트 데이터 수집, 환경 변수 관리를 위한 파이썬 라이브러리들을 설치합니다.

아래 명령어를 복사해서 터미널에 입력하세요:
```bash
pip install -r requirements.txt
```
*(또는 개별 설치 시: `pip install pytest selenium allure-pytest requests python-dotenv concurrent-log-handler`)*

### 2. 환경 변수 설정 (.env)
프로젝트 최상위 경로에 `.env` 파일을 생성하고 아래 양식에 맞게 본인의 정보를 입력합니다.
⚠️ **[보안 주의]** `.env` 파일은 절대 Git에 커밋하지 마세요. 반드시 `.gitignore`에 등록해야 합니다.

```env
TEST_USER_ID=your_id@example.com
TEST_USER_PW=your_password
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your_jira_email@example.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=YOUR_PROJECT_KEY
```

### 3. Allure 리포트 환경 구성
Allure는 생성된 JSON 데이터를 시각적인 웹 리포트로 렌더링하기 위해 내부적으로 Java와 Node.js를 사용합니다.

* **① JAVA_HOME 환경 변수 등록:** PC에 Java(JDK 8 이상)가 설치되어 있고 환경 변수가 세팅되어 있어야 합니다.
* **② Allure CLI 툴 설치:** Node.js 기반으로 아래 명령어를 터미널에 입력해 전역 설치합니다.

아래 명령어를 복사해서 터미널에 입력하세요:
```bash
npm install -g allure-commandline
```

---

## 🚀 How to Run (테스트 실행)

`pytest.ini`에 필수 옵션이 모두 세팅되어 있으므로, 명령어 하나로 테스트를 실행하고 Allure 결과 데이터를 수집할 수 있습니다.

**전체 테스트 실행:**
```bash
pytest
```

**특정 디렉토리(UI 테스트)만 실행:**
```bash
pytest tests/ui/
```

---

## 📊 Reporting & Issue Tracking

### 1. 테스트 결과 리포트 확인 (Allure)
테스트가 완료되면 `reports/allure-results/`에 데이터가 쌓입니다. 아래 명령어를 터미널에 입력하여 웹 브라우저에 시각화된 Allure 대시보드를 띄웁니다.

```bash
allure serve reports/allure-results
```

### 2. Auto Ticketing (Jira 연동)
테스트 실행 중 검증(Assertion)에 실패하거나 Timeout 에러가 발생할 경우, `tests/conftest.py`의 Pytest Hook과 `utils/jira_client.py`가 이를 감지하여 다음 액션을 자동으로 수행합니다.

1. 에러가 발생한 즉시 브라우저 스크린샷 캡처
2. 에러 로그 정제 후 지정된 Jira 프로젝트 보드에 버그(Bug) 티켓 자동 생성
3. 생성된 Jira 티켓에 캡처한 스크린샷 파일 직접 첨부 (Direct Attach)