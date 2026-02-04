FREE_PLAN = {
    "name": "Free",
    "limits": {
        "optimizations": 1,
        "csv_export": False,
        "cro_audit": False,
        "ad_hooks": False,
    },
}

PLAN_CONFIG = {
    "price_starter_monthly": {
        "name": "Starter",
        "limits": {
            "optimizations": 50,
            "csv_export": True,
            "cro_audit": True,
            "ad_hooks": True,
        },
    },
    "price_growth_monthly": {
        "name": "Growth",
        "limits": {
            "optimizations": "unlimited",
            "csv_export": True,
            "cro_audit": True,
            "ad_hooks": True,
        },
    },
}

PLANS_BY_PRICE_ID = {
    "price_starter_123": {
        "id": "starter",
        "name": "Starter",
        "limits": {
            "optimizations_per_period": 50
        },
    },
    "price_growth_456": {
        "id": "growth",
        "name": "Growth",
        "limits": {
            "optimizations_per_period": 999999
        },
    },
}