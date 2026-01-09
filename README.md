# 원단 원가 계산기 (Fabric Cost Calculator)

원사 배합, 가공비, 손실률 등을 고려하여 원단의 NET 단가를 계산하고 Excel로 출력하는 Tkinter GUI 애플리케이션입니다.

## 🎯 주요 기능

- ✅ 원사 혼용 계산 (다중 원사 비율 지원)
- ✅ 다중 환율 시나리오 계산 (기준±50원)
- ✅ 손실률 적용 (제직, 염색, 지연)
- ✅ 원사 DB 관리 (JSON 기반)
- ✅ 계산 이력 저장/조회 (SQLite)
- ✅ Excel 템플릿 기반 결과 출력
- ✅ 로깅 시스템

## 📦 설치 및 실행

### 요구사항
```
Python 3.8+
tkinter (Python 표준 라이브러리)
openpyxl
```

### 설치
```bash
pip install openpyxl
```

### 실행

#### Windows 사용자 (배치 파일)

더블 클릭으로 바로 실행하세요:

- `run_simple.bat` - GUI 바로 실행 (가장 간단)
- `run.bat` - 가상환경 선택 후 GUI 실행
- `run_examples.bat` - 사용 예제 실행 (메뉴 선택)
- `install.bat` - 필수 라이브러리 설치

**최초 설치 시:**
1. `install.bat` 더블 클릭 → 라이브러리 설치
2. `run_simple.bat` 더블 클릭 → 프로그램 실행

#### Linux/Mac 사용자 (터미널)

```bash
# 1. 라이브러리 설치
pip install openpyxl

# 2. 프로그램 실행
python main.py                # 메인 GUI
python example_usage.py       # CLI 예제
```

#### 레거시 실행 (원본 코드)

```bash
python calculate_net_price.py
```

## 🏗️ 프로젝트 구조

### 모듈화된 구조 (신규)

```
costNETprice/
├── models/                 # 데이터 모델
│   ├── constants.py        # 상수 정의 (매직 넘버 제거)
│   └── yarn.py            # Yarn, CalculationResult 데이터 클래스
│
├── services/              # 비즈니스 로직
│   ├── converter.py       # 단위/통화 변환
│   ├── validator.py       # 입력 검증
│   └── calculator.py      # 원가 계산 엔진
│
├── data/                  # 데이터 접근 계층
│   ├── yarn_repository.py     # yarn_db.json 관리
│   └── history_repository.py  # calculation_history.db 관리
│
├── ui/                    # UI 레이어 (향후 분리)
│   └── base_window.py     # 기본 윈도우 클래스
│
├── utils/                 # 유틸리티
│   ├── logger.py          # 로깅 시스템
│   └── excel_exporter.py  # Excel 출력
│
├── config.py              # 설정 관리
├── main.py                # 진입점 (새 모듈 기반)
├── example_usage.py       # 사용 예제
└── calculate_net_price.py # 레거시 코드 (원본)
```

## 💡 새 모듈 사용 예제

### 1. 기본 계산

```python
from services.calculator import CostCalculator
from services.validator import InputValidator

# 입력 데이터
inputs = {
    "item_name": "CPEM(60-147M)",
    "fabric_width_inch": 60,
    "proc_weight_input_value": 205,
    "proc_weight_input_unit": "g/yd",
    "yarns_data": [
        {
            "id": 1,
            "price_val": 0.80,
            "price_currency": "$",
            "price_unit": "lb",
            "ratio_pct": 100.0,
            "display_name_in_combobox": "Polyester(virgin) 150D/72F DTY SD"
        }
    ],
    "weaving_loss_pct": 2,
    "dyeing_loss_pct": 4,
    "delay_loss_pct": 6,
    "weaving_fee_krw_kg": 450,
    "dyeing_fee_krw_kg": 1900,
    "base_exchange_rate_krw_usd": 1150,
    "other_costs": [],
    "selling_price_usd_yd": 1.50
}

# 입력 검증
validation = InputValidator.validate_all_inputs(inputs)
if not validation.is_valid():
    print(validation.get_first_error())
    exit(1)

# 계산 수행
calculator = CostCalculator()
result = calculator.calculate_single_scenario(inputs, 1150)

print(f"NET 단가: ${result.net_cost_usd_yd:.2f}/yd")
print(f"마진: {result.margin_pct:.2f}%")
```

### 2. 다중 환율 시나리오

```python
from config import get_config

# 설정 로드
config = get_config()
scenarios = config.get_exchange_scenarios(1150)
# [{"label": "낮은 환율 (1100원)", "rate": 1100}, ...]

# 다중 계산
results = calculator.calculate_multiple_scenarios(inputs, scenarios)
for item in results:
    if item["success"]:
        res = item["result"]
        print(f"{item['scenario']}: ${res.net_cost_usd_yd:.2f}/yd")
```

### 3. 원사 관리

```python
from data.yarn_repository import YarnRepository
from models.yarn import Yarn

repo = YarnRepository()

# 전체 조회
yarns = repo.get_all()

# 검색
results = repo.search("Polyester")

# 추가
new_yarn = Yarn(
    id=0,  # 자동 할당
    yarn_type="Spandex",
    denier=40,
    filament=1,
    processing_type="FY",
    luster="BRT",
    recycle_status="virgin",
    price_value=5.50,
    price_currency="$",
    price_unit="lb",
    quality="AAA",
    created_at="",
    updated_at=""
)
repo.add(new_yarn)
```

