import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as req:
    requirements = req.read().replace(" ", "").split("\n")

setuptools.setup(
    name="lopolis",
    version="1.0.0",
    author="mytja",
    description="Lo.Polis API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mytja/lopolis-api",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements,
    python_requires='>=3.7',
)
