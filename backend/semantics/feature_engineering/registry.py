from .datetime_features import DatetimeFeaturesRule
from .margin import MarginRule
from .ratios import RatioRule
from .revenue import RevenueRule

FEATURE_RULES = [
    RevenueRule(),  # price × quantity → ricavo
    MarginRule(),  # sell_price - cost → margine
    RatioRule(),  # quantity / quantity → rapporto
    DatetimeFeaturesRule(),
]
