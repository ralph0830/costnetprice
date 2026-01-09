"""
상수 정의 모듈

원가 계산기에서 사용하는 모든 상수를 정의합니다.
매직 넘버를 제거하고 의미있는 이름으로 관리합니다.
"""


class UnitConversion:
    """단위 변환 상수"""

    # 중량 변환
    LB_TO_KG = 0.453592  # 파운드(lb)를 킬로그램(kg)으로
    KG_TO_LB = 2.20462   # 킬로그램(kg)을 파운드(lb)로

    # 길이 변환
    YD_TO_M = 0.9144     # 야드(yd)를 미터(m)로
    M_TO_YD = 1.09361    # 미터(m)를 야드(yd)로
    INCH_TO_CM = 2.54    # 인치(inch)를 센티미터(cm)로

    # 원단 중량 변환
    GSM_TO_GYD_PER_INCH = 0.02322576  # g/sqm을 g/yd로 변환 (inch당)
    G_TO_KG = 0.001      # 그램(g)을 킬로그램(kg)으로


class DefaultValues:
    """기본값 설정"""

    # 환율 및 통화
    EXCHANGE_RATE_KRW_USD = 1150  # 기본 환율 (원/$)
    EXCHANGE_RATE_VARIANCE = 50   # 환율 시나리오 변동폭 (±50원)

    # 가공비 (원화/kg 기준)
    WEAVING_FEE_KRW_KG = 450   # 제직료
    DYEING_FEE_KRW_KG = 1900   # 염색료

    # 손실률 (%)
    WEAVING_LOSS_PCT = 2   # 제직 Loss
    DYEING_LOSS_PCT = 4    # 염색 Loss
    DELAY_LOSS_PCT = 6     # 지연 Loss

    # 원단 기본값
    FABRIC_WIDTH_INCH = 60        # 가공 전폭 (inch)
    PROC_WEIGHT_VALUE = 205       # 가공 중량 값
    PROC_WEIGHT_UNIT = "g/yd"     # 가공 중량 단위

    # 기타
    SELLING_PRICE_USD_YD = 1.50   # 수주단가 ($/yd)
    ITEM_NAME = "CPEM(60-147M)"   # 아이템 이름


class ValidationRules:
    """검증 규칙 상수"""

    # 최소값
    MIN_FABRIC_WIDTH = 0.01       # 최소 원단 전폭 (inch)
    MIN_WEIGHT_VALUE = 0.01       # 최소 중량 값
    MIN_EXCHANGE_RATE = 100       # 최소 환율
    MIN_LOSS_PCT = 0              # 최소 손실률 (%)
    MIN_PRICE = 0                 # 최소 단가

    # 최대값
    MAX_YARN_RATIO_SUM = 100.0    # 원사 비율 합계 (%)
    MAX_YARN_RATIO_TOLERANCE = 1e-3  # 100% 검증 허용 오차

    # 기타
    ZERO_TOLERANCE = 1e-9         # 0 비교 허용 오차 (부동소수점)


class YarnAttributes:
    """원사 속성 옵션"""

    # 사종 (Yarn Type)
    YARN_TYPES = [
        "Polyester",
        "Spandex",
        "Nylon",
        "Cotton",
        "Rayon",
        "Tencel",
        "Modal",
        "Acetate",
        "Linen",
        "Wool",
        "Custom"
    ]

    # 사가공 (Processing Type)
    PROCESSING_TYPES = [
        "DTY",  # Draw Textured Yarn
        "FY",   # Filament Yarn
        "ATY",  # Air Textured Yarn
        "ITY",  # Intermingled Textured Yarn
        "Spun", # Spun Yarn
        "FDY",  # Fully Drawn Yarn
        "POY",  # Partially Oriented Yarn
        "N/A"
    ]

    # 광택 (Luster)
    LUSTER_TYPES = [
        "SD",    # Semi Dull
        "BRT",   # Bright
        "FD",    # Full Dull
        "CDP",   # Cationic Dyeable
        "Matte",
        "N/A"
    ]

    # Recycle 여부
    RECYCLE_STATUS = [
        "virgin",
        "recycled",
        "N/A"
    ]

    # 품질 등급
    QUALITY_GRADES = [
        "일반",
        "AAA"
    ]


class CurrencyUnits:
    """통화 및 단위 옵션"""

    # 통화
    CURRENCIES = ["$", "원화"]
    CURRENCY_USD = "$"
    CURRENCY_KRW = "원화"

    # 중량 단위
    WEIGHT_UNITS = ["lb", "kg"]
    UNIT_LB = "lb"
    UNIT_KG = "kg"

    # 원단 중량 단위
    FABRIC_WEIGHT_UNITS = ["g/yd", "g/sqm"]
    UNIT_GYD = "g/yd"
    UNIT_GSQM = "g/sqm"


class FileNames:
    """파일명 상수"""

    # 데이터 파일
    YARN_DB_JSON = "yarn_db.json"
    HISTORY_DB = "calculation_history.db"

    # Excel 관련
    EXCEL_TEMPLATE = "FabricCost_Form.xlsx"
    EXCEL_OUTPUT_PREFIX = "원가계산서"

    # 로그 파일
    LOG_FILE = "app.log"

    # 설정 파일
    CONFIG_FILE = "config.json"


