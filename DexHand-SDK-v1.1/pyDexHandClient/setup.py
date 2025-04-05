from setuptools import setup, find_packages

setup(
    name="dexhand_client",
    version="1.0.6",
    packages=find_packages(exclude=["examples*"]),
    install_requires=[
        "numpy",
        "colorlog",
    ],
    package_data={
        "dexhand_client": ["config/*.json"],
    },
    include_package_data=True,
    author="Acorn Robotics",
    author_email="autorobotlab@126.com",
    description="The Python API of DexHand, providing interfaces to control DexHand and read DexHand information.",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
)
