import unittest
from pathlib import Path
H=(Path(__file__).resolve().parents[1]/'web/preview-v4-22.html').read_text()
class RecapReadability(unittest.TestCase):
    def test_two_result_card_larger_and_vertically_distributed(self):
        self.assertIn('DISPLAY BUILD 4.22',H)
        self.assertIn('#board.is-recap #card.two-result-mode{',H)
        self.assertIn('justify-content:space-evenly;',H)
        self.assertIn('font-size:3.2cqw;',H)
        self.assertIn('font-size:2.92cqw;',H)
        self.assertIn('createRecapResult(results[n],n)',H)
        self.assertIn('createRecapResult(rows[n],n)',H)
    def test_no_data_change_or_unwanted_labels(self):
        self.assertNotIn("createElement('a')",H)
        self.assertNotIn('REPORTED / UNVERIFIED · FINISHED SHOW',H)
        self.assertIn("x.status==='REPORTED_UNVERIFIED'",H)
        self.assertIn('record.airdate!==show.previous?.date',H)
        self.assertIn('televisionBroadcastFinished(past,key)',H)
    def test_portrait_size_and_latest_live_board(self):
        self.assertIn('#board{width:min(100vw,56.25dvh)',H)
        self.assertIn('aspect-ratio:9/16',H)
        self.assertIn("showReportedCard(show,key,evolve);",H)
        self.assertIn("renderEvolveRecap(show);",H)
if __name__=='__main__':unittest.main()
