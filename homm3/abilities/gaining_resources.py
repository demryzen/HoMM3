from homm3.abilities import Ability, register_ability


@register_ability
class GoldGenerationAbility(Ability):
    name = "GoldGeneration"


@register_ability
class CrystalsGenerationAbility(Ability):
    name = "CrystalsGeneration"


