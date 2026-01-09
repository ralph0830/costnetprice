# 코드 개선 제안서

분석일: 2026-01-09
대상 파일: calculate_net_price.py (1303 lines)

## 🔴 Critical (높은 우선순위)

### 1. 코드 모듈화 - 단일 파일 분리

**현재 문제:**
- 1303줄의 단일 파일로 유지보수 어려움
- 계층 간 의존성이 명확하지 않음
- 테스트 및 재사용 불가능

**개선 방안:**
```
costNETprice/
├── models/
│   ├── yarn.py              # Yarn 데이터 클래스
│   ├── calculation.py        # 계산 결과 데이터 클래스
│   └── constants.py          # 상수 정의
├── data/
│   ├── yarn_repository.py    # yarn_db.json 관리
│   └── history_repository.py # calculation_history.db 관리
├── services/
│   ├── calculator.py         # 계산 로직 (비즈니스 로직)
│   ├── converter.py          # 단위/통화 변환 로직
│   └── validator.py          # 입력 검증 로직
├── ui/
│   ├── main_window.py        # FabricCostCalculatorApp
│   ├── yarn_manager.py       # YarnManagementWindow
│   └── history_window.py     # HistoryWindow
├── utils/
│   ├── excel_exporter.py     # Excel 출력 로직
│   └── logger.py             # 로깅 설정
├── config.py                 # 설정 관리
└── main.py                   # 진입점
```

**장점:**
- 각 모듈의 책임이 명확해짐
- 테스트 작성 가능
- 코드 재사용성 증가
- 협업 시 충돌 감소

---

### 2. 매직 넘버 제거 및 상수화

**현재 문제:**
```python
# 코드 곳곳에 하드코딩된 값들
proc_weight_gyd = proc_weight_input_val * fabric_width_inch * 0.02322576  # 이게 뭘까?
yarn_price_usd_per_kg = price_in_usd_original_unit * 2.20462  # 이것도?
exchange_rate_var = tk.DoubleVar(value=1150)  # 왜 1150?
weaving_fee_krw_kg_var = tk.DoubleVar(value=450)  # 왜 450?
rates_to_calculate = {... base_rate - 50 ...}  # 왜 50?
```

**개선 방안:**
```python
# constants.py
class UnitConversion:
    """단위 변환 상수"""
    LB_TO_KG = 0.453592
    KG_TO_LB = 2.20462
    YD_TO_M = 0.9144
    M_TO_YD = 1.09361
    INCH_TO_CM = 2.54
    GSM_TO_GYD_PER_INCH = 0.02322576  # g/sqm을 g/yd로 변환 (inch당)

class DefaultValues:
    """기본값 설정"""
    EXCHANGE_RATE_KRW_USD = 1150
    WEAVING_FEE_KRW_KG = 450
    DYEING_FEE_KRW_KG = 1900
    EXCHANGE_RATE_VARIANCE = 50  # 환율 시나리오 변동폭

    WEAVING_LOSS_PCT = 2
    DYEING_LOSS_PCT = 4
    DELAY_LOSS_PCT = 6

class ValidationRules:
    """검증 규칙"""
    MIN_FABRIC_WIDTH = 0.01
    MIN_WEIGHT_VALUE = 0.01
    MIN_EXCHANGE_RATE = 100
    MAX_YARN_RATIO_TOLERANCE = 1e-3  # 100% 검증 허용 오차
```

**사용 예시:**
```python
# 변환 전
price_usd_kg = price_usd_lb * 2.20462

# 변환 후
from models.constants import UnitConversion
price_usd_kg = price_usd_lb * UnitConversion.KG_TO_LB
```

---

### 3. 에러 처리 개선 - 로깅 시스템 도입

**현재 문제:**
- messagebox 28회 사용 → GUI 없이는 디버깅 불가
- print 문 37회 사용 → 운영 환경에서 추적 어려움
- 에러 발생 시 상세 컨텍스트 부족

**개선 방안:**
```python
# utils/logger.py
import logging
from pathlib import Path

def setup_logger(name: str, log_file: str = "app.log") -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 파일 핸들러
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    # 콘솔 핸들러
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

# services/calculator.py
from utils.logger import setup_logger

logger = setup_logger(__name__)

class CostCalculator:
    def calculate_single_scenario(self, inputs, exchange_rate):
        try:
            logger.info(f"계산 시작: 환율={exchange_rate}")
            # 계산 로직
            logger.info(f"계산 완료: NET={net_cost:.2f}")
            return result
        except ValueError as e:
            logger.error(f"계산 오류: {e}, inputs={inputs}")
            raise
        except Exception as e:
            logger.exception(f"예상치 못한 오류: {e}")
            raise
```

