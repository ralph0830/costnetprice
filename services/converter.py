"""
단위 및 통화 변환 모듈

원가 계산에 필요한 모든 단위 변환과 통화 변환 기능을 제공합니다.
"""

from models.constants import UnitConversion, CurrencyUnits, ErrorMessages


class UnitConverter:
    """단위 변환 유틸리티 클래스"""

    @staticmethod
    def weight_to_gyd(value: float, unit: str, width_inch: float = None) -> float:
        """
        원단 중량을 g/yd로 변환합니다.

        Args:
            value: 중량 값
            unit: 중량 단위 ("g/yd" 또는 "g/sqm")
            width_inch: 원단 전폭 (g/sqm 변환 시 필요)

        Returns:
            g/yd 단위로 변환된 값

        Raises:
            ValueError: 지원하지 않는 단위이거나 필수 파라미터 누락
        """
        if unit == CurrencyUnits.UNIT_GYD:
            return value

        elif unit == CurrencyUnits.UNIT_GSQM:
            if width_inch is None or width_inch <= 0:
                raise ValueError(ErrorMessages.ERR_GSQM_CONVERSION)
            return value * width_inch * UnitConversion.GSM_TO_GYD_PER_INCH

        else:
            raise ValueError(f"지원하지 않는 중량 단위: {unit}")

    @staticmethod
    def weight_to_kg_per_yd(value_gyd: float) -> float:
        """
        g/yd를 kg/yd로 변환합니다.

        Args:
            value_gyd: g/yd 값

        Returns:
            kg/yd로 변환된 값
        """
        return value_gyd * UnitConversion.G_TO_KG

    @staticmethod
    def price_to_usd_per_kg(
        price: float,
        currency: str,
        unit: str,
        exchange_rate: float
    ) -> float:
        """
        원사 단가를 $/kg로 변환합니다.

        Args:
            price: 원사 단가
            currency: 통화 ("$" 또는 "원화")
            unit: 단위 ("lb" 또는 "kg")
            exchange_rate: 환율 (원/$)

        Returns:
            $/kg로 변환된 단가

        Raises:
            ValueError: 유효하지 않은 환율 또는 지원하지 않는 통화/단위
        """
        # 1단계: 통화를 USD로 변환
        price_usd = CurrencyConverter.to_usd(price, currency, exchange_rate)

        # 2단계: 단위를 kg으로 변환
        if unit == CurrencyUnits.UNIT_LB:
            return price_usd * UnitConversion.KG_TO_LB
        elif unit == CurrencyUnits.UNIT_KG:
            return price_usd
        else:
            raise ValueError(f"지원하지 않는 중량 단위: {unit}")

    @staticmethod
    def lb_to_kg(value_lb: float) -> float:
        """파운드를 킬로그램으로 변환"""
        return value_lb * UnitConversion.LB_TO_KG

    @staticmethod
    def kg_to_lb(value_kg: float) -> float:
        """킬로그램을 파운드로 변환"""
        return value_kg * UnitConversion.KG_TO_LB

    @staticmethod
    def yd_to_m(value_yd: float) -> float:
        """야드를 미터로 변환"""
        return value_yd * UnitConversion.YD_TO_M

    @staticmethod
    def m_to_yd(value_m: float) -> float:
        """미터를 야드로 변환"""
        return value_m * UnitConversion.M_TO_YD

    @staticmethod
    def inch_to_cm(value_inch: float) -> float:
        """인치를 센티미터로 변환"""
        return value_inch * UnitConversion.INCH_TO_CM


class CurrencyConverter:
    """통화 변환 유틸리티 클래스"""

    @staticmethod
    def to_usd(amount: float, currency: str, exchange_rate: float) -> float:
        """
        금액을 USD로 변환합니다.

        Args:
            amount: 금액
            currency: 통화 ("$" 또는 "원화")
            exchange_rate: 환율 (원/$)

        Returns:
            USD로 변환된 금액

        Raises:
            ValueError: 유효하지 않은 환율 또는 지원하지 않는 통화
        """
        if currency == CurrencyUnits.CURRENCY_USD:
            return amount

        elif currency == CurrencyUnits.CURRENCY_KRW:
            if exchange_rate <= 0:
                raise ValueError("유효하지 않은 환율입니다.")
            return amount / exchange_rate

        else:
            raise ValueError(f"지원하지 않는 통화: {currency}")

    @staticmethod
    def to_krw(amount: float, currency: str, exchange_rate: float) -> float:
        """
        금액을 원화로 변환합니다.

        Args:
            amount: 금액
            currency: 통화 ("$" 또는 "원화")
            exchange_rate: 환율 (원/$)

        Returns:
            원화로 변환된 금액

        Raises:
            ValueError: 유효하지 않은 환율 또는 지원하지 않는 통화
        """
        if currency == CurrencyUnits.CURRENCY_KRW:
            return amount

        elif currency == CurrencyUnits.CURRENCY_USD:
            if exchange_rate <= 0:
                raise ValueError("유효하지 않은 환율입니다.")
            return amount * exchange_rate

        else:
            raise ValueError(f"지원하지 않는 통화: {currency}")


