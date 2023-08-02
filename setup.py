
from setuptools import setup, find_packages



with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='scrapifurs',
    version='0.1.2',
    packages=find_packages(),
    install_requires=required,
    package_data={
        'scrapifurs': ['../data/*.txt'],
    },
    # Other metadata here...
)







