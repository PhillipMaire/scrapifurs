from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()    


setup(
    name='scrapifurs',
    version='0.1.2',
    packages=find_packages(),
    install_requires=required,
    package_data={
        'scrapifurs': ['../data/*.txt'],
    },
    long_description=long_description,
    long_description_content_type='text/markdown'
    )







