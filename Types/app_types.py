

class PosParams:
    def __init__(self, is_relative: bool, base: PosParams | None, base_name: str, margins: tuple):
        self.is_relative = is_relative
        self.base = base
        self.base_name = base_name
        self.margins = margins