from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import Extension

extra_compile_args = ["-O3", "-ffast-math", "-fopenmp"]
extra_link_args = ["-fopenmp"]

lib_modules = []

lib_modules.append(
    Extension(
        "zip_decrypter",
        ["zip_decrypter.pyx"],
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
)
