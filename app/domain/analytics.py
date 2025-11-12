from __future__ import annotations

from typing import Dict, List, Optional


def safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b in (None, 0):
        return None
    try:
        return a / b
    except ZeroDivisionError:
        return None


def price_per_sqft(price: Optional[float], sqft: Optional[float]) -> Optional[float]:
    return safe_div(price, sqft)


def rent_per_sqft(rent_monthly: Optional[float], sqft: Optional[float]) -> Optional[float]:
    return safe_div(rent_monthly, sqft)


def rent_to_price(rent_monthly: Optional[float], price: Optional[float]) -> Optional[float]:
    annual = None if rent_monthly is None else rent_monthly * 12
    return safe_div(annual, price)


def gross_yield(annual_rent: Optional[float], purchase_price: Optional[float]) -> Optional[float]:
    return safe_div(annual_rent, purchase_price)


def cap_rate(
    annual_rent: Optional[float],
    vacancy_pct: float,
    op_ex_annual: Optional[float],
    purchase_price: Optional[float],
) -> Optional[float]:
    if annual_rent is None or purchase_price in (None, 0):
        return None
    effective = annual_rent * (1 - (vacancy_pct or 0) / 100.0)
    if op_ex_annual is None:
        return safe_div(effective, purchase_price)
    return safe_div(effective - op_ex_annual, purchase_price)


def grm(purchase_price: Optional[float], annual_rent: Optional[float]) -> Optional[float]:
    return safe_div(purchase_price, annual_rent)


def compute_metrics(row: Dict, assumptions: Dict) -> Dict[str, Optional[float]]:
    facts = row.get("facts", {})
    pricing = row.get("pricing", {})
    category = row.get("category")

    sqft = facts.get("sqft")
    list_price = pricing.get("list_price")

    rent_m = list_price if category == "rental" else None
    price = list_price if category == "sale" else None

    annual_rent = None if rent_m is None else rent_m * 12
    op_ex_annual = None
    if annual_rent is not None:
        maint = (assumptions.get("maintenance_pct_of_rent", 0) or 0) / 100.0
        mgmt = (assumptions.get("mgmt_pct_of_rent", 0) or 0) / 100.0
        taxes = assumptions.get("taxes_annual") or 0
        ins = assumptions.get("insurance_annual") or 0
        hoa = (assumptions.get("hoa_monthly") or 0) * 12
        op_ex_annual = annual_rent * (maint + mgmt) + taxes + ins + hoa

    purchase_price = assumptions.get("purchase_price") or price

    return {
        "price_per_sqft": price_per_sqft(price, sqft),
        "rent_per_sqft": rent_per_sqft(rent_m, sqft),
        "rent_to_price": rent_to_price(rent_m, price),
        "gross_yield": gross_yield(annual_rent, purchase_price),
        "cap_rate": cap_rate(annual_rent, assumptions.get("vacancy_pct", 0) or 0, op_ex_annual, purchase_price),
        "grm": grm(purchase_price, annual_rent),
    }