**에러 처리 레이어 분리:**
```python
# ui/main_window.py
class FabricCostCalculatorApp:
    def calculate_all(self):
        try:
            inputs = self.get_all_inputs()
            results = self.calculator.calculate_all(inputs)
            self._display_results(results)
        except ValueError as e:
            # 사용자 입력 오류 → messagebox
            messagebox.showerror("입력 오류", str(e))
            logger.warning(f"사용자 입력 오류: {e}")
        except Exception as e:
            # 시스템 오류 → 로그 기록 + 사용자 안내
            logger.exception("시스템 오류 발생")
            messagebox.showerror("시스템 오류",
                "계산 중 오류가 발생했습니다.\n로그 파일을 확인하세요.")
```

---

### 4. 환율 시나리오 동적 설정

**현재 문제:**
```python
# 하드코딩된 환율 시나리오 (±50원 고정)
rates_to_calculate = {
    f"{base_rate - 50:.0f} 원": base_rate - 50,
    f"{base_rate:.0f} 원": base_rate,
    f"{base_rate + 50:.0f} 원": base_rate + 50
}
```

**개선 방안:**
```python
# config.py
class Config:
    """애플리케이션 설정"""
    # 환율 시나리오 설정
    EXCHANGE_RATE_SCENARIOS = [
        {"label": "낮은 환율", "offset": -50},
        {"label": "기준 환율", "offset": 0},
        {"label": "높은 환율", "offset": +50},
    ]

    @classmethod
    def load_from_file(cls, config_file="config.json"):
        """설정 파일에서 로드"""
        if Path(config_file).exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                cls.EXCHANGE_RATE_SCENARIOS = config_data.get(
                    "exchange_scenarios", cls.EXCHANGE_RATE_SCENARIOS
                )

# services/calculator.py
def generate_scenarios(base_rate: float) -> list:
    """동적으로 환율 시나리오 생성"""
    scenarios = []
    for scenario in Config.EXCHANGE_RATE_SCENARIOS:
        rate = base_rate + scenario["offset"]
        scenarios.append({
            "label": f"{scenario['label']} ({rate:.0f}원)",
            "rate": rate
        })
    return scenarios
```

**config.json 예시:**
```json
{
  "exchange_scenarios": [
    {"label": "최저 환율", "offset": -100},
    {"label": "낮은 환율", "offset": -50},
    {"label": "기준 환율", "offset": 0},
    {"label": "높은 환율", "offset": 50},
    {"label": "최고 환율", "offset": 100}
  ],
  "default_values": {
    "exchange_rate": 1150,
    "weaving_fee": 450,
    "dyeing_fee": 1900
  }
}
```

---

## 🟡 Important (중간 우선순위)

### 5. 데이터 검증 로직 중앙화

**현재 문제:**
- 검증 로직이 UI와 계산 로직에 분산됨
- 중복된 검증 코드
- 일관성 없는 에러 메시지

**개선 방안:**
```python
# services/validator.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ValidationError:
    field: str
    message: str

class InputValidator:
    """입력값 검증 클래스"""

    @staticmethod
    def validate_fabric_input(fabric_width: float,
                             weight_value: float,
                             weight_unit: str) -> List[ValidationError]:
        """원단 입력 검증"""
        errors = []

        if weight_value <= 0:
            errors.append(ValidationError(
                "weight_value",
                "가공 중량 값은 0보다 커야 합니다."
            ))

        if weight_unit == "g/sqm" and fabric_width <= 0:
            errors.append(ValidationError(
                "fabric_width",
                "g/sqm 단위 선택 시 가공 전폭은 0보다 커야 합니다."
            ))

        return errors

    @staticmethod
    def validate_yarn_ratios(yarns_data: list) -> List[ValidationError]:
        """원사 비율 검증"""
        errors = []

        if not yarns_data:
            errors.append(ValidationError(
                "yarns",
                "최소 한 개의 원사 정보가 필요합니다."
            ))
            return errors

        total_ratio = sum(y["ratio_pct"] for y in yarns_data)

        if len(yarns_data) > 1 and abs(total_ratio - 100.0) > 1e-3:
            errors.append(ValidationError(
                "yarn_ratios",
                f"모든 원사 비율의 합이 100%여야 합니다. "
                f"(현재 합계: {total_ratio:.2f}%)"
            ))

        return errors

    @staticmethod
    def validate_all(inputs: dict) -> List[ValidationError]:
        """전체 입력 검증"""
        errors = []
        errors.extend(InputValidator.validate_fabric_input(
            inputs["fabric_width_inch"],
            inputs["proc_weight_input_value"],
            inputs["proc_weight_input_unit"]
        ))
        errors.extend(InputValidator.validate_yarn_ratios(
            inputs["yarns_data"]
        ))
        return errors
```

