
if __name__ == "__main__":
    import sys
    import ablector.cmd.Run

    cmd = ablector.cmd.Run.helpCmd
    if len(sys.argv) >= 1:
        # TODO: More advanced argument parsing...
        sys.argv = sys.argv[1:]
        cmd = ablector.cmd.Run.main
    cmd(sys.argv)