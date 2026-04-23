from __future__ import annotations

from dataclasses import dataclass

from app.ai_agents.schemas import AIUserContext
from app.models.exercise import Equipment, Exercise
from app.services.workout.rules import DEFAULT_EQUIPMENT, resolve_injury_contras


@dataclass(slots=True, frozen=True)
class SafetyFilterResult:
    safe_slugs: frozenset[str]
    contras: frozenset[str]
    equipment: frozenset[Equipment]
    dropped: tuple[str, ...]


class SafetyAgent:
    """Pure-rule gatekeeper. Runs before AND after the LLM.

    - Pre-LLM: we pass only safe slugs into the prompt, so the model cannot even
      choose dangerous exercises.
    - Post-LLM: we re-check that the slugs it returned are still safe — defense
      in depth against jailbreaks / hallucinations.
    """

    def filter_catalogue(
        self,
        ctx: AIUserContext,
        catalogue: list[Exercise],
    ) -> SafetyFilterResult:
        contras = resolve_injury_contras(ctx.injuries)
        equipment = self._parse_equipment(ctx.equipment)

        safe: set[str] = set()
        dropped: list[str] = []
        for ex in catalogue:
            if not ex.is_active:
                continue
            if ex.equipment not in equipment:
                continue
            if contras & set(ex.contraindications):
                dropped.append(ex.slug)
                continue
            safe.add(ex.slug)
        return SafetyFilterResult(
            safe_slugs=frozenset(safe),
            contras=contras,
            equipment=equipment,
            dropped=tuple(dropped),
        )

    def is_exercise_safe(self, ex: Exercise, result: SafetyFilterResult) -> bool:
        if ex.equipment not in result.equipment:
            return False
        return not (result.contras & set(ex.contraindications))

    @staticmethod
    def _parse_equipment(values: list[str]) -> frozenset[Equipment]:
        valid = {v for v in values if v in Equipment._value2member_map_}
        return frozenset(Equipment(v) for v in valid) or DEFAULT_EQUIPMENT
