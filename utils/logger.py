"""
로깅 시스템 모듈

애플리케이션 전체에서 사용할 로거를 설정합니다.
파일과 콘솔 양쪽에 로그를 기록하며, 레벨별로 다른 처리를 합니다.
"""

import logging
from pathlib import Path
from datetime import datetime
from models.constants import FileNames


def setup_logger(
    name: str,
    log_file: str = None,
    level: int = logging.DEBUG,
    console_level: int = logging.INFO
) -> logging.Logger:
    """
    로거를 설정합니다.

    Args:
        name: 로거 이름 (일반적으로 __name__ 사용)
        log_file: 로그 파일 경로 (None이면 기본값 사용)
        level: 파일 로그 레벨 (기본: DEBUG)
        console_level: 콘솔 로그 레벨 (기본: INFO)

    Returns:
        설정된 Logger 객체
    """
    # 로거 생성
    logger = logging.getLogger(name)

    # 이미 핸들러가 설정되어 있으면 중복 방지
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # 로그 파일 경로 설정
    if log_file is None:
        log_file = FileNames.LOG_FILE

    # 로그 디렉토리가 없으면 생성
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 파일 핸들러 (상세 로그 기록)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)

    # 콘솔 핸들러 (중요 정보만 출력)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)

    # 포맷터 설정
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    file_handler.setFormatter(detailed_formatter)
    console_handler.setFormatter(simple_formatter)

    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    기존 로거를 가져오거나 새로 생성합니다.

    Args:
        name: 로거 이름

    Returns:
        Logger 객체
    """
    logger = logging.getLogger(name)

    # 핸들러가 없으면 기본 설정으로 생성
    if not logger.handlers:
        return setup_logger(name)

    return logger


class LoggerMixin:
    """
    로거 기능을 클래스에 추가하는 Mixin

    사용 예시:
        class MyClass(LoggerMixin):
            def my_method(self):
                self.logger.info("작업 시작")
    """

    @property
    def logger(self) -> logging.Logger:
        """클래스명으로 로거를 반환합니다."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def log_function_call(func):
    """
    함수 호출을 로깅하는 데코레이터

    사용 예시:
        @log_function_call
        def calculate_cost(price, quantity):
            return price * quantity
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"함수 호출: {func.__name__}(args={args}, kwargs={kwargs})")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"함수 완료: {func.__name__} -> {result}")
            return result
        except Exception as e:
            logger.exception(f"함수 오류: {func.__name__} - {e}")
            raise
    return wrapper


def log_exception(logger: logging.Logger, exc: Exception, context: str = ""):
    """
    예외를 상세하게 로깅합니다.

    Args:
        logger: Logger 객체
        exc: Exception 객체
        context: 추가 컨텍스트 정보
    """
    error_msg = f"오류 발생"
    if context:
        error_msg += f" [{context}]"
    error_msg += f": {type(exc).__name__}: {exc}"

    logger.exception(error_msg)


# 애플리케이션 전역 로거
app_logger = setup_logger('app')


if __name__ == '__main__':
    # 테스트 코드
    test_logger = setup_logger('test')

    test_logger.debug("디버그 메시지")
    test_logger.info("정보 메시지")
    test_logger.warning("경고 메시지")
    test_logger.error("에러 메시지")

    try:
        result = 1 / 0
    except Exception as e:
        log_exception(test_logger, e, "테스트 중")

    print(f"\n로그 파일 생성됨: {FileNames.LOG_FILE}")
