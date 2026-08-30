"""Repo-wide consistency checks across every skill in .cursor/skills/.

These are structural guards that apply to any skill added later, so a new skill
cannot land with a broken frontmatter, a name/directory mismatch, or no tests.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / ".cursor/skills"
TESTS_DIR = ROOT / "tests"

FRONTMATTER = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)


def skill_files() -> list[Path]:
    return sorted(SKILLS_DIR.glob("*/SKILL.md"))


class SkillsConsistencyTests(unittest.TestCase):
    def test_skills_directory_is_not_empty(self) -> None:
        self.assertTrue(skill_files(), f"no SKILL.md found under {SKILLS_DIR}")

    def test_every_skill_has_parsable_frontmatter(self) -> None:
        for path in skill_files():
            with self.subTest(skill=path.parent.name):
                match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
                self.assertIsNotNone(match, "missing or malformed --- frontmatter block")
                keys = dict(
                    re.findall(r"^(\w+): (.+)$", match.group("body"), re.MULTILINE)
                )
                self.assertIn("name", keys)
                self.assertIn("description", keys)
                self.assertTrue(keys["description"].strip())

    def test_skill_name_matches_directory(self) -> None:
        for path in skill_files():
            directory = path.parent.name
            with self.subTest(skill=directory):
                match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
                name = dict(
                    re.findall(r"^(\w+): (.+)$", match.group("body"), re.MULTILINE)
                )["name"].strip()
                self.assertEqual(name, directory)

    def test_description_states_when_to_use_the_skill(self) -> None:
        """A description without trigger cues will not route reliably."""
        for path in skill_files():
            with self.subTest(skill=path.parent.name):
                match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
                description = dict(
                    re.findall(r"^(\w+): (.+)$", match.group("body"), re.MULTILINE)
                )["description"]
                self.assertGreaterEqual(len(description), 40)
                self.assertRegex(description, r"Use (when|for)|use when")

    def test_every_skill_has_a_test_module(self) -> None:
        for path in skill_files():
            directory = path.parent.name
            expected = TESTS_DIR / f"test_{directory.replace('-', '_')}_skill.py"
            with self.subTest(skill=directory):
                self.assertTrue(
                    expected.exists(),
                    f"skill '{directory}' has no contract tests at {expected.name}",
                )

    def test_files_are_hygienic(self) -> None:
        for path in skill_files():
            raw = path.read_text(encoding="utf-8")
            with self.subTest(skill=path.parent.name):
                self.assertTrue(raw.endswith("\n"), "file must end with a newline")
                self.assertNotIn("\t", raw, "use spaces, not tabs")
                trailing = [
                    i for i, line in enumerate(raw.splitlines(), 1) if line != line.rstrip()
                ]
                self.assertEqual(trailing, [], f"trailing whitespace on lines {trailing}")


if __name__ == "__main__":
    unittest.main()
