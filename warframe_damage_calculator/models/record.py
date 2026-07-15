from .data import Data


class Record(Data):
    """Backward-compatible alias. New code should use :class:`Data`."""

    def __init__(self, data=None, /, **fields):
        super().__init__(data, **fields)
