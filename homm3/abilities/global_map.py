from homm3.abilities import Ability, register_ability


@register_ability
class SandwalkerAbility(Ability):
    name = "Sandwalker"


@register_ability
class SpyingAbility(Ability):
    name = "Spying"

