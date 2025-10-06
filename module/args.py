import argparse

def parser():
    parser = argparse.ArgumentParser(description="Computer vision module")
    parser.add_argument('--debug', action='store_true', help='Print detection log messages')
    parser.add_argument('--draw', action='store_true', help='Display debug window')
    args = parser.parse_args()
    return args
