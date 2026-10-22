import unittest
from pathlib import Path

PREVIEW=(Path(__file__).resolve().parents[1]/'web/preview-v4-11.html').read_text()
class ProviderOutcomePreview(unittest.TestCase):
    def test_historical_matches_suppressed_when_result_seen(self):
        self.assertIn('provider.episode_outcome_detected',PREVIEW)
        self.assertIn('provider.episode_withdrawn',PREVIEW)
        self.assertIn('RESULTS DETECTED · FINISHED-SHOW RECAP NOT CONNECTED',PREVIEW)
        self.assertIn('SCHEDULE CHANGE REPORTED · UNVERIFIED',PREVIEW)
    def test_labels_sources_and_old_structure_retained(self):
        self.assertIn('REPORTED / UNVERIFIED',PREVIEW)
        self.assertIn('tvmaze-reported.json',PREVIEW)
        self.assertIn('research-20261022.json',PREVIEW)
        self.assertIn('#board{width:min(100vw,56.25dvh)',PREVIEW)
        self.assertIn('DISPLAY BUILD 4.11',PREVIEW)
if __name__=="__main__":unittest.main()
