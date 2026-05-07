import asyncio
from snowninja.repl.shell import SnowNinjaShell

def test():
    shell = SnowNinjaShell()
    print(f"Initial mode: {shell.mode}, role: {shell.model_role}")
    handled = shell._dispatch_slash("/explore")
    print(f"Handled: {handled}")
    print(f"New mode: {shell.mode}, role: {shell.model_role}")

if __name__ == "__main__":
    test()
