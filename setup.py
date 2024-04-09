from setuptools import setup, find_packages
import os

here = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(here, "README.md"), "r", encoding="utf8") as fh:
    long_description = fh.read()

setup(
    name="gimpml",  # Required
    version="0.0.9",  # Required
    description="GIMP3-ML",  # Optional
    long_description=long_description,  # Optional
    long_description_content_type="text/markdown",  # Optional (see note above)
    url="",  # Optional
    author="",  # Optional
    author_email="",  # Optional
    classifiers=[  # Optional
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Graphics Editing Software :: Editors",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="ml, gimp, plugins",  # Optional
    packages=find_packages(),
    python_requires=">=3.8",
    include_package_data=True,  # to include manifest.in
    install_requires=[]
)
