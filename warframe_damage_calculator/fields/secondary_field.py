from .ranged_field import RangedField


class SecondaryField(RangedField):
    """Represents keyword fields for secondary weapons.

    Secondary weapons currently use the same constructor inputs as other
    ranged weapons, so this class does not add fields beyond ``RangedField``.

    It gives ``Secondary`` its own named input type while keeping the shared
    ranged weapon field set.
    """