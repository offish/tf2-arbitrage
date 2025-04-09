from tf2_utils import PricesTF as PricesTFUtils

from .sites import Site


class PricesTF(PricesTFUtils, Site):
    def __init__(self) -> None:
        super().__init__()
