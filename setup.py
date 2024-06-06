from setuptools import setup, find_packages
from pathlib import Path

setup(
    name="enjarify",
    version="0.1.0",
    description="Enjarify is a tool for translating Dalvik bytecode to equivalent Java bytecode. This enjarify-adapter fork is type optimized for mypyc, pip installable and exports the 'enjarify' methods for use in external scripts",
    long_description=(Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/LucasFaudman/enjarify-adapter.git",
    author="Lucas Faudman, 2015 Google Inc.",
    author_email="lucasfaudman@gmail.com",
    license="Apache License 2.0",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
    ],
    entry_points={
        "console_scripts": [
            "enjarify=enjarify.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    zip_safe=False,
)
