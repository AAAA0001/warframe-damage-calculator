from .ranged_field import RangedField


class PrimaryField(RangedField):
    """Represents keyword fields for primary weapons.

    Primary weapons currently use the same constructor inputs as other ranged
    weapons, so this class does not add fields beyond ``RangedField``.

    It gives ``Primary`` its own named input type while keeping the shared
    ranged weapon field set.
    """