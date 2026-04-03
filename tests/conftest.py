import sys
from pathlib import Path

# Add scripts/ to path so all tests can import utils, ingest, compile, etc.
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
