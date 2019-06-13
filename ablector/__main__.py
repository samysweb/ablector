
if __name__ == "__main__":
    import sys
    import ablector.src.cmd.Run

    cmd = ablector.src.cmd.Run.helpCmd
    if len(sys.argv) >= 1:
        # TODO (steuber): More advanced argument parsing...
        sys.argv = sys.argv[1:]
        cmd = ablector.src.cmd.Run.main
    cmd(sys.argv)