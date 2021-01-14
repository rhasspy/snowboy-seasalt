import os
import sys
import platform

if platform.system() == "Darwin":
    sys.path.insert(
        0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib/osx/pmdl")
    )
    from snowboy import *
else:
    sys.path.insert(
        0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib/ubuntu64/pmdl")
    )
    from snowboy import *
