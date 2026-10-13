import unittest
from meekro.catalog import CATALOG, BY_ID, PRESETS
from meekro.backend import build_plan, InstallError
from meekro.easter import EasterEgg

class CatalogTests(unittest.TestCase):
    def test_unique_ids_and_packages(self):
        self.assertEqual(len(CATALOG),len(BY_ID))
        self.assertTrue(all(x.package and x.title for x in CATALOG))
        self.assertTrue(all(x in BY_ID for p in PRESETS.values() for x in p))

    def test_dnf_plan(self):
        p=build_plan(["python","npm"],False)
        self.assertEqual(len(p),1)
        self.assertEqual(p[0].argv[:4],("pkexec","/usr/bin/dnf5","install","--assumeyes"))
        self.assertIn("python3",p[0].argv)

    def test_flatpak_requires_consent(self):
        with self.assertRaises(InstallError):
            build_plan(["steam"],False)
        p=build_plan(["steam"],True)
        self.assertEqual(p[0].argv[0:3],("flatpak","remote-add","--user"))
        self.assertEqual(p[1].argv[-1],"com.valvesoftware.Steam")

    def test_no_injection_ids(self):
        with self.assertRaises(InstallError):
            build_plan(["python; rm -rf /"],True)

    def test_easter_exact_sequence(self):
        e=EasterEgg()
        self.assertEqual([e.feed(ch) for ch in "heeekrob_"].count(True),1)
        self.assertFalse(e.feed("x"))

if __name__=="__main__": unittest.main()
