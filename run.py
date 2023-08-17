import traceback

from py_extract import create_py_extractor

try:
    py_extractor = create_py_extractor()
    py_extractor.run()
except Exception:
    print(traceback.format_exc())
finally:
    input("Press Enter to exit...")
