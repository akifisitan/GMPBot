from dataclasses import dataclass
import random


@dataclass(frozen=True)
class ServerColors:
    Red = 0xfc4a4a
    Rose = 0xfe5a8d
    DarkOrange = 0xf75829
    TealGreen = 0x1bbd9c
    Purple = 0x9b59b6
    Turquoise = 0x14c5e0
    Blue = 0x3498db
    ColorList = [Red, Rose, DarkOrange, TealGreen, Purple, Turquoise, Blue]


def random_color() -> int:
    return random.choice(ServerColors.ColorList)
