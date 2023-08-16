pybabel compile -D py_extract -d locales/

python setup.py build_ext  --inplace

pyinstaller --onefile --specpath "spec" --add-data "locales;locales" -n "PyExtract" "run.py"

copy ".\config\example_config.toml"  ".\dist\"