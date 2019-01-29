import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ufarc",
    version="0.1.0",
    author="Dean Hall",
    author_email="dwhall256@gmail.com",
    description="Framework for Asyncio AHSM Run-to-completion Concurrency for MicroPython",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dwhall/ufarc",
    packages=setuptools.find_packages(),
    classifiers=[
        # Python 3.4 (or later) because asyncio is required
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: MicroPython",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