class LossCalculator:
    """손실률 계산 유틸리티 클래스"""

    @staticmethod
    def calculate_loss_multiplier(
        weaving_loss_pct: float,
        dyeing_loss_pct: float,
        delay_loss_pct: float
    ) -> float:
        """
        손실률을 반영한 승수를 계산합니다.

        각 단계의 손실률이 누적 적용됩니다.
        예: 2% + 4% + 6% = 1.02 × 1.04 × 1.06 = 1.1245

        Args:
            weaving_loss_pct: 제직 손실률 (%)
            dyeing_loss_pct: 염색 손실률 (%)
            delay_loss_pct: 지연 손실률 (%)

        Returns:
            손실률 승수
        """
        multiplier = 1.0
        multiplier *= (1 + weaving_loss_pct / 100.0)
        multiplier *= (1 + dyeing_loss_pct / 100.0)
        multiplier *= (1 + delay_loss_pct / 100.0)
        return multiplier

    @staticmethod
    def apply_loss_to_weight(base_weight: float, loss_multiplier: float) -> float:
        """
        손실률을 원단 중량에 적용합니다.

        Args:
            base_weight: 기본 중량
            loss_multiplier: 손실률 승수

        Returns:
            손실률이 적용된 중량
        """
        return base_weight * loss_multiplier


if __name__ == '__main__':
    # 테스트 코드
    print("=== 단위 변환 테스트 ===\n")

    # 1. 원단 중량 변환
    print("1. 원단 중량 변환:")
    weight_gyd = UnitConverter.weight_to_gyd(205, "g/yd")
    print(f"   205 g/yd = {weight_gyd} g/yd")

    weight_gsqm_to_gyd = UnitConverter.weight_to_gyd(205, "g/sqm", width_inch=60)
    print(f"   205 g/sqm (60 inch) = {weight_gsqm_to_gyd:.2f} g/yd")

    weight_kg_yd = UnitConverter.weight_to_kg_per_yd(205)
    print(f"   205 g/yd = {weight_kg_yd:.4f} kg/yd")

    # 2. 원사 단가 변환
    print("\n2. 원사 단가 변환:")
    price_usd_kg = UnitConverter.price_to_usd_per_kg(
        price=0.8,
        currency="$",
        unit="lb",
        exchange_rate=1150
    )
    print(f"   $0.8/lb = ${price_usd_kg:.4f}/kg")

    price_krw_kg = UnitConverter.price_to_usd_per_kg(
        price=2500,
        currency="원화",
        unit="kg",
        exchange_rate=1150
    )
    print(f"   2500원/kg = ${price_krw_kg:.4f}/kg (환율 1150원)")

    # 3. 통화 변환
    print("\n3. 통화 변환:")
    usd_amount = CurrencyConverter.to_usd(1150, "원화", 1150)
    print(f"   1150원 = ${usd_amount:.2f} (환율 1150원)")

    krw_amount = CurrencyConverter.to_krw(1.0, "$", 1150)
    print(f"   $1.0 = {krw_amount:.0f}원 (환율 1150원)")

    # 4. 손실률 계산
    print("\n4. 손실률 계산:")
    loss_multiplier = LossCalculator.calculate_loss_multiplier(2, 4, 6)
    print(f"   제직 2% + 염색 4% + 지연 6% = {loss_multiplier:.4f}")
    print(f"   총 손실률: {(loss_multiplier - 1) * 100:.2f}%")

    base_weight = 0.205  # kg/yd
    actual_weight = LossCalculator.apply_loss_to_weight(base_weight, loss_multiplier)
    print(f"   기본 중량: {base_weight:.3f} kg/yd")
    print(f"   손실 적용 후: {actual_weight:.3f} kg/yd")

    # 5. 에러 처리 테스트
    print("\n5. 에러 처리 테스트:")
    try:
        UnitConverter.weight_to_gyd(205, "g/sqm")  # width_inch 누락
    except ValueError as e:
        print(f"   예상된 에러: {e}")

    try:
        CurrencyConverter.to_usd(1000, "원화", 0)  # 잘못된 환율
    except ValueError as e:
        print(f"   예상된 에러: {e}")

    print("\n테스트 완료!")