class UIConfig:
    """UI 설정 상수"""

    # 메인 윈도우
    MAIN_WINDOW_WIDTH = 1160
    MAIN_WINDOW_HEIGHT = 850
    MAIN_WINDOW_TITLE = "원단 원가 계산기"

    # 원사 관리 윈도우
    YARN_MANAGER_WIDTH = 950
    YARN_MANAGER_HEIGHT = 700
    YARN_MANAGER_TITLE = "원사 DB 관리 (JSON)"

    # 히스토리 윈도우
    HISTORY_WINDOW_WIDTH = 1000
    HISTORY_WINDOW_HEIGHT = 700
    HISTORY_WINDOW_TITLE = "원가 계산 History"

    # 색상 테마 (메인 - 그린)
    THEME_BG_COLOR = "#E8F5E9"
    THEME_FG_COLOR = "#004D40"
    THEME_BUTTON_COLOR = "#66BB6A"
    THEME_BUTTON_ACTIVE = "#4CAF50"
    THEME_HEADING_BG = "#A5D6A7"

    # 색상 테마 (원사 관리 - 블루)
    YARN_THEME_BG_COLOR = "#E1F5FE"
    YARN_THEME_FG_COLOR = "#01579B"
    YARN_THEME_BUTTON_COLOR = "#03A9F4"
    YARN_THEME_BUTTON_ACTIVE = "#0288D1"


class DatabaseConfig:
    """데이터베이스 설정 상수"""

    # 테이블명
    TABLE_CALCULATION_HISTORY = "calculation_history"

    # 컬럼명
    COL_ID = "id"
    COL_CALCULATION_DATE = "calculation_date"
    COL_ITEM_NAME = "item_name"
    COL_INPUTS_JSON = "inputs_json"
    COL_BASE_RATE_RESULTS_JSON = "base_rate_results_json"


class ExcelCellMapping:
    """Excel 셀 매핑 상수 (템플릿 기준)"""

    # 기본 정보
    ITEM_NAME = "B2"
    FABRIC_WIDTH = "D2"
    PROC_WEIGHT_VALUE = "B3"

    # 원사 정보 (최대 3개)
    YARN1_NAME = "B7"
    YARN1_RATIO = "D7"
    YARN1_PRICE = "F7"

    YARN2_NAME = "B8"
    YARN2_RATIO = "D8"
    YARN2_PRICE = "F8"

    YARN3_NAME = "B9"
    YARN3_RATIO = "D9"
    YARN3_PRICE = "F9"

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
    OTHER_COST2_DESC = "B24"
    OTHER_COST2_AMOUNT = "D24"
    OTHER_COST3_DESC = "B25"
    OTHER_COST3_AMOUNT = "D25"

    # 결과
    NET_COST_BASE = "C27"
    SELLING_PRICE = "C31"


class ErrorMessages:
    """에러 메시지 상수"""

    # 입력 검증
    ERR_WEIGHT_VALUE = "가공 중량 값은 0보다 커야 합니다."
    ERR_FABRIC_WIDTH = "g/sqm 단위 선택 시 가공 전폭은 0보다 커야 합니다."
    ERR_EXCHANGE_RATE = "기준환율은 0보다 커야 합니다."
    ERR_NO_YARN = "최소 한 개의 원사 정보가 필요합니다."
    ERR_YARN_NOT_SELECTED = "모든 원사 항목에서 원사를 선택해주세요."
    ERR_YARN_RATIO_ZERO = "다중 원사 사용 시, 각 원사의 비율은 0보다 커야 합니다."
    ERR_YARN_RATIO_SUM = "모든 원사 비율의 합이 100%여야 합니다. (현재 합계: {total:.2f}%)"

    # 계산 오류
    ERR_EXCHANGE_ZERO_YARN = "환율 오류(원사)."
    ERR_EXCHANGE_ZERO_PROCESS = "환율 오류(가공비)."
    ERR_EXCHANGE_ZERO_OTHER = "환율 오류(기타비용)."
    ERR_GSQM_CONVERSION = "g/sqm 변환을 위해 가공 전폭이 필요합니다."

    # 파일 오류
    ERR_JSON_SAVE = "원사 DB 파일 저장에 실패했습니다:\n{error}"
    ERR_HISTORY_SAVE = "계산 내역 저장 중 오류 발생:\n{error}"
    ERR_HISTORY_LOAD = "계산 내역 로드 중 오류 발생:\n{error}"
    ERR_TEMPLATE_NOT_FOUND = "템플릿 파일을 찾을 수 없습니다: {file}"

    # 일반 오류
    ERR_CALCULATION = "계산 중 오류가 발생했습니다."
    ERR_UNEXPECTED = "예상치 못한 오류가 발생했습니다."


# 기본 원사 데이터 (초기화용)
DEFAULT_YARNS = [
    {
        "id": 1,
        "yarn_type": "Polyester",
        "denier": 150,
        "filament": 72,
        "processing_type": "DTY",
        "luster": "SD",
        "recycle_status": "virgin",
        "price_value": 0.80,
        "price_currency": "$",
        "price_unit": "lb",
        "quality": "일반"
    },
    {
        "id": 2,
        "yarn_type": "Polyester",
        "denier": 75,
        "filament": 36,
        "processing_type": "DTY",
        "luster": "BRT",
        "recycle_status": "recycled",
        "price_value": 1.20,
        "price_currency": "$",
        "price_unit": "lb",
        "quality": "AAA"
    },
    {
        "id": 3,
        "yarn_type": "Nylon",
        "denier": 70,
        "filament": 68,
        "processing_type": "ATY",
        "luster": "SD",
        "recycle_status": "virgin",
        "price_value": 2500,
        "price_currency": "원화",
        "price_unit": "kg",
        "quality": "일반"
    },
    {
        "id": 4,
        "yarn_type": "Custom",
        "denier": 0,
        "filament": 0,
        "processing_type": "N/A",
        "luster": "N/A",
        "recycle_status": "N/A",
        "price_value": 0.80,
        "price_currency": "$",
        "price_unit": "lb",
        "quality": "일반"
    }
]
