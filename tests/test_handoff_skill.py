"""Contract tests for the prose-based handoff skill.

The value of this skill is its strict output shape: a handoff that drops a
section, reorders it, or wraps it in commentary is no longer self-contained for
the next agent. These tests pin the shape, the trigger words, and the rules.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / ".cursor/skills/handoff/SKILL.md"

REQUIRED_SECTIONS = [
    "### HANDOFF",
    "**Status:**",
    "**What was done:**",
    "**Key decisions:**",
    "**Current state:**",
    "**What remains:**",
    "**Next recommended steps:**",
    "**Context for next agent/human:**",
    "**Handoff ready:**",
]


class HandoffSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")

    def assert_contains_all(self, values: list[str]) -> None:
        for value in values:
            with self.subTest(value=value):
                self.assertIn(value, self.skill)

    def test_frontmatter_and_trigger_words(self) -> None:
        self.assertTrue(self.skill.startswith("---\nname: handoff\n"))
        description = re.search(r"^description: (?P<body>.+)$", self.skill, re.MULTILINE)
        self.assertIsNotNone(description)
        body = description.group("body")
        for trigger in ('"handoff"', '"završi"', '"proglasi handoff"', '"wrap up"'):
            with self.subTest(trigger=trigger):
                self.assertIn(trigger, body)

    def test_output_format_is_declared_strict(self) -> None:
        self.assertIn("## Output Format (strict)", self.skill)
        self.assertIn(
            "Always respond with **only** the following structure "
            "(no extra commentary before or after)",
            self.skill,
        )

    def test_all_sections_present_and_ordered(self) -> None:
        positions = []
        for section in REQUIRED_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(section, self.skill)
            positions.append(self.skill.index(section))
        self.assertEqual(
            positions, sorted(positions), "handoff sections are out of order"
        )

    def test_status_offers_the_three_outcomes(self) -> None:
        self.assertIn("**Status:** [Completed / Partially completed / Blocked]", self.skill)

    def test_current_state_captures_files_and_outputs(self) -> None:
        self.assert_contains_all(["- Files changed / created:", "- Important outputs:"])

    def test_next_steps_are_enumerated(self) -> None:
        block = self.skill[
            self.skill.index("**Next recommended steps:**") : self.skill.index(
                "**Context for next agent/human:**"
            )
        ]
        self.assertIn("1. ...", block)
        self.assertIn("2. ...", block)

    def test_rules_forbid_inventing_work(self) -> None:
        rules = self.skill[self.skill.index("## Rules") :]
        for rule in (
            "Be concise and factual.",
            "Never invent work that was not done.",
            'clearly mark it under "What remains"',
            "self-contained",
            "without reading the full chat",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, rules)


if __name__ == "__main__":
    unittest.main()
