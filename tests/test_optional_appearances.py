"""V4.10: no source-attributed appearances is normal, not a failure state."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'web/preview-v4-10.html'

class OptionalAppearancePresentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=PAGE.read_text(encoding='utf-8')

    def test_optional_panel_with_hidden_semantics(self):
        self.assertIn('id="appearance-panel"',self.html)
        self.assertIn('panel.hidden=!hasAppearances;',self.html)
        self.assertIn("const rows=evolve?[]:reportedRows(show,key,'appearances');",self.html)
        self.assertIn('if(!hasAppearances)return;',self.html)
        self.assertIn('#appearance-panel[hidden]{display:none!important}',self.html)

    def test_real_appearances_still_source_linked_and_rotating(self):
        self.assertIn("put('segment-title','REPORTED APPEARANCE · '",self.html)
        self.assertIn('const page=Math.floor(position/(keys.length===1?1:5))%rows.length;',self.html)
        self.assertIn("REPORTED / UNVERIFIED",self.html)
        self.assertIn('link.href=x.evidence_url',self.html)

    def test_no_appearance_data_dependency_or_production_mutation(self):
        self.assertIn("reportedRows(show,key,'matches')",self.html)
        self.assertIn('DISPLAY BUILD 4.10',self.html)
        self.assertIn('#board{width:min(100vw,56.25dvh)',self.html)
        self.assertIn('aspect-ratio:9/16',self.html)
        self.assertIn('tvmaze-reported.json',self.html)

if __name__ == '__main__':
    unittest.main()
