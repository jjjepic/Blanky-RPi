import unittest

from blanky.event_columns import event_divider, event_header, event_prefix


class EventColumnsTests(unittest.TestCase):
    def test_header_divider_and_rows_share_separator_positions(self):
        row = event_prefix("[014]", "11:42:23", "BOTÃO", "MODE_MANUAL", "✓ OK") + "Descrição"
        divider = event_divider()
        for lang in ("pt", "en"):
            header = event_header(lang)
            self.assertEqual([i for i, char in enumerate(header) if char == "|"],
                             [i for i, char in enumerate(row) if char == "|"])
            self.assertEqual([i for i, char in enumerate(divider) if char == "|"],
                             [i for i, char in enumerate(row) if char == "|"])
            self.assertEqual(header.index("Descrição" if lang == "pt" else "Description"),
                             row.index("Descrição"))


if __name__ == "__main__":
    unittest.main()
