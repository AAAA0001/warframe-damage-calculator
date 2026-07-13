class WeaponFormatter:
    def __init__(self, calculator):
        self.calculator = calculator

    def upgrades(self):
        contributions = self.calculator.contribution_proportions()
        if not contributions: return ""
        max_len = max(len(name) for name in contributions)
        return "\n".join(f"{f'{name}:':<{max_len + 1}} {contribution:.2%}" for name, contribution in contributions.items())
