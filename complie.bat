python setup.py build_ext  --inplace

pyinstaller --onefile --specpath "spec" -n "PyExtract" "run.py"
