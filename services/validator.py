"""
입력 검증 모듈

사용자 입력값의 유효성을 검증합니다.
UI와 비즈니스 로직에서 분산된 검증 코드를 중앙화합니다.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from models.constants import (
    ValidationRules,
    CurrencyUnits,
    ErrorMessages
)


@dataclass
class ValidationError:
    """검증 오류 정보"""
    field: str
    message: str
    value: Any = None

    def __str__(self):
        if self.value is not None:
            return f"{self.field}: {self.message} (입력값: {self.value})"
        return f"{self.field}: {self.message}"


class ValidationResult:
    """검증 결과"""

    def __init__(self):
        self.errors: List[ValidationError] = []

    def add_error(self, field: str, message: str, value: Any = None):
        """오류 추가"""
        self.errors.append(ValidationError(field, message, value))

    def is_valid(self) -> bool:
        """유효한지 확인"""
        return len(self.errors) == 0

    def get_error_messages(self) -> List[str]:
        """오류 메시지 목록 반환"""
        return [str(error) for error in self.errors]

    def get_first_error(self) -> Optional[str]:
        """첫 번째 오류 메시지 반환"""
        if self.errors:
            return str(self.errors[0])
        return None

    def __str__(self):
        if self.is_valid():
            return "검증 통과"
        return "\n".join(self.get_error_messages())


class InputValidator:
    """입력값 검증 클래스"""

    @staticmethod
    def validate_fabric_input(
        fabric_width: float,
        weight_value: float,
        weight_unit: str
    ) -> ValidationResult:
        """
        원단 입력값 검증

        Args:
            fabric_width: 가공 전폭 (inch)
            weight_value: 가공 중량 값
            weight_unit: 가공 중량 단위

        Returns:
            ValidationResult 객체
        """
        result = ValidationResult()

        # 중량 값 검증
        if weight_value <= ValidationRules.MIN_WEIGHT_VALUE:
            result.add_error(
                "weight_value",
                ErrorMessages.ERR_WEIGHT_VALUE,
                weight_value
            )

        # g/sqm 단위 사용 시 전폭 필수
        if weight_unit == CurrencyUnits.UNIT_GSQM:
            if fabric_width <= ValidationRules.MIN_FABRIC_WIDTH:
                result.add_error(
                    "fabric_width",
                    ErrorMessages.ERR_FABRIC_WIDTH,
                    fabric_width
                )

        return result

    @staticmethod
    def validate_exchange_rate(exchange_rate: float) -> ValidationResult:
        """
        환율 검증

        Args:
            exchange_rate: 환율 (원/$)

        Returns:
            ValidationResult 객체
        """
        result = ValidationResult()

        if exchange_rate <= ValidationRules.MIN_EXCHANGE_RATE:
            result.add_error(
                "exchange_rate",
                ErrorMessages.ERR_EXCHANGE_RATE,
                exchange_rate
            )

        return result

    @staticmethod
    def validate_yarn_data(yarns_data: List[Dict[str, Any]]) -> ValidationResult:
        """
        원사 데이터 검증

        Args:
            yarns_data: 원사 정보 리스트
                [{"id": 1, "price_val": 0.8, "ratio_pct": 100.0, ...}, ...]

        Returns:
            ValidationResult 객체
        """
        result = ValidationResult()

        # 원사 개수 검증
        if not yarns_data:
            result.add_error(
                "yarns",
                ErrorMessages.ERR_NO_YARN
            )
            return result

        # 각 원사 검증
        for idx, yarn in enumerate(yarns_data):
            # ID 검증
            yarn_id = yarn.get("id", 0)
            if not yarn_id or yarn_id == 0:
                result.add_error(
                    f"yarn[{idx}].id",
                    ErrorMessages.ERR_YARN_NOT_SELECTED,
                    yarn_id
                )

            # 비율 검증 (다중 원사인 경우)
            if len(yarns_data) > 1:
                ratio = yarn.get("ratio_pct", 0)
                if ratio <= 0:
                    result.add_error(
                        f"yarn[{idx}].ratio_pct",
                        ErrorMessages.ERR_YARN_RATIO_ZERO,
                        ratio
                    )

        # 비율 합계 검증 (다중 원사인 경우)
        if len(yarns_data) > 1:
            total_ratio = sum(yarn.get("ratio_pct", 0) for yarn in yarns_data)
            if abs(total_ratio - ValidationRules.MAX_YARN_RATIO_SUM) > ValidationRules.MAX_YARN_RATIO_TOLERANCE:
                result.add_error(
                    "yarn_ratios",
                    ErrorMessages.ERR_YARN_RATIO_SUM.format(total=total_ratio)
                )

        return result

    @staticmethod
    def validate_loss_percentages(
        weaving_loss: float,
        dyeing_loss: float,
        delay_loss: float
    ) -> ValidationResult:
        """
        손실률 검증

        Args:
            weaving_loss: 제직 손실률 (%)
            dyeing_loss: 염색 손실률 (%)
            delay_loss: 지연 손실률 (%)

        Returns:
            ValidationResult 객체
        """
        result = ValidationResult()

        if weaving_loss < ValidationRules.MIN_LOSS_PCT:
            result.add_error(
                "weaving_loss",
                f"제직 손실률은 {ValidationRules.MIN_LOSS_PCT}% 이상이어야 합니다.",
                weaving_loss
            )

        if dyeing_loss < ValidationRules.MIN_LOSS_PCT:
            result.add_error(
                "dyeing_loss",
                f"염색 손실률은 {ValidationRules.MIN_LOSS_PCT}% 이상이어야 합니다.",
                dyeing_loss
            )

        if delay_loss < ValidationRules.MIN_LOSS_PCT:
            result.add_error(
                "delay_loss",
                f"지연 손실률은 {ValidationRules.MIN_LOSS_PCT}% 이상이어야 합니다.",
                delay_loss
            )

        return result

    @staticmethod
    def validate_processing_fees(
        weaving_fee: float,
        dyeing_fee: float
    ) -> ValidationResult:
        """
        가공비 검증

        Args:
            weaving_fee: 제직료 (원화/kg)
            dyeing_fee: 염색료 (원화/kg)

        Returns:
            ValidationResult 객체
        """
        result = ValidationResult()

        if weaving_fee < ValidationRules.MIN_PRICE:
            result.add_error(
                "weaving_fee",
                f"제직료는 {ValidationRules.MIN_PRICE}원 이상이어야 합니다.",
                weaving_fee
            )

        if dyeing_fee < ValidationRules.MIN_PRICE:
            result.add_error(
                "dyeing_fee",
                f"염색료는 {ValidationRules.MIN_PRICE}원 이상이어야 합니다.",
                dyeing_fee
            )

        return result

    @staticmethod
    def validate_all_inputs(inputs: Dict[str, Any]) -> ValidationResult:
        """
        전체 입력값 통합 검증

        Args:
            inputs: 전체 입력 딕셔너리
                {
                    "fabric_width_inch": 60,
                    "proc_weight_input_value": 205,
                    "proc_weight_input_unit": "g/yd",
                    "yarns_data": [...],
                    "weaving_loss_pct": 2,
                    "dyeing_loss_pct": 4,
                    "delay_loss_pct": 6,
                    "weaving_fee_krw_kg": 450,
                    "dyeing_fee_krw_kg": 1900,
                    "base_exchange_rate_krw_usd": 1150,
                    "other_costs": [...],
                    "selling_price_usd_yd": 1.50
                }

        Returns:
            ValidationResult 객체
        """
        result = ValidationResult()

        # 1. 원단 입력 검증
        fabric_result = InputValidator.validate_fabric_input(
            inputs.get("fabric_width_inch", 0),
            inputs.get("proc_weight_input_value", 0),
            inputs.get("proc_weight_input_unit", "g/yd")
        )
        result.errors.extend(fabric_result.errors)

        # 2. 환율 검증
        exchange_result = InputValidator.validate_exchange_rate(
            inputs.get("base_exchange_rate_krw_usd", 0)
        )
        result.errors.extend(exchange_result.errors)

        # 3. 원사 데이터 검증
        yarn_result = InputValidator.validate_yarn_data(
            inputs.get("yarns_data", [])
        )
        result.errors.extend(yarn_result.errors)

        # 4. 손실률 검증
        loss_result = InputValidator.validate_loss_percentages(
            inputs.get("weaving_loss_pct", 0),
            inputs.get("dyeing_loss_pct", 0),
            inputs.get("delay_loss_pct", 0)
        )
        result.errors.extend(loss_result.errors)

        # 5. 가공비 검증
        fee_result = InputValidator.validate_processing_fees(
            inputs.get("weaving_fee_krw_kg", 0),
            inputs.get("dyeing_fee_krw_kg", 0)
        )
        result.errors.extend(fee_result.errors)

        return result


class YarnValidator:
    """원사 데이터 검증 클래스"""

    @staticmethod
    def validate_yarn_price(
        price_value: float,
        currency: str,
        unit: str
    ) -> ValidationResult:
        """
        원사 단가 검증

        Args:
            price_value: 단가 금액
            currency: 통화
            unit: 단위

        Returns:
            ValidationResult 객체
        """
        result = ValidationResult()

        if price_value < ValidationRules.MIN_PRICE:
            result.add_error(
                "price_value",
                f"단가는 {ValidationRules.MIN_PRICE} 이상이어야 합니다.",
                price_value
            )

        if currency not in CurrencyUnits.CURRENCIES:
            result.add_error(
                "currency",
                f"지원하지 않는 통화입니다. ({', '.join(CurrencyUnits.CURRENCIES)})",
                currency
            )

        if unit not in CurrencyUnits.WEIGHT_UNITS:
            result.add_error(
                "unit",
                f"지원하지 않는 단위입니다. ({', '.join(CurrencyUnits.WEIGHT_UNITS)})",
                unit
            )

        return result

    @staticmethod
    def validate_yarn_properties(
        denier: float,
        filament: float
    ) -> ValidationResult:
        """
        원사 속성 검증

        Args:
            denier: Denier 값
            filament: Filament 값

        Returns:
            ValidationResult 객체
        """
        result = ValidationResult()

        if denier < 0:
            result.add_error(
                "denier",
                "Denier는 0 이상이어야 합니다.",
                denier
            )

        if filament < 0:
            result.add_error(
                "filament",
                "Filament는 0 이상이어야 합니다.",
                filament
            )

        return result


if __name__ == '__main__':
    # 테스트 코드
    print("=== 입력 검증 테스트 ===\n")

    # 1. 원단 입력 검증
    print("1. 원단 입력 검증:")
    result = InputValidator.validate_fabric_input(60, 205, "g/yd")
    print(f"   정상 입력: {result.is_valid()}")

    result = InputValidator.validate_fabric_input(0, 205, "g/sqm")
    print(f"   비정상 입력 (g/sqm without width): {result.is_valid()}")
    if not result.is_valid():
        print(f"   오류: {result.get_first_error()}")

    # 2. 원사 데이터 검증
    print("\n2. 원사 데이터 검증:")
    yarns_valid = [
        {"id": 1, "ratio_pct": 60.0},
        {"id": 2, "ratio_pct": 40.0}
    ]
    result = InputValidator.validate_yarn_data(yarns_valid)
    print(f"   정상 원사 (60% + 40%): {result.is_valid()}")

    yarns_invalid = [
        {"id": 1, "ratio_pct": 60.0},
        {"id": 2, "ratio_pct": 30.0}  # 합계 90%
    ]
    result = InputValidator.validate_yarn_data(yarns_invalid)
    print(f"   비정상 원사 (60% + 30%): {result.is_valid()}")
    if not result.is_valid():
        print(f"   오류: {result.get_first_error()}")

    # 3. 통합 검증
    print("\n3. 통합 검증:")
    inputs = {
        "fabric_width_inch": 60,
        "proc_weight_input_value": 205,
        "proc_weight_input_unit": "g/yd",
        "yarns_data": [{"id": 1, "ratio_pct": 100.0}],
        "weaving_loss_pct": 2,
        "dyeing_loss_pct": 4,
        "delay_loss_pct": 6,
        "weaving_fee_krw_kg": 450,
        "dyeing_fee_krw_kg": 1900,
        "base_exchange_rate_krw_usd": 1150
    }
    result = InputValidator.validate_all_inputs(inputs)
    print(f"   정상 입력: {result.is_valid()}")

    inputs["base_exchange_rate_krw_usd"] = 0  # 잘못된 환율
    result = InputValidator.validate_all_inputs(inputs)
    print(f"   비정상 입력 (환율 0): {result.is_valid()}")
    if not result.is_valid():
        print(f"   오류 개수: {len(result.errors)}")
        for error in result.errors:
            print(f"      - {error}")

    # 4. 원사 단가 검증
    print("\n4. 원사 단가 검증:")
    result = YarnValidator.validate_yarn_price(0.8, "$", "lb")
    print(f"   정상 단가 ($0.8/lb): {result.is_valid()}")

    result = YarnValidator.validate_yarn_price(-1, "$", "lb")
    print(f"   비정상 단가 (-$1/lb): {result.is_valid()}")
    if not result.is_valid():
        print(f"   오류: {result.get_first_error()}")

    print("\n테스트 완료!")
