from snowninja.repl.shell import SnowNinjaShell

def test():
    shell = SnowNinjaShell()
    shell._dispatch_slash("/models")

if __name__ == "__main__":
    test()
