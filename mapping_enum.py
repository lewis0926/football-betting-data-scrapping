from enum import Enum


# Home/Away/Draw (主客和)
# Handicap HAD (讓球主客和)
# Handicap (讓球)
class OddTypeEnum(Enum):
    HomeAwayDraw = "had"
    HandicapHAD = "hha"
    Handicap = "hdc"
    HiLo = "hil"


class CompetitionEnum(Enum):
    UEChampions = "50000017"
