from setuptools import setup, find_packages

setup(
    name='ChiaNoSSD',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'psutil',
        'python-telegram-bot[job-queue]',
        'PyYAML',
        'pyshortcuts',
        'termcolor'
],
    entry_points={
        'console_scripts': ['chianossd=chia_nossd.__main__:main',
                            'chianossd_shortcut=chia_nossd.__main__:create_shortcut'],
    },
    url='https://github.com/bds89/ChiaNoSSD',
    license='',
    author='bds89',
    author_email='bds89@mail.ru',
    description='Control and monitoring for NoSSD chia plotter and farmer'
)
