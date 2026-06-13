from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Optional


class CarBrand(Enum):
    JAPANESE = "日系"
    GERMAN = "德系"
    AMERICAN = "美系"
    KOREAN = "韩系"
    FRENCH = "法系"
    CHINESE = "国产"
    OTHER = "其他"


BRAND_DEFAULT_INTERVAL = {
    CarBrand.JAPANESE: 5_000,
    CarBrand.KOREAN: 5_000,
    CarBrand.AMERICAN: 8_000,
    CarBrand.CHINESE: 7_500,
    CarBrand.GERMAN: 10_000,
    CarBrand.FRENCH: 10_000,
    CarBrand.OTHER: 10_000,
}


def get_default_interval(brand: CarBrand) -> int:
    return BRAND_DEFAULT_INTERVAL.get(brand, 10_000)


@dataclass
class MaintenanceResult:
    brand: CarBrand
    next_mileage: int
    remaining_mileage: int
    estimated_days: int
    estimated_date: date
    is_overdue: bool
    overdue_mileage: int


@dataclass
class VehicleProfile:
    current_mileage: int
    last_maintenance_mileage: int
    last_maintenance_date: date
    brand: CarBrand = CarBrand.OTHER
    maintenance_interval_km: Optional[int] = None
    current_date: Optional[date] = None
    daily_mileage: Optional[float] = None

    def __post_init__(self):
        if self.maintenance_interval_km is None:
            self.maintenance_interval_km = get_default_interval(self.brand)
        if self.current_date is None:
            self.current_date = date.today()
        if self.daily_mileage is None:
            days_since = max((self.current_date - self.last_maintenance_date).days, 1)
            km_since = self.current_mileage - self.last_maintenance_mileage
            self.daily_mileage = max(km_since / days_since, 0.0)


def calculate_next_maintenance(profile: VehicleProfile) -> MaintenanceResult:
    if profile.current_mileage < 0 or profile.last_maintenance_mileage < 0:
        raise ValueError("里程不能为负数")
    if profile.current_mileage < profile.last_maintenance_mileage:
        raise ValueError("当前里程不能小于上次保养里程")
    if profile.maintenance_interval_km <= 0:
        raise ValueError("保养间隔必须大于0")

    next_mileage = profile.last_maintenance_mileage + profile.maintenance_interval_km

    intervals_passed = 0
    if next_mileage <= profile.current_mileage:
        intervals_passed = (profile.current_mileage - profile.last_maintenance_mileage) // profile.maintenance_interval_km
        next_mileage = profile.last_maintenance_mileage + (intervals_passed + 1) * profile.maintenance_interval_km

    remaining_mileage = next_mileage - profile.current_mileage
    is_overdue = intervals_passed > 0
    overdue_mileage = max(profile.current_mileage - (profile.last_maintenance_mileage + intervals_passed * profile.maintenance_interval_km), 0)

    if profile.daily_mileage > 0:
        estimated_days = int(remaining_mileage / profile.daily_mileage)
    else:
        estimated_days = 0

    estimated_date = profile.current_date + timedelta(days=estimated_days)

    return MaintenanceResult(
        brand=profile.brand,
        next_mileage=next_mileage,
        remaining_mileage=remaining_mileage,
        estimated_days=estimated_days,
        estimated_date=estimated_date,
        is_overdue=is_overdue,
        overdue_mileage=overdue_mileage,
    )


def demo_brand_comparison():
    demo_date = date(2026, 6, 13)
    last_date = date(2025, 12, 1)
    last_mileage = 50_000
    current_mileage = 58_000

    print("=== 不同车系保养间隔对比 ===")
    print(f"基准条件: 当前里程 {current_mileage:,} km / 上次 {last_mileage:,} km / 上次日期 {last_date}\n")

    for brand in [CarBrand.JAPANESE, CarBrand.GERMAN, CarBrand.AMERICAN, CarBrand.CHINESE]:
        profile = VehicleProfile(
            current_mileage=current_mileage,
            last_maintenance_mileage=last_mileage,
            last_maintenance_date=last_date,
            brand=brand,
            current_date=demo_date,
        )
        result = calculate_next_maintenance(profile)
        status = f"[已超期 {result.overdue_mileage:,} km]" if result.is_overdue else ""
        print(f"{brand.value:<6} 间隔 {profile.maintenance_interval_km:>6,} km | "
              f"下次 {result.next_mileage:>7,} km | "
              f"剩余 {result.remaining_mileage:>5,} km | "
              f"预计 {result.estimated_date} {status}")


if __name__ == "__main__":
    demo_brand_comparison()
    print()

    profile = VehicleProfile(
        current_mileage=58_000,
        last_maintenance_mileage=50_000,
        last_maintenance_date=date(2025, 12, 1),
        brand=CarBrand.JAPANESE,
        current_date=date(2026, 6, 13),
    )

    result = calculate_next_maintenance(profile)

    print("=== 日系车单独示例 ===")
    print(f"车系:           {profile.brand.value}")
    print(f"当前里程:       {profile.current_mileage:,} km")
    print(f"上次保养里程:   {profile.last_maintenance_mileage:,} km")
    print(f"保养间隔:       {profile.maintenance_interval_km:,} km")
    print(f"日均行驶:       {profile.daily_mileage:.1f} km")
    print("-" * 40)
    print(f"下次保养里程:   {result.next_mileage:,} km")
    print(f"剩余里程:       {result.remaining_mileage:,} km")
    print(f"预计天数:       {result.estimated_days} 天")
    print(f"预计日期:       {result.estimated_date}")
    if result.is_overdue:
        print(f"⚠ 已超期:       {result.overdue_mileage:,} km")

