import argparse

def parser():
    parser = argparse.ArgumentParser(description="Computer vision server")
    parser.add_argument('--debug', action='store_true', help='Print detection log messages')
    parser.add_argument('--draw', action='store_true', help='Display debug window')
    parser.add_argument('--shadow', action='store_true', help='Track without publishing official outputs')
    args = parser.parse_args()
    return args