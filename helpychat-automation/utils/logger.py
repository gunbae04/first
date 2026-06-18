"""
================================================================================
커스텀 로거(Logger) 구축 및 Log Rotation 핵심 원리
================================================================================

Q1. 왜 Pytest의 기본 로깅 기능(pytest.ini)에만 의존하지 않고, 별도의 logger.py를 만들었나요?
A1. '실행 환경의 독립성'을 확보하기 위함입니다.
    실제 운영 환경에서는 스크립트를 항상 `pytest` 명령어로만 실행하지 않습니다. 슬랙 알림 로직만 따로 떼어 파이썬 스크립트로 단독 실행(`python slack_notifier.py`)하거나, 다른 배치(Batch) 작업에 물릴 수도 있습니다. 
    이렇게 중앙 관제탑(logger.py)을 하나 만들어두면, 프레임워크 안팎 어디서 실행하든 100% 동일한 포맷과 규칙으로 로그가 기록됩니다.

Q2. 파일 출력에 일반 FileHandler가 아닌 `RotatingFileHandler`를 사용한 이유는 무엇인가요?
A2. 시스템 다운(Crash)을 막기 위한 필수 안전장치인 '로그 로테이션(Log Rotation)' 때문입니다.
    엔터프라이즈 환경에서 매일 수천 개의 E2E 테스트가 돌면 일반 로그 파일은 순식간에 수십 기가바이트(GB)로 팽창하여 서버의 디스크 용량을 꽉 채워버립니다. 
    따라서 "파일 하나가 10MB를 넘으면 자동으로 파일을 쪼개고, 가장 오래된 것부터 지워서 최근 5개만 남겨라(maxBytes, backupCount)"라는 통제 로직을 반드시 걸어두어야 합니다.

Q3. `if logger.handlers: return logger` 라는 방어 코드는 왜 필요한가요?
A3. 로그가 2줄, 3줄씩 중복해서 찍히는 현상을 막기 위해서입니다.
    파이썬의 logging 모듈은 똑같은 이름(__name__)으로 로거 객체를 여러 번 부르면, 그때마다 핸들러(출력 방식)가 계속 누적해서 추가되는 특징이 있습니다. 
    이 코드를 넣어두면 이미 세팅이 끝난 로거는 재활용하게 되므로 로그 중복 출력 버그를 깔끔하게 차단할 수 있습니다.
================================================================================
"""



"""
프로젝트 전역에서 사용되는 커스텀 로거 설정 파일.
Pytest 실행 여부와 무관하게 일관된 로깅 포맷과 Log Rotation(용량 제한)을 제공합니다.
"""

import logging
from pathlib import Path
# from logging.handlers import RotatingFileHandler               # [기존] Python의 logging 모듈은 내부적으로 싱글톤(Singleton)처럼 동작하여, 동일한 이름으로 여러 번 호출해도 같은 객체를 반환.
from concurrent_log_handler import ConcurrentRotatingFileHandler # [변경] 멀티 프로세스/스레드 환경에서 로그 파일 핸들러가 충돌하는 것을 방지하기 위해 ConcurrentLogHandler 외부 패키지 도입.

def get_custom_logger(name: str) -> logging.Logger:
    """
    모듈 이름을 받아 세팅이 완료된 로거 객체를 반환합니다.
    사용법: logger = get_custom_logger(__name__)
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 세팅된 로거라면 중복 추가 방지를 위해 그대로 반환
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # 1. 공통 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 2. 콘솔 출력 핸들러 (StreamHandler)
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)

    # 3. 파일 출력 핸들러 (ConcurrentRotatingFileHandler)
    # 로그 파일 하나가 10MB를 넘으면 파일을 분리하고, 최근 5개까지만 보관합니다.
    
    # 현재 파일(utils/logger.py) 기준으로 2단계 위인 프로젝트 루트 경로를 동적으로 추적하여 logs 폴더 지정
    project_root = Path(__file__).resolve().parent.parent
    log_dir = project_root / "logs"
    
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    # [아키텍처 최적화] 파일명에 동적 날짜를 넣으면 backupCount가 무력화되므로 
    # 고정된 파일명을 사용하여 로테이션 관리 통제권을 유지합니다.
    # automation.log.1, automation.log.2, ... 이런 식으로 자동 분리됨.
    log_file_path = log_dir / "automation.log"

    file_handler = ConcurrentRotatingFileHandler(
        str(log_file_path), # 안전성을 위해 문자열 경로로 변환
        "a",
        maxBytes=10 * 1024 * 1024,  # 10 MB 기준으로 롤링
        backupCount=5,              # 최대 5개 백업 파일 유지 후 순차 삭제 (오버플로우 방지)
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger