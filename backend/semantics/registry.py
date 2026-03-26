from .detectors.price import PriceDetector
from .detectors.quantity import QuantityDetector
from .detectors.id import IDDetector
from .detectors.date import DateDetector
from .detectors.percentage import PercentageDetector
from .detectors.categorical import CategoricalDetector
from .detectors.text import TextDetector

DETECTORS = [
    PriceDetector(),
    QuantityDetector(),
    IDDetector(),
    DateDetector(),
    PercentageDetector(),
    CategoricalDetector(),
    TextDetector()
]
