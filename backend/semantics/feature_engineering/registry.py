from .revenue import RevenueRule
from .ratios import RatioRule
from .margin import MarginRule
from .datetime_features import DatetimeFeaturesRule

FEATURE_RULES = [
    RevenueRule(),    # price × quantity → ricavo
    MarginRule(),     # sell_price - cost → margine
    RatioRule(),      # quantity / quantity → rapporto
    DatetimeFeaturesRule(),
]
