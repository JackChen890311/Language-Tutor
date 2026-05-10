import os

os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

from ui.app import main

if __name__ == "__main__":
    main()
