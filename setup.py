import setuptools

setuptools.setup(
    name='lightweight-charts',
    version='0.0.2',
    description=
    'Experimental tradingview lightweight charts in python for the use in notebooks.',
    long_description=open('README.md', 'r', encoding='utf8').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/sjmillius/lightweight-charts',
    project_urls={
        "Bug Tracker": "https://github.com/sjmillius/lightweight-charts/issues"
    },
    license='Apache License 2.0',
    packages=['lightweight_charts'],
    install_requires=['apischema', 'jinja2', 'pandas'],
)