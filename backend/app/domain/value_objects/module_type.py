from enum import Enum


class ModuleType(str, Enum):
    SCREEN = "screen"
    API = "api"
    BATCH = "batch"
