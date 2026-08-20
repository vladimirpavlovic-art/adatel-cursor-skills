"""Contract tests for the prose-based ADATEL mail triage skill."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / ".cursor/skills/adatel-mail-triage/SKILL.md"


class AdatelMailTriageSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")

    def assert_contains_all(self, values: list[str]) -> None:
        for value in values:
            with self.subTest(value=value):
                self.assertIn(value, self.skill)

    def test_frontmatter_and_account_scope(self) -> None:
        self.assertTrue(self.skill.startswith("---\nname: adatel-mail-triage\n"))
        self.assertIn("vladimir.pavlovic@adatel.rs", self.skill)
        self.assertIn("Business / Codex", self.skill)

    def test_thread_reducer_contract(self) -> None:
        self.assert_contains_all(
            [
                "previous_state:",
                "new_state:",
                "state_change:",
                "new_fact:",
                "resolved_fact:",
                "remaining_blocker:",
                "next_action:",
                "`SUPERSEDED`",
                "`previous_state == new_state`",
            ]
        )

    def test_lifecycle_and_parallel_flags_are_complete(self) -> None:
        self.assert_contains_all(
            [
                "`NEW`",
                "`INFO_MISSING`",
                "`READY_TO_WORK`",
                "`IN_PROGRESS`",
                "`EXECUTED_PENDING_CLOSEOUT`",
                "`DOCUMENTATION_INCOMPLETE`",
                "`DOCUMENTATION_COMPLETE`",
                "`READY_TO_INVOICE`",
                "`INVOICED`",
                "`CLOSED`",
                "`URGENT`",
                "`BLOCKED`",
                "`DISPUTED`",
                "`ON_HOLD`",
                "`CLIENT_ESCALATION`",
                "`COMMERCIAL_RISK`",
                "`AUTHORITY_CONFLICT`",
            ]
        )

    def test_readiness_is_not_urgency(self) -> None:
        self.assertIn("`URGENT != READY_TO_WORK`", self.skill)
        self.assert_contains_all(
            [
                "KIR / radni dokument",
                "Jednoznačan scope",
                "Količina",
                "Lokacija / element",
                "Materijal",
                "Pristup / mehanizacija",
                "Telekom/client support",
                "Prioritet i authority",
                "`PASS`, `FAIL` ili `N/A`",
            ]
        )

    def test_billing_states_remain_separate(self) -> None:
        billing_block = re.search(
            r"## Billing state\n(?P<body>.*?)\n## Responsibility attribution",
            self.skill,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(billing_block)
        body = billing_block.group("body")
        for state in (
            "work_executed",
            "signed",
            "documentation_complete",
            "ready_to_invoice",
            "invoiced",
            "paid",
        ):
            with self.subTest(state=state):
                self.assertIn(state, body)
        self.assertIn("„Možete poslati račun”", body)
        self.assertIn("ne `READY_TO_INVOICE`", body)

    def test_responsibility_and_dispute_contracts(self) -> None:
        self.assert_contains_all(
            [
                "ADATEL | DOT | TELEKOM | SHARED | UNKNOWN",
                "EXECUTION_FAILURE",
                "MISSING_INPUT",
                "DOCUMENTATION_DELAY",
                "APPROVAL_DELAY",
                "MATERIAL_BLOCKER",
                "ACCESS_BLOCKER",
                "CONFLICTING_PRIORITY_AUTHORITY",
                "accepted_facts:",
                "disputed_facts:",
                "resolved_issues:",
                "open_issues:",
                "decision_already_accepted:",
                "requested_exception_or_carve_out:",
            ]
        )

    def test_unread_review_is_deduplicated_and_safe(self) -> None:
        self.assertIn("## UNREAD_REVIEW mode", self.skill)
        self.assertIn(
            "| # | Topic/thread | Priority | State | Why keep unread | Action |",
            self.skill,
        )
        self.assert_contains_all(
            [
                "`KEEP_UNREAD`",
                "`READ_CLOSE`",
                "`WATCH`",
                "Jedna poslovna nit = jedan red",
                "zamrzni ih do kraja run-a",
                "Predloženi `READ_CLOSE` nije dozvola za mark-read",
            ]
        )

    def test_real_world_fixtures_a_through_f(self) -> None:
        fixture_titles = {
            "A": "urgent scope mutates",
            "B": "CAV ready for invoice",
            "C": "signed but incomplete",
            "D": "strategic stop + operational dispute",
            "E": "work executed but closeout missing",
            "F": "authority conflict",
        }
        for letter, title in fixture_titles.items():
            with self.subTest(fixture=letter):
                self.assertEqual(
                    self.skill.count(f"### TEST {letter} — {title}"),
                    1,
                )

    def test_fixture_expected_outcomes(self) -> None:
        expected_signals = {
            "A": ["`3 wooden`", "`6 concrete`", "`SUPERSEDED`"],
            "B": ["`ready_to_invoice: CONFIRMED`", "`READY_TO_INVOICE`"],
            "C": ["`signed: CONFIRMED`", "`DOCUMENTATION_INCOMPLETE`"],
            "D": ["`decision_already_accepted`", "`open_issues`"],
            "E": ["`EXECUTED_PENDING_CLOSEOUT`", "official number", "log signature"],
            "F": [
                "`AUTHORITY_CONFLICT`",
                "`CONFLICTING_PRIORITY_AUTHORITY`",
                "`SHARED`",
                "`UNKNOWN`",
            ],
        }
        for letter, expected in expected_signals.items():
            start = self.skill.index(f"### TEST {letter} —")
            next_fixture = re.search(r"\n### TEST [A-F] —", self.skill[start + 1 :])
            end = (
                start + 1 + next_fixture.start()
                if next_fixture
                else self.skill.index("\n## Regression guardovi", start)
            )
            fixture = self.skill[start:end]
            for signal in expected:
                with self.subTest(fixture=letter, signal=signal):
                    self.assertIn(signal, fixture)

    def test_backward_compatibility_guards(self) -> None:
        self.assert_contains_all(
            [
                "Minimax grouping",
                "Drive structural signals",
                "Compliance qualification",
                "Client/Partner Meeting Pack",
                "Mark-read safety",
            ]
        )

    def test_required_changelog_entries(self) -> None:
        changelog = self.skill[self.skill.index("## Changelog") :]
        for entry in (
            "thread-state reducer",
            "readiness i urgency",
            "billing",
            "responsibility attribution",
            "prihvaćene odluke od otvorenih pitanja",
            "`UNREAD_REVIEW`",
        ):
            with self.subTest(entry=entry):
                self.assertIn(entry, changelog)


if __name__ == "__main__":
    unittest.main()
