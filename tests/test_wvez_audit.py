import json,unittest
from proof.wvez_audit import inspect,fetch
class WvezProbe(unittest.TestCase):
    def test_no_unauthorized_urls(self):
        with self.assertRaises(ValueError):fetch('../other')
    def test_fails_closed_without_mit_license(self):
        with self.assertRaises(ValueError):inspect(b'not MIT',b'x',b'x')
if __name__=="__main__":unittest.main()
