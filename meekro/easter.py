"""Keyboard-only developer Easter egg; no global keylogging."""
class EasterEgg:
    SECRET = "eekrob_"
    def __init__(self):
        self._tail = ""
    def feed(self, key: str) -> bool:
        if len(key) != 1 or not key.isprintable():
            self._tail = ""
            return False
        self._tail = (self._tail + key.casefold())[-len(self.SECRET):]
        if self._tail == self.SECRET:
            self._tail = ""
            return True
        return False
