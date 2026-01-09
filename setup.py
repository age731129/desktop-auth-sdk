from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="desktop-auth-sdk",
    version="1.0.0",
    author="Ryan",
    description="Desktop application authorization SDK for shpquery.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/age731129/desktop-auth-sdk",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.25.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)