from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


@dataclass
class MaintenanceResult:
    next_mileage: int
    remaining_mileage: int
    estimated_days: int
    estimated_date: date


@dataclass
class VehicleProfile:
    current_mileage: int
    last_maintenance_mileage: int
    maintenance_interval_km: int
    last_maintenance_date: date
    current_date: Optional[date] = None
    daily_mileage: Optional[float] = None

    def __post_init__(self):
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

    if next_mileage <= profile.current_mileage:
        intervals_passed = (profile.current_mileage - profile.last_maintenance_mileage) // profile.maintenance_interval_km
        next_mileage = profile.last_maintenance_mileage + (intervals_passed + 1) * profile.maintenance_interval_km

    remaining_mileage = next_mileage - profile.current_mileage

    if profile.daily_mileage > 0:
        estimated_days = int(remaining_mileage / profile.daily_mileage)
    else:
        estimated_days = 0

    estimated_date = profile.current_date + timedelta(days=estimated_days)

    return MaintenanceResult(
        next_mileage=next_mileage,
        remaining_mileage=remaining_mileage,
        estimated_days=estimated_days,
        estimated_date=estimated_date,
    )


if __name__ == "__main__":
    profile = VehicleProfile(
        current_mileage=58_000,
        last_maintenance_mileage=50_000,
        maintenance_interval_km=10_000,
        last_maintenance_date=date(2025, 12, 1),
        current_date=date(2026, 6, 13),
    )

    result = calculate_next_maintenance(profile)

    print(f"当前里程:       {profile.current_mileage:,} km")
    print(f"上次保养里程:   {profile.last_maintenance_mileage:,} km")
    print(f"保养间隔:       {profile.maintenance_interval_km:,} km")
    print(f"日均行驶:       {profile.daily_mileage:.1f} km")
    print("-" * 35)
    print(f"下次保养里程:   {result.next_mileage:,} km")
    print(f"剩余里程:       {result.remaining_mileage:,} km")
    print(f"预计天数:       {result.estimated_days} 天")
    print(f"预计日期:       {result.estimated_date}")