---

### 6. 단위 변환 로직 분리

**현재 문제:**
- 단위 변환 로직이 계산 코드에 섞여있음
- 재사용 불가능
- 테스트 어려움

**개선 방안:**
```python
# services/converter.py
from models.constants import UnitConversion

class UnitConverter:
    """단위 변환 유틸리티"""

    @staticmethod
    def weight_to_gyd(value: float, unit: str, width_inch: float = None) -> float:
        """원단 중량을 g/yd로 변환"""
        if unit == "g/yd":
            return value
        elif unit == "g/sqm":
            if width_inch is None or width_inch <= 0:
                raise ValueError("g/sqm 변환을 위해 가공 전폭이 필요합니다.")
            return value * width_inch * UnitConversion.GSM_TO_GYD_PER_INCH
        else:
            raise ValueError(f"지원하지 않는 중량 단위: {unit}")

    @staticmethod
    def price_to_usd_per_kg(price: float,
                           currency: str,
                           unit: str,
                           exchange_rate: float) -> float:
        """원사 단가를 $/kg로 변환"""
        # 1단계: 통화 변환
        price_usd = price
        if currency == "원화":
            if exchange_rate <= 0:
                raise ValueError("유효하지 않은 환율입니다.")
            price_usd = price / exchange_rate

        # 2단계: 단위 변환
        if unit == "lb":
            return price_usd * UnitConversion.KG_TO_LB
        elif unit == "kg":
            return price_usd
        else:
            raise ValueError(f"지원하지 않는 중량 단위: {unit}")

class CurrencyConverter:
    """통화 변환 유틸리티"""

    @staticmethod
    def to_usd(amount: float, currency: str, exchange_rate: float) -> float:
        """금액을 USD로 변환"""
        if currency == "$":
            return amount
        elif currency == "원화":
            if exchange_rate <= 0:
                raise ValueError("유효하지 않은 환율입니다.")
            return amount / exchange_rate
        else:
            raise ValueError(f"지원하지 않는 통화: {currency}")
```

**사용 예시:**
```python
# 변환 전 (복잡한 로직이 계산 함수 안에)
proc_weight_gyd = proc_weight_input_val
if proc_weight_input_unit == "g/sqm":
    if fabric_width_inch <= 0:
        raise ValueError("...")
    proc_weight_gyd = proc_weight_input_val * fabric_width_inch * 0.02322576

# 변환 후 (명확하고 재사용 가능)
proc_weight_gyd = UnitConverter.weight_to_gyd(
    proc_weight_input_val,
    proc_weight_input_unit,
    fabric_width_inch
)
```

---

### 7. 데이터 클래스 도입

**현재 문제:**
- 딕셔너리 기반 데이터 전달 → 타입 안정성 부족
- 키 오타 가능성
- IDE 자동완성 불가

