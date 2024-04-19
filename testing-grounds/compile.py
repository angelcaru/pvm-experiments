#!/usr/bin/env python3
import sys

def main(argv: list[str]):
    program_name = argv.pop(0)
    if len(argv) != 1:
        print(f"Usage: {program_name} <filename.py>", file=sys.stderr)
        exit(1)

    filename = argv.pop(0)
    __import__(filename)
    exit(0)

if __name__ == "__main__":
    main(sys.argv)
