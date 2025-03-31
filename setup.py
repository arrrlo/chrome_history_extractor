from setuptools import setup, find_packages

import chrome_history_extractor


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='chrome_history_extractor',
    version=chrome_history_extractor.__version__,
    description='Tool for extracting chrome history',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/arrrlo/chrome_history_extractor',
    licence='MIT',
    author='arrrlo',
    packages=find_packages(),
    install_requires=[
        'click',
        'terminaltables',
        'pytest',
        'pytest-mock'
    ],
    entry_points={
        'console_scripts': [
            'chrome_history_extractor=chrome_history_extractor.cli:cli'
        ],
    },
    project_urls={
        'Source': 'https://github.com/arrrlo/chrome_history_extractor',
    },
)
