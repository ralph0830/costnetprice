"""
설정 관리 모듈

애플리케이션 설정을 파일로 관리하고 동적으로 로드/저장합니다.
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any
from models.constants import (
    DefaultValues,
    FileNames,
    UIConfig
)


@dataclass
class ExchangeRateScenario:
    """환율 시나리오 설정"""
    label: str
    offset: float


@dataclass
class AppConfig:
    """애플리케이션 설정"""

    # 기본값
    default_exchange_rate: float = DefaultValues.EXCHANGE_RATE_KRW_USD
    default_weaving_fee: float = DefaultValues.WEAVING_FEE_KRW_KG
    default_dyeing_fee: float = DefaultValues.DYEING_FEE_KRW_KG
    default_weaving_loss: float = DefaultValues.WEAVING_LOSS_PCT
    default_dyeing_loss: float = DefaultValues.DYEING_LOSS_PCT
    default_delay_loss: float = DefaultValues.DELAY_LOSS_PCT
    default_fabric_width: float = DefaultValues.FABRIC_WIDTH_INCH
    default_proc_weight: float = DefaultValues.PROC_WEIGHT_VALUE
    default_selling_price: float = DefaultValues.SELLING_PRICE_USD_YD

    # 환율 시나리오
    exchange_rate_scenarios: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"label": "낮은 환율", "offset": -50},
        {"label": "기준 환율", "offset": 0},
        {"label": "높은 환율", "offset": 50}
    ])

    # 파일 경로
    yarn_db_file: str = FileNames.YARN_DB_JSON
    history_db_file: str = FileNames.HISTORY_DB
    excel_template_file: str = FileNames.EXCEL_TEMPLATE
    log_file: str = FileNames.LOG_FILE

    # UI 설정
    window_width: int = UIConfig.MAIN_WINDOW_WIDTH
    window_height: int = UIConfig.MAIN_WINDOW_HEIGHT

    # 로깅 설정
    log_level: str = "DEBUG"
    console_log_level: str = "INFO"

    @classmethod
    def load(cls, config_file: str = None) -> 'AppConfig':
        """
        설정 파일에서 로드합니다.

        Args:
            config_file: 설정 파일 경로 (기본값: config.json)

        Returns:
            AppConfig 인스턴스
        """
        if config_file is None:
            config_file = FileNames.CONFIG_FILE

        config_path = Path(config_file)

        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return cls(**data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"설정 파일 로드 오류: {e}. 기본 설정을 사용합니다.")
                return cls()
        else:
            # 설정 파일이 없으면 기본 설정으로 생성
            config = cls()
            config.save(config_file)
            return config

    def save(self, config_file: str = None):
        """
        설정을 파일에 저장합니다.

        Args:
            config_file: 설정 파일 경로 (기본값: config.json)
        """
        if config_file is None:
            config_file = FileNames.CONFIG_FILE

        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)

    def get_exchange_scenarios(self, base_rate: float) -> List[Dict[str, Any]]:
        """
        환율 시나리오 목록을 생성합니다.

        Args:
            base_rate: 기준 환율

        Returns:
            [{"label": "...", "rate": ...}, ...] 형태의 리스트
        """
        scenarios = []
        for scenario in self.exchange_rate_scenarios:
            rate = base_rate + scenario["offset"]
            scenarios.append({
                "label": f"{scenario['label']} ({rate:.0f}원)",
                "rate": rate,
                "offset": scenario["offset"]
            })
        return scenarios

    def add_exchange_scenario(self, label: str, offset: float):
        """
        환율 시나리오를 추가합니다.

        Args:
            label: 시나리오 라벨
            offset: 기준 환율로부터의 변동폭
        """
        self.exchange_rate_scenarios.append({
            "label": label,
            "offset": offset
        })

    def remove_exchange_scenario(self, index: int):
        """
        환율 시나리오를 제거합니다.

        Args:
            index: 제거할 시나리오 인덱스
        """
        if 0 <= index < len(self.exchange_rate_scenarios):
            self.exchange_rate_scenarios.pop(index)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)


# 전역 설정 인스턴스
_config_instance = None


def get_config() -> AppConfig:
    """
    전역 설정 인스턴스를 반환합니다.
    싱글톤 패턴으로 구현되어 있습니다.

    Returns:
        AppConfig 인스턴스
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig.load()
    return _config_instance


def reload_config(config_file: str = None):
    """
    설정을 다시 로드합니다.

    Args:
        config_file: 설정 파일 경로
    """
    global _config_instance
    _config_instance = AppConfig.load(config_file)


if __name__ == '__main__':
    # 테스트 코드
    print("=== 설정 파일 테스트 ===\n")

    # 1. 기본 설정 생성 및 저장
    config = AppConfig()
    print("1. 기본 설정 생성:")
    print(f"   기본 환율: {config.default_exchange_rate}원")
    print(f"   제직료: {config.default_weaving_fee}원/kg")
    print(f"   염색료: {config.default_dyeing_fee}원/kg")

    # 2. 환율 시나리오 테스트
    print("\n2. 환율 시나리오 (기준환율 1150원):")
    scenarios = config.get_exchange_scenarios(1150)
    for scenario in scenarios:
        print(f"   {scenario['label']}: {scenario['rate']:.0f}원")

    # 3. 시나리오 추가
    config.add_exchange_scenario("최저 환율", -100)
    config.add_exchange_scenario("최고 환율", +100)
    print("\n3. 시나리오 추가 후:")
    scenarios = config.get_exchange_scenarios(1150)
    for scenario in scenarios:
        print(f"   {scenario['label']}: {scenario['rate']:.0f}원")

    # 4. 설정 저장
    test_config_file = "test_config.json"
    config.save(test_config_file)
    print(f"\n4. 설정 파일 저장: {test_config_file}")

    # 5. 설정 로드
    loaded_config = AppConfig.load(test_config_file)
    print(f"\n5. 설정 파일 로드:")
    print(f"   환율 시나리오 개수: {len(loaded_config.exchange_rate_scenarios)}개")

    # 6. 정리
    Path(test_config_file).unlink()
    print(f"\n6. 테스트 파일 삭제 완료")
