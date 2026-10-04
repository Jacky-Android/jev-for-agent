import pathlib
import sys
if sys.version_info < (3,11):
    raise SystemExit('Python 3.11+ required. Use python3.11 or: uv run --python 3.11 python <script>')
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
