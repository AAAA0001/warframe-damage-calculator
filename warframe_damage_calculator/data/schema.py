class DatabaseEntry:
    def __init__(self, category, name, data):
        self.category = category
        self.name = name
        self.data = data

    @property
    def is_weapon(self):
        return self.category in {"primary", "secondary", "melee"}