**개선 방안:**
```python
# models/yarn.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Yarn:
    """원사 데이터 클래스"""
    id: int
    yarn_type: str
    denier: float
    filament: float
    processing_type: str
    luster: str
    recycle_status: str
    price_value: float
    price_currency: str
    price_unit: str
    quality: str
    created_at: datetime
    updated_at: datetime

    def get_display_name(self) -> str:
        """표시용 이름 생성"""
        desc = f"{self.yarn_type}({self.recycle_status})"
        if self.denier or self.filament:
            desc += f" {int(self.denier)}D/{int(self.filament)}F"
        desc += f" {self.processing_type} {self.luster}"
        desc += f" ({self.quality})"
        return desc.strip()

    @classmethod
    def from_dict(cls, data: dict) -> 'Yarn':
        """딕셔너리에서 생성"""
        return cls(
            id=data["id"],
            yarn_type=data["yarn_type"],
            denier=data["denier"],
            filament=data["filament"],
            processing_type=data["processing_type"],
            luster=data["luster"],
            recycle_status=data["recycle_status"],
            price_value=data["price_value"],
            price_currency=data["price_currency"],
            price_unit=data["price_unit"],
            quality=data["quality"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "yarn_type": self.yarn_type,
            "denier": self.denier,
            "filament": self.filament,
            "processing_type": self.processing_type,
            "luster": self.luster,
            "recycle_status": self.recycle_status,
            "price_value": self.price_value,
            "price_currency": self.price_currency,
            "price_unit": self.price_unit,
            "quality": self.quality,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

# models/calculation.py
@dataclass
class YarnCostComponent:
    """원사 비용 구성 요소"""
    yarn_id: int
    name: str
    ratio_pct: float
    cost_if_100pct_usd_yd: float
    cost_contrib_usd_yd: float

@dataclass
class CalculationResult:
    """계산 결과"""
    net_cost_usd_yd: float
    margin_pct: float
    total_yarn_cost_usd_yd: float
    cost_weaving_usd_yd: float
    cost_dyeing_usd_yd: float
    total_other_costs_usd_yd: float
    yarn_components: list[YarnCostComponent]

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (Excel 출력용)"""
        return {
            "net_cost_usd_yd": self.net_cost_usd_yd,
            "margin_pct": self.margin_pct,
            "details": {
                "total_yarn_cost_usd_yd": self.total_yarn_cost_usd_yd,
                "cost_weaving_usd_yd": self.cost_weaving_usd_yd,
                "cost_dyeing_usd_yd": self.cost_dyeing_usd_yd,
                "total_other_costs_usd_yd": self.total_other_costs_usd_yd,
                "yarn_cost_components_usd_yd": [
                    {
                        "name": c.name,
                        "ratio": c.ratio_pct,
                        "cost_contrib_usd_yd": c.cost_contrib_usd_yd
                    }
                    for c in self.yarn_components
                ]
            }
        }
```

---

### 8. Excel 출력 로직 개선

**현재 문제:**
- 하드코딩된 셀 주소 (C26, D25 등)
- 주석 처리된 코드 다수
- 디버그 print 문 과다

**개선 방안:**
```python
# utils/excel_exporter.py
from dataclasses import dataclass
from openpyxl import load_workbook
from pathlib import Path

@dataclass
class ExcelCellMapping:
    """Excel 셀 매핑 정의"""
    # 기본 정보
    ITEM_NAME = "B2"
    FABRIC_WIDTH = "D2"
    PROC_WEIGHT_VALUE = "B3"
    PROC_WEIGHT_UNIT = "D3"

    # 원사 정보
    YARN1_NAME = "B7"
    YARN1_RATIO = "D7"
    YARN1_PRICE = "F7"
    YARN1_UNIT = "H7"

    YARN2_NAME = "B8"
    YARN2_RATIO = "D8"
    YARN2_PRICE = "F8"
    YARN2_UNIT = "H8"

    # 손실률
    WEAVING_LOSS = "B11"
    DYEING_LOSS = "B12"
    DELAY_LOSS = "B13"

    # 가공비
    WEAVING_FEE = "D11"
    DYEING_FEE = "D12"
    EXCHANGE_RATE = "D13"

    # 기타 비용
    OTHER_COST1_DESC = "B23"
    OTHER_COST1_AMOUNT = "D23"

    # 결과
    NET_COST_BASE = "C27"
    SELLING_PRICE = "C31"

class ExcelExporter:
    """Excel 출력 클래스"""

    def __init__(self, template_file: str = "FabricCost_Form.xlsx"):
        self.template_file = Path(template_file)
        self.mapping = ExcelCellMapping()

    def export(self,
               output_file: str,
               inputs: dict,
               results: dict) -> bool:
        """계산 결과를 Excel로 출력"""
        try:
            # 템플릿 복사
            wb = load_workbook(self.template_file)
            sheet = wb.active

            # 데이터 입력
            self._fill_basic_info(sheet, inputs)
            self._fill_yarn_info(sheet, inputs)
            self._fill_costs(sheet, inputs)
            self._fill_results(sheet, results)

            # 저장
            wb.save(output_file)
            logger.info(f"Excel 저장 완료: {output_file}")
            return True

        except FileNotFoundError:
            logger.error(f"템플릿 파일 없음: {self.template_file}")
            return False
        except Exception as e:
            logger.exception(f"Excel 출력 오류: {e}")
            return False

    def _fill_basic_info(self, sheet, inputs):
        """기본 정보 입력"""
        sheet[self.mapping.ITEM_NAME] = inputs.get("item_name", "")
        sheet[self.mapping.FABRIC_WIDTH] = inputs.get("fabric_width_inch", 0)
        sheet[self.mapping.PROC_WEIGHT_VALUE] = inputs.get("proc_weight_input_value", 0)

    def _fill_yarn_info(self, sheet, inputs):
        """원사 정보 입력"""
        yarns = inputs.get("yarns_data", [])

        # 동적 셀 매핑 (최대 3개 원사 지원)
        yarn_rows = [7, 8, 9]

        for idx, yarn in enumerate(yarns[:3]):
            row = yarn_rows[idx]
            sheet[f"B{row}"] = yarn.get("display_name_in_combobox", "")
            sheet[f"D{row}"] = yarn.get("ratio_pct", 0)
            sheet[f"F{row}"] = yarn.get("price_val", 0)
            sheet[f"H{row}"] = f"{yarn.get('price_currency', '$')} / {yarn.get('price_unit', 'lb')}"

    def _fill_costs(self, sheet, inputs):
        """비용 정보 입력"""
        sheet[self.mapping.WEAVING_LOSS] = inputs.get("weaving_loss_pct", 0)
        sheet[self.mapping.DYEING_LOSS] = inputs.get("dyeing_loss_pct", 0)
        sheet[self.mapping.DELAY_LOSS] = inputs.get("delay_loss_pct", 0)

        sheet[self.mapping.WEAVING_FEE] = inputs.get("weaving_fee_krw_kg", 0)
        sheet[self.mapping.DYEING_FEE] = inputs.get("dyeing_fee_krw_kg", 0)
        sheet[self.mapping.EXCHANGE_RATE] = inputs.get("base_exchange_rate_krw_usd", 0)

    def _fill_results(self, sheet, results):
        """계산 결과 입력"""
        sheet[self.mapping.NET_COST_BASE] = results.get("net_cost_usd_yd", 0)
        # ... 나머지 결과 입력
```

---

## 🟢 Recommended (낮은 우선순위)

### 9. 테스트 코드 작성

**개선 방안:**
```python
# tests/test_converter.py
import pytest
from services.converter import UnitConverter, CurrencyConverter

class TestUnitConverter:
    def test_weight_gyd_to_gyd(self):
        """g/yd → g/yd 변환 (변환 없음)"""
        result = UnitConverter.weight_to_gyd(200, "g/yd")
        assert result == 200

    def test_weight_gsm_to_gyd(self):
        """g/sqm → g/yd 변환"""
        result = UnitConverter.weight_to_gyd(205, "g/sqm", width_inch=60)
        expected = 205 * 60 * 0.02322576
        assert abs(result - expected) < 0.01

    def test_price_usd_lb_to_usd_kg(self):
        """$/lb → $/kg 변환"""
        result = UnitConverter.price_to_usd_per_kg(
            price=0.8,
            currency="$",
            unit="lb",
            exchange_rate=1150
        )
        expected = 0.8 * 2.20462
        assert abs(result - expected) < 0.01

class TestCurrencyConverter:
    def test_krw_to_usd(self):
        """원화 → USD 변환"""
        result = CurrencyConverter.to_usd(1150, "원화", 1150)
        assert result == 1.0

    def test_invalid_exchange_rate(self):
        """잘못된 환율 처리"""
        with pytest.raises(ValueError):
            CurrencyConverter.to_usd(1000, "원화", 0)

# tests/test_calculator.py
from services.calculator import CostCalculator

class TestCostCalculator:
    def test_single_scenario_calculation(self):
        """단일 시나리오 계산 테스트"""
        calculator = CostCalculator()
        inputs = {
            "fabric_width_inch": 60,
            "proc_weight_input_value": 205,
            "proc_weight_input_unit": "g/yd",
            "yarns_data": [{
                "id": 1,
                "price_val": 0.8,
                "price_currency": "$",
                "price_unit": "lb",
                "quality": "일반",
                "ratio_pct": 100.0,
                "display_name_in_combobox": "Polyester"
            }],
            "weaving_loss_pct": 2,
            "dyeing_loss_pct": 4,
            "delay_loss_pct": 6,
            "weaving_fee_krw_kg": 450,
            "dyeing_fee_krw_kg": 1900,
            "base_exchange_rate_krw_usd": 1150,
            "other_costs": [],
            "selling_price_usd_yd": 1.50
        }

        result = calculator.calculate_single_scenario(inputs, 1150)

        assert result is not None
        assert result.net_cost_usd_yd > 0
        assert -100 < result.margin_pct < 100
```

---

### 10. 설정 파일 기반 관리

**개선 방안:**
```python
# config.py
import json
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class AppConfig:
    """애플리케이션 설정"""
    # 기본값
    default_exchange_rate: float = 1150
    default_weaving_fee: float = 450
    default_dyeing_fee: float = 1900

    # 환율 시나리오
    exchange_rate_scenarios: list = None

    # 파일 경로
    yarn_db_file: str = "yarn_db.json"
    history_db_file: str = "calculation_history.db"
    excel_template_file: str = "FabricCost_Form.xlsx"

    # UI 설정
    window_width: int = 1160
    window_height: int = 850

    def __post_init__(self):
        if self.exchange_rate_scenarios is None:
            self.exchange_rate_scenarios = [
                {"label": "낮은 환율", "offset": -50},
                {"label": "기준 환율", "offset": 0},
                {"label": "높은 환율", "offset": +50}
            ]

    @classmethod
    def load(cls, config_file: str = "config.json") -> 'AppConfig':
        """설정 파일에서 로드"""
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls(**data)
        return cls()

    def save(self, config_file: str = "config.json"):
        """설정 파일에 저장"""
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)
```

---

## 구현 우선순위 로드맵

### Phase 1: 기초 정리 (1-2일)
1. ✅ constants.py 생성 및 매직 넘버 제거
2. ✅ logger.py 생성 및 로깅 시스템 도입
3. ✅ config.py 생성 및 설정 파일 관리

### Phase 2: 비즈니스 로직 분리 (2-3일)
4. ✅ converter.py 생성 (단위/통화 변환)
5. ✅ validator.py 생성 (입력 검증)
6. ✅ calculator.py 생성 (계산 로직)

### Phase 3: 데이터 레이어 분리 (2일)
7. ✅ models/yarn.py 생성 (데이터 클래스)
8. ✅ data/yarn_repository.py 생성
9. ✅ data/history_repository.py 생성

### Phase 4: UI 레이어 분리 (3일)
10. ✅ ui/main_window.py 생성
11. ✅ ui/yarn_manager.py 생성
12. ✅ ui/history_window.py 생성

### Phase 5: 테스트 및 문서화 (2일)
13. ✅ 단위 테스트 작성
14. ✅ 통합 테스트 작성
15. ✅ API 문서화

---

## 예상 효과

### 코드 품질
- 🎯 **유지보수성**: 70% 향상 (모듈화로 인한 책임 분리)
- 🎯 **테스트 가능성**: 0% → 80% (현재 테스트 불가 → 단위 테스트 가능)
- 🎯 **가독성**: 60% 향상 (1303줄 → 각 모듈 100-200줄)

### 개발 생산성
- 🎯 **버그 추적**: 2배 빠름 (로깅 시스템)
- 🎯 **신규 기능 추가**: 3배 빠름 (명확한 레이어 분리)
- 🎯 **협업**: 충돌 감소 (모듈별 작업 가능)

### 확장성
- 🎯 **새로운 단위 추가**: 5분 (UnitConverter 수정)
- 🎯 **새로운 원사 속성**: 10분 (Yarn 클래스 수정)
- 🎯 **새로운 계산 로직**: 30분 (CostCalculator 확장)

---

## 시작하기 좋은 개선 작업

### 빠른 개선 (1시간 이내)
1. **constants.py 생성**: 매직 넘버만 분리
2. **print → logging 변환**: 기존 print 문을 logger로 교체
3. **환율 시나리오 설정화**: ±50 하드코딩 제거

### 중간 개선 (반나절)
4. **UnitConverter 클래스**: 단위 변환 로직만 분리
5. **InputValidator 클래스**: 검증 로직만 분리
6. **Yarn 데이터 클래스**: 딕셔너리 → dataclass

### 완전한 리팩토링 (1-2주)
7. **전체 모듈화**: 위 제안된 구조대로 완전 분리
8. **테스트 코드 작성**: 80% 이상 커버리지
9. **문서화**: API 문서, 개발자 가이드

---

## 참고사항

- 리팩토링 전에 현재 동작하는 코드를 백업하세요
- 단계별로 진행하며 각 단계마다 테스트하세요
- 기존 기능 유지를 최우선으로 하세요
- Git을 사용하여 각 개선 단계를 커밋하세요
