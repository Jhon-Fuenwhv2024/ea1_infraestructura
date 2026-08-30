from setuptools import setup, find_packages

setup(
    name="infraestructura-iud-ea1",
    version="1.0.0",
    description=(
        "EA1 - Etapa de ingesta de datos: Open Brewery DB -> MySQL "
        "(Infraestructura y arquitectura Big Data - IU Digital de Antioquia)"
    ),
    author="Jhon Jairo Fuentes Turizo",
    author_email="",
    python_requires=">=3.11",
    packages=find_packages(where=".", include=["src", "src.*"]),
    py_modules=[],
    package_dir={"": "."},
    install_requires=[
        "requests>=2.31.0",
        "pymysql>=1.1.0",
        "pandas>=2.1.0",
        "openpyxl>=3.1.0",
        "python-dotenv>=1.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
)
