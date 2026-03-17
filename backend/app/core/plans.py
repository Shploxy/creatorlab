from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanDefinition:
    key: str
    name: str
    monthly_jobs: int | None
    monthly_price_usd: int
    description: str
    features: list[str]


PLANS: dict[str, PlanDefinition] = {
    "free": PlanDefinition(
        key="free",
        name="Free",
        monthly_jobs=50,
        monthly_price_usd=0,
        description="For everyday creator tasks with instant access and no signup required for the normal flow.",
        features=[
            "50 jobs per month",
            "Core image and PDF tools",
            "Saved history on the same device",
        ],
    ),
    "creator": PlanDefinition(
        key="creator",
        name="Creator",
        monthly_jobs=200,
        monthly_price_usd=5,
        description="For freelancers and solo creators who want more monthly headroom and a smoother queue.",
        features=[
            "200 jobs per month",
            "Priority processing",
            "Faster queue placement",
        ],
    ),
    "pro": PlanDefinition(
        key="pro",
        name="Pro",
        monthly_jobs=None,
        monthly_price_usd=12,
        description="For heavier usage with faster turnaround, premium access, and fair-use processing priority.",
        features=[
            "High or fair-use monthly jobs",
            "Fastest queue priority",
            "Prepared for future Stripe billing integration",
        ],
    ),
}


def get_plan(plan_key: str) -> PlanDefinition:
    if plan_key == "growth":
        return PLANS["pro"]
    return PLANS.get(plan_key, PLANS["free"])


def serialize_plans() -> list[dict[str, object]]:
    return [
        {
            "key": plan.key,
            "name": plan.name,
            "monthly_jobs": plan.monthly_jobs,
            "monthly_price_usd": plan.monthly_price_usd,
            "description": plan.description,
            "features": plan.features,
        }
        for plan in PLANS.values()
    ]
