from Types.Listerners.Pos import PosBase


class PosParams:
    def __init__(self, is_relative: bool, base: PosBase | None | str, base_name: str | None, margins: tuple):
        self.is_relative = is_relative
        self.base = base
        self.base_name = base_name
        self.margins = margins