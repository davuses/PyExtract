python -m pip install -r requirements.txt
python -m pip install pyinstaller

python setup.py compile_catalog -D py_extract -d locales/

python setup.py build_ext  --inplace

pyinstaller --onefile --add-data "locales;locales" -n "PyExtract" "run.py"

copy ".\config\example_config.toml"  ".\dist\py_extract_config.toml"
