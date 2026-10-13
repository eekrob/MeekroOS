import json
import tempfile
from pathlib import Path
import unittest
from meekro.settings import defaults, normalize, read, write, SettingsError
from scripts.patch_kickstart import patch

class SettingsTests(unittest.TestCase):
    def test_portable_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"profile.json"
            saved=write({"selected":["steam","python","steam"],"theme":"light","blur":True,"flathub":True},path)
            self.assertEqual(read(path),saved)
            self.assertEqual(saved["selected"],["python","steam"])

    def test_disallow_bad_ids(self):
        with self.assertRaises(SettingsError):
            normalize({"selected":["any script"]})

    def test_disallow_bad_fields(self):
        with self.assertRaises(SettingsError):
            normalize({"theme":"evil"})

    def test_kickstart_overlay(self):
        ks="%packages\nfirefox\n%end\n%post\necho test\n%end\n"
        a=patch(ks)
        b=patch(a)
        self.assertEqual(a,b)
        self.assertIn("meekro-welcome",a)
        self.assertIn("%post\necho test\n%end",a)

if __name__=="__main__": unittest.main()
