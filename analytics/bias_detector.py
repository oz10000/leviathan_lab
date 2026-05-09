import re

def detect_lookahead(code):
    flags = []
    # check for shift(1) when using rolling/rank
    if 'rolling' in code and 'shift(1)' not in code:
        flags.append("Possible lookahead: missing shift(1) in rolling calculations")
    # additional checks...
    return flags
