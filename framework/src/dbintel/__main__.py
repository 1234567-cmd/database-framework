"""Allow ``python -m dbintel``."""
import sys

from .cli import main

sys.exit(main())
