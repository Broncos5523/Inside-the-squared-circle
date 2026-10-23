import unittest
from pathlib import Path
H=(Path(__file__).resolve().parents[1]/'web/preview-v4-25.html').read_text()
class EpisodeBriefFrontend(unittest.TestCase):
    def test_after_air_exact_episode_only_fallback(self):
        for term in (
           "episode-briefs.json",
           "row.airdate!==newestCompleted(show,key)",
           "function renderEpisodeSynopsis(show,key)",
           "renderEpisodeSynopsis(show,key);",
           "TVMAZE_FINISHED_EPISODE_GUIDE_SYNOPSIS_ONLY",
           "if(forceBrief&&keys.length===1)",
           "!hasReviewed&&!resultRows(k).length&&episodeSynopsis(k)",
           "row.license!=='CC BY-SA'",
        ):self.assertIn(term,H)
    def test_preserve_visual_checkpoint_and_no_links(self):
        self.assertIn('DISPLAY BUILD 4.25',H)
        self.assertIn('createRecapResult(rows[n],n)',H)
        self.assertIn('createRecapResult(results[n],n)',H)
        self.assertIn('justify-content:space-evenly;',H)
        self.assertNotIn("createElement('a')",H)
        self.assertIn("#board{width:min(100vw,56.25dvh)",H)
        self.assertIn("aspect-ratio:9/16",H)
if __name__=='__main__':unittest.main()
