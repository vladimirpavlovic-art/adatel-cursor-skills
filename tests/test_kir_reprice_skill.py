"""Contract tests for the prose-based KIR reprice skill.

The skill is a normative specification, not executable code. These tests pin the
parts a future edit must not silently drop: the hard stop before repricing, the
Art. 3.5 gate, the mapping vocabulary, and golden test C's source total.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / ".cursor/skills/kir-reprice/SKILL.md"


class KirRepriceSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")

    def assert_contains_all(self, values: list[str]) -> None:
        for value in values:
            with self.subTest(value=value):
                self.assertIn(value, self.skill)

    @staticmethod
    def flatten(text: str) -> str:
        """Collapse whitespace so assertions survive prose re-wrapping."""
        return re.sub(r"\s+", " ", text).strip()

    def assert_contains_all_flat(self, values: list[str]) -> None:
        flat_skill = self.flatten(self.skill)
        for value in values:
            with self.subTest(value=value):
                self.assertIn(self.flatten(value), flat_skill)

    def test_frontmatter(self) -> None:
        self.assertTrue(self.skill.startswith("---\nname: kir-reprice\n"))
        description = re.search(r"^description: (?P<body>.+)$", self.skill, re.MULTILINE)
        self.assertIsNotNone(description)
        self.assert_contains_all(["Art. 3.5", "reconciliation"])

    def test_engine_is_deterministic_not_an_llm_agent(self) -> None:
        self.assert_contains_all(
            [
                "Ovo **nije** generički LLM spreadsheet agent.",
                "implementirani u kodu, ne u proznom zaključivanju",
                "Nema LLM procene cena, šifara, datuma ni ugovornog statusa.",
                'Nema "pametnog" popunjavanja praznih polja.',
                "Nema fuzzy matcha kao izvora istine",
            ]
        )

    def test_all_required_inputs_are_declared(self) -> None:
        self.assert_contains_all(
            [
                "KIR xlsx kartica",
                "stari Telekom OPEX cenovnik",
                "novi Telekom OPEX cenovnik",
                "old↔new mapping tabela",
                "effective dates",
                "commercial-rules tabela",
                "execution/signature/status metadata",
            ]
        )
        self.assertIn("Ne nastavljaj sa parcijalnim ulazom.", self.skill)

    def test_pipeline_steps_are_complete_and_ordered(self) -> None:
        steps = [
            "1. **Parse source workbook**",
            "2. **Canonical line-item ledger**",
            "3. **Reprodukuj originalni source total**",
            "4. **Hard stop**",
            "5. **Map old/new codes**",
            "6. **Technical value**",
            "7. **Contractual value**",
            "8. **Art. 3.5 rule**",
            "9. **Out-of-scope**",
            "10. **Exception queue**",
            "11. **Output**",
        ]
        positions = []
        for step in steps:
            with self.subTest(step=step):
                self.assertIn(step, self.skill)
            positions.append(self.skill.index(step))
        self.assertEqual(positions, sorted(positions), "pipeline steps are out of order")

    def test_hard_stop_precedes_repricing(self) -> None:
        """Step 4 must abort before mapping and repricing, not warn and continue."""
        self.assertIn("Ne repricing, ne mapping, ne report.", self.skill)
        self.assertIn("Mismatch source totala je hard stop, ne warning.", self.skill)
        hard_stop = self.skill.index("4. **Hard stop**")
        mapping = self.skill.index("5. **Map old/new codes**")
        self.assertLess(hard_stop, mapping)

    def test_mapping_classification_vocabulary(self) -> None:
        self.assert_contains_all(["`EXACT`", "`MAPPED`", "`SPLIT_MERGE`", "`REVIEW`", "`EXTRA`"])
        self.assertIn("svaka stavka dobija tačno jednu klasifikaciju", self.skill)
        self.assertIn("ne zaključuje automatski", self.skill)

    def test_art_35_gate_requires_both_conditions(self) -> None:
        gate = self.skill[self.skill.index("## Art. 3.5 gate") : self.skill.index("## Output")]
        for fragment in (
            "70% stopu isključivo kada su oba uslova eksplicitno potvrđena",
            "**Base condition**",
            "**Effective-date condition**",
            "Nema delimične primene",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, gate)
        self.assertIn("70% verifikovane DOT→Telekom stope", self.skill)
        self.assert_contains_all_flat(
            ["Nikada se ne primenjuje Art. 3.5 automatski na out-of-scope stavke."]
        )

    def test_technical_and_contractual_values_stay_separate(self) -> None:
        self.assert_contains_all_flat(
            [
                "Dve vrednosti se nikada ne mešaju u istoj koloni.",
                "Technical i contractual vrednost ostaju razdvojene kroz ceo pipeline.",
            ]
        )

    def test_golden_tests_and_regression_total(self) -> None:
        golden = self.skill[self.skill.index("## Obavezni golden testovi") : self.skill.index("## Hard rules")]
        self.assertIn("Engine se ne smatra ispravnim dok sva tri ne prolaze", golden)
        self.assertIn("**A** — jedna zatvorena OLD-price kartica.", golden)
        self.assertIn("**B** — jedna zatvorena NEW-price kartica.", golden)
        self.assertIn("**499.594,04 RSD**", golden)
        self.assertIn("regression guard za korak 3/4", golden)
        self.assertIn('ne "popravljaj" ga podešavanjem repricing logike', golden)

    def test_hard_rules_are_intact(self) -> None:
        rules = self.skill[self.skill.index("## Hard rules") :]
        for rule in (
            "Nikada ne nagađaj šifru, cenu, datum ili ugovorni status.",
            "Nepotvrđeno ≠ nula.",
            "decimalne aritmetike, ne float-a",
            "Svaka izlazna cifra mora imati trag do ulaznog reda i primenjenog pravila.",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, rules)

    def test_outputs_are_reproducible_and_auditable(self) -> None:
        self.assert_contains_all(
            [
                "XLSX reconciliation report",
                "machine-readable audit file",
                "isti ulaz → bajt-identičan rezultat",
            ]
        )


if __name__ == "__main__":
    unittest.main()
