from setuptools import setup, find_packages

setup(
    name="fuentes_jhon_ea2",
    version="1.0.0",
    description="EA2 Limpieza de datos - Cervecerías (Open Brewery DB)",
    author="Jhon Jairo Fuentes Turizo",
    packages=find_packages(where="src") or [],
    py_modules=[],
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
    ],
    entry_points={
        "console_scripts": [],
    },
)
