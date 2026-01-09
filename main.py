"""
원단 원가 계산기 - 메인 진입점

모듈화된 새 구조를 사용합니다.
기존 calculate_net_price.py는 레거시 코드로 유지됩니다.
"""

import sys
import tkinter as tk

# 레거시 코드 import (기존 UI 사용)
from calculate_net_price import FabricCostCalculatorApp

# 새 모듈들 (향후 점진적 마이그레이션용)
from config import get_config
from utils.logger import setup_logger

# 로거 설정
logger = setup_logger('main')


def main():
    """메인 함수"""
    try:
        # 설정 로드
        config = get_config()
        logger.info("=" * 50)
        logger.info("원단 원가 계산기 시작")
        logger.info(f"기본 환율: {config.default_exchange_rate}원")
        logger.info("=" * 50)

        # Tkinter 루트 생성
        root = tk.Tk()

        # 기존 UI 사용 (레거시)
        app = FabricCostCalculatorApp(root)

        # 메인 루프 실행
        root.mainloop()

        logger.info("프로그램 종료")

    except Exception as e:
        logger.exception(f"예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
