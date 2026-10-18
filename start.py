"""Create an isolated local runtime, then open SpectraCave. Python 3.10+."""
import os
from pathlib import Path
import subprocess
import sys
import venv

BASE=Path(__file__).resolve().parent

def main():
    if sys.version_info < (3,10):
        print('SpectraCave needs Python 3.10 or newer. Install Python from python.org.');return 1
    target=BASE/'.venv'
    runtime=target/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    try:
        if not runtime.exists():
            print('Preparing SpectraCave. First launch needs internet to install NumPy and Pillow.',flush=True)
            venv.EnvBuilder(with_pip=True).create(target)
        check=subprocess.run([str(runtime),'-c','import numpy; from PIL import Image'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if check.returncode:
            subprocess.run([str(runtime),'-m','pip','install','-r',str(BASE/'requirements.txt')],check=True)
        if '--check' in sys.argv[1:]:
            print('SpectraCave runtime is ready.');return 0
        return subprocess.call([str(runtime),str(BASE/'app.py'),'--open',*sys.argv[1:]],cwd=BASE)
    except (OSError,subprocess.CalledProcessError) as exc:
        print(f'Startup could not finish: {exc}\nCheck your Python installation and internet connection, then try again.');return 1

if __name__=='__main__':raise SystemExit(main())