### 4. 계산 이력 관리

```python
from data.history_repository import HistoryRepository

repo = HistoryRepository()

# 이력 저장
history_id = repo.add(
    item_name="CPEM(60-147M)",
    inputs=inputs,
    base_rate_results=result.to_dict()
)

# 이력 조회
summary = repo.get_summary_list(limit=10)
detail = repo.get_by_id(history_id)
```

### 5. Excel 출력

```python
from utils.excel_exporter import ExcelExporter, ExcelExportHelper

exporter = ExcelExporter("FabricCost_Form.xlsx")
output_file = ExcelExportHelper.generate_output_filename("CPEM")

exporter.export(
    output_file,
    inputs,
    result.to_dict()
)
```

## 🔧 설정 관리

### config.json 파일
```json
{
  "default_exchange_rate": 1150,
  "default_weaving_fee": 450,
  "default_dyeing_fee": 1900,
  "exchange_rate_scenarios": [
    {"label": "최저 환율", "offset": -100},
    {"label": "낮은 환율", "offset": -50},
    {"label": "기준 환율", "offset": 0},
    {"label": "높은 환율", "offset": 50},
    {"label": "최고 환율", "offset": 100}
  ]
}
```

### Python에서 설정 사용
```python
from config import get_config

config = get_config()
print(config.default_exchange_rate)  # 1150

# 환율 시나리오 추가
config.add_exchange_scenario("특별 환율", 75)
config.save()
```

## 📊 데이터 파일

- `yarn_db.json`: 원사 마스터 데이터 (JSON)
- `calculation_history.db`: 계산 이력 (SQLite)
- `FabricCost_Form.xlsx`: Excel 출력 템플릿
- `config.json`: 애플리케이션 설정 (선택)
- `app.log`: 로그 파일

## 🚀 개선 사항 (v2.0)

### Phase 1: 기초 모듈 구조
- ✅ 매직 넘버 제거 → `models/constants.py`
- ✅ 로깅 시스템 도입 → `utils/logger.py`
- ✅ 설정 파일 관리 → `config.py`
- ✅ 단위/통화 변환 유틸리티 → `services/converter.py`

### Phase 2: 비즈니스 로직 분리
- ✅ 입력 검증 중앙화 → `services/validator.py`
- ✅ 계산 로직 분리 → `services/calculator.py`
- ✅ 데이터 클래스 도입 → `models/yarn.py`
- ✅ 저장소 패턴 → `data/yarn_repository.py`, `history_repository.py`

### Phase 3: 통합 및 문서화
- ✅ Excel 출력 모듈화 → `utils/excel_exporter.py`
- ✅ 사용 예제 작성 → `example_usage.py`
- ✅ 문서화 → `README.md`, `CLAUDE.md`

### 향후 계획 (Phase 4+)
- ⏳ UI 레이어 완전 분리
- ⏳ 단위 테스트 추가 (pytest)
- ⏳ 설정 GUI 추가
- ⏳ 데이터베이스 백업/복원 기능

## 📈 코드 품질 개선

### Before (원본)
```python
# 하드코딩된 매직 넘버
proc_weight_gyd = value * width * 0.02322576
yarn_price_kg = price * 2.20462

# 37개의 print 문
print(f"DEBUG: ...")

# 28개의 messagebox
messagebox.showerror("오류", "...")

# 1303줄의 단일 파일
# 테스트 불가능
```

### After (모듈화)
```python
# 명확한 상수
from models.constants import UnitConversion
proc_weight_gyd = value * width * UnitConversion.GSM_TO_GYD_PER_INCH
yarn_price_kg = price * UnitConversion.KG_TO_LB

# 로깅 시스템
logger.debug("상세 로그")
logger.error("오류 발생")

# 검증 로직 분리
validation = InputValidator.validate_all_inputs(inputs)

# 모듈별 100-400줄
# 단위 테스트 가능
# 재사용 가능
```

## 📝 로깅

로그는 `app.log` 파일에 기록됩니다.

```python
from utils.logger import get_logger

logger = get_logger(__name__)
logger.info("정보 메시지")
logger.error("오류 메시지")
logger.debug("디버그 메시지")
```

## 🐛 문제 해결

### Excel 저장 시 MergedCell 오류
- 템플릿 파일의 병합된 셀에 값을 쓰려고 할 때 발생
- 현재는 무시하고 저장 (파일은 정상 생성됨)

### 원사 DB 초기화
```python
from data.yarn_repository import YarnRepository
repo = YarnRepository()  # 자동으로 기본 원사 4개 생성
```

### 설정 파일 재생성
```python
from config import AppConfig
config = AppConfig()
config.save("config.json")
```

## 📄 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.

## 🤝 기여

이 프로젝트는 모듈화 리팩토링을 통해 개선되었습니다.

- 원본 코드: `calculate_net_price.py` (레거시)
- 새 구조: 모듈화된 디렉토리 구조

## 📞 지원

문제가 발생하면 `app.log` 파일을 확인하세요.
