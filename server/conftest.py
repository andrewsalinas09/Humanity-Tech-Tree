import os
import sys

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "kernel"))
sys.path.insert(0, os.path.join(ROOT, "backend"))
