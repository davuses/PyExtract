from babel.messages import frontend as babel
from Cython.Build import cythonize
from Cython.Distutils import Extension
from setuptools import setup

extra_compile_args = ["-O3", "-ffast-math", "-fopenmp"]
extra_link_args = ["-fopenmp"]

lib_modules = []

lib_modules.append(
    Extension(
        "py_extract.zip_decrypter",
        ["py_extract/zip_decrypter.pyx"],
        language="c",
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
)

setup(
    name="zip_decrypter",
    zip_safe=False,
    ext_modules=cythonize(
        lib_modules,
        language_level=3,
        compiler_directives={"always_allow_keywords": True},
    ),
    cmdclass={"compile_catalog": babel.compile_catalog},
)
