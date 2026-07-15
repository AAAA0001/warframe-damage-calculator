from ..models import Melee, Primary, Secondary, Upgrade


class DatabaseFactory:
    models = {"primary": Primary, "secondary": Secondary, "melee": Melee, "mod": Upgrade, "arcane": Upgrade}

    def create(self, entry):
        return self.models[entry.category](entry.data)
