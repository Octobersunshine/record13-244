from dataclasses import dataclass, field
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


class MaintenanceType(Enum):
    MINOR = "小保养"
    MEDIUM = "中保养"
    MAJOR = "大保养"
    INSPECTION = "检查项"


BRAND_DEFAULT_INTERVAL = {
    CarBrand.JAPANESE: 5_000,
    CarBrand.KOREAN: 5_000,
    CarBrand.AMERICAN: 8_000,
    CarBrand.CHINESE: 7_500,
    CarBrand.GERMAN: 10_000,
    CarBrand.FRENCH: 10_000,
    CarBrand.OTHER: 10_000,
}


BRAND_OIL_GRADE = {
    CarBrand.JAPANESE: "0W-20 全合成",
    CarBrand.KOREAN: "5W-30 全合成",
    CarBrand.AMERICAN: "5W-30 全合成",
    CarBrand.CHINESE: "5W-40 全合成",
    CarBrand.GERMAN: "0W-40 全合成",
    CarBrand.FRENCH: "5W-30 全合成",
    CarBrand.OTHER: "5W-30 全合成",
}


def get_default_interval(brand: CarBrand) -> int:
    return BRAND_DEFAULT_INTERVAL.get(brand, 10_000)


@dataclass
class MaintenanceItem:
    name: str
    item_type: MaintenanceType
    price: float = 0.0
    is_required: bool = True
    notes: str = ""

    def display(self) -> str:
        tag = "★必做" if self.is_required else " 建议"
        price_str = f" ¥{self.price:,.0f}" if self.price > 0 else ""
        notes_str = f" ({self.notes})" if self.notes else ""
        return f"[{self.item_type.value}] {tag} {self.name}{price_str}{notes_str}"


@dataclass
class MaintenanceItemsResult:
    maintenance_type: MaintenanceType
    items: list[MaintenanceItem] = field(default_factory=list)

    @property
    def total_price(self) -> float:
        return sum(it.price for it in self.items)

    def required_items(self) -> list[MaintenanceItem]:
        return [it for it in self.items if it.is_required]

    def optional_items(self) -> list[MaintenanceItem]:
        return [it for it in self.items if not it.is_required]


@dataclass
class MaintenanceResult:
    brand: CarBrand
    next_mileage: int
    remaining_mileage: int
    estimated_days: int
    estimated_date: date
    is_overdue: bool
    overdue_mileage: int
    maintenance_items: MaintenanceItemsResult


@dataclass
class VehicleProfile:
    current_mileage: int
    last_maintenance_mileage: int
    last_maintenance_date: date
    brand: CarBrand = CarBrand.OTHER
    maintenance_interval_km: Optional[int] = None
    current_date: Optional[date] = None
    daily_mileage: Optional[float] = None
    has_timing_belt: bool = True
    transmission_type: str = "AT"

    def __post_init__(self):
        if self.maintenance_interval_km is None:
            self.maintenance_interval_km = get_default_interval(self.brand)
        if self.current_date is None:
            self.current_date = date.today()
        if self.daily_mileage is None:
            days_since = max((self.current_date - self.last_maintenance_date).days, 1)
            km_since = self.current_mileage - self.last_maintenance_mileage
            self.daily_mileage = max(km_since / days_since, 0.0)


def _oil_and_filter_items(brand: CarBrand) -> list[MaintenanceItem]:
    oil_grade = BRAND_OIL_GRADE.get(brand, "5W-30 全合成")
    prices = {
        CarBrand.GERMAN: 180,
        CarBrand.JAPANESE: 120,
        CarBrand.KOREAN: 130,
        CarBrand.AMERICAN: 140,
        CarBrand.CHINESE: 100,
        CarBrand.FRENCH: 140,
        CarBrand.OTHER: 130,
    }
    oil_price = prices.get(brand, 130)
    return [
        MaintenanceItem(f"发动机机油 {oil_grade} (4L)", MaintenanceType.MINOR, oil_price, True),
        MaintenanceItem("机油滤清器", MaintenanceType.MINOR, 40, True),
    ]


def _air_filter_items(brand: CarBrand) -> list[MaintenanceItem]:
    return [
        MaintenanceItem("空气滤芯", MaintenanceType.MEDIUM, 60, True),
        MaintenanceItem("空调滤芯", MaintenanceType.MEDIUM, 50, True),
    ]


def _fuel_and_brake_items() -> list[MaintenanceItem]:
    return [
        MaintenanceItem("汽油滤清器", MaintenanceType.MAJOR, 80, True),
        MaintenanceItem("刹车油 (1L)", MaintenanceType.MAJOR, 120, True),
        MaintenanceItem("变速箱油", MaintenanceType.MAJOR, 260, True),
        MaintenanceItem("火花塞 (4支)", MaintenanceType.MAJOR, 240, True),
    ]


def _major_service_items(profile: VehicleProfile, next_mileage: int) -> list[MaintenanceItem]:
    items: list[MaintenanceItem] = []

    if next_mileage % 20_000 == 0:
        items.extend(_air_filter_items(profile.brand))

    if next_mileage % 40_000 == 0:
        items.extend(_fuel_and_brake_items())

    if next_mileage % 60_000 == 0:
        items.append(MaintenanceItem("防冻液 (4L)", MaintenanceType.MAJOR, 180, True))
        if profile.has_timing_belt:
            items.append(MaintenanceItem("正时皮带+张紧轮", MaintenanceType.MAJOR, 680, True, "皮带车型必换"))

    if next_mileage % 80_000 == 0:
        items.append(MaintenanceItem("助力转向油", MaintenanceType.MAJOR, 100, True))
        items.append(MaintenanceItem("氧传感器检查/更换", MaintenanceType.MAJOR, 380, False))

    if next_mileage % 100_000 == 0:
        items.append(MaintenanceItem("节气门深度清洗", MaintenanceType.MAJOR, 200, False))
        items.append(MaintenanceItem("喷油嘴清洗", MaintenanceType.MAJOR, 260, False))
        items.append(MaintenanceItem("三元催化清洗", MaintenanceType.MAJOR, 320, False))

    return items


def _inspection_items() -> list[MaintenanceItem]:
    return [
        MaintenanceItem("刹车片磨损检查", MaintenanceType.INSPECTION, 0, True),
        MaintenanceItem("轮胎磨损/气压检查", MaintenanceType.INSPECTION, 0, True),
        MaintenanceItem("电瓶电压检测", MaintenanceType.INSPECTION, 0, True),
        MaintenanceItem("灯光系统检查", MaintenanceType.INSPECTION, 0, True),
        MaintenanceItem("底盘/悬挂检查", MaintenanceType.INSPECTION, 0, True),
        MaintenanceItem("雨刮片检查", MaintenanceType.INSPECTION, 0, False),
        MaintenanceItem("防冻液冰点检测", MaintenanceType.INSPECTION, 0, False),
    ]


def determine_maintenance_type(next_mileage: int, interval: int) -> MaintenanceType:
    if next_mileage % 40_000 == 0 or next_mileage % 60_000 == 0 or next_mileage % 100_000 == 0:
        return MaintenanceType.MAJOR
    if next_mileage % 20_000 == 0:
        return MaintenanceType.MEDIUM
    return MaintenanceType.MINOR


def generate_maintenance_items(profile: VehicleProfile, next_mileage: int) -> MaintenanceItemsResult:
    interval = profile.maintenance_interval_km or 10_000
    mtype = determine_maintenance_type(next_mileage, interval)

    items: list[MaintenanceItem] = []
    items.extend(_oil_and_filter_items(profile.brand))
    items.extend(_major_service_items(profile, next_mileage))
    items.extend(_inspection_items())

    return MaintenanceItemsResult(maintenance_type=mtype, items=items)


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
    maintenance_items = generate_maintenance_items(profile, next_mileage)

    return MaintenanceResult(
        brand=profile.brand,
        next_mileage=next_mileage,
        remaining_mileage=remaining_mileage,
        estimated_days=estimated_days,
        estimated_date=estimated_date,
        is_overdue=is_overdue,
        overdue_mileage=overdue_mileage,
        maintenance_items=maintenance_items,
    )


def print_items_detail(result: MaintenanceResult):
    mi = result.maintenance_items
    print(f"\n保养类型:       {mi.maintenance_type.value}")
    print("-" * 55)
    print("保养项目清单:")
    for item in mi.items:
        print(f"  {item.display()}")
    print("-" * 55)
    req_count = len(mi.required_items())
    opt_count = len(mi.optional_items())
    print(f"必做项目 {req_count} 项, 建议项目 {opt_count} 项")
    print(f"预估总费用:     ¥{mi.total_price:,.0f}")


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
        mtype_tag = f"[{result.maintenance_items.maintenance_type.value}]"
        print(f"{brand.value:<6} 间隔 {profile.maintenance_interval_km:>6,} km | "
              f"下次 {result.next_mileage:>7,} km {mtype_tag:<6} | "
              f"剩余 {result.remaining_mileage:>5,} km | "
              f"¥{result.maintenance_items.total_price:>5,.0f} | "
              f"预计 {result.estimated_date} {status}")


if __name__ == "__main__":
    demo_brand_comparison()
    print()

    cases = [
        ("日系 6 万公里大保养示例", CarBrand.JAPANESE, 58_000, 55_000),
        ("德系 6 万公里大保养示例", CarBrand.GERMAN, 58_000, 50_000),
        ("美系 4 万公里中保养示例", CarBrand.AMERICAN, 38_000, 32_000),
        ("日系 1 万公里小保养示例", CarBrand.JAPANESE, 54_000, 50_000),
    ]

    for title, brand, cur_mileage, last_mileage in cases:
        profile = VehicleProfile(
            current_mileage=cur_mileage,
            last_maintenance_mileage=last_mileage,
            last_maintenance_date=date(2025, 12, 1),
            brand=brand,
            current_date=date(2026, 6, 13),
        )
        result = calculate_next_maintenance(profile)

        print(f"=== {title} ===")
        print(f"车系:           {profile.brand.value}")
        print(f"当前里程:       {profile.current_mileage:,} km")
        print(f"下次保养里程:   {result.next_mileage:,} km")
        print(f"剩余里程:       {result.remaining_mileage:,} km")
        print(f"预计日期:       {result.estimated_date}")
        if result.is_overdue:
            print(f"⚠ 已超期:       {result.overdue_mileage:,} km")
        print_items_detail(result)
        print()
