from setuptools import setup, find_packages

setup(
    name='repotracker',
    description='A microservice for tracking container repositories, and publishing a message when they change',
    author='Mike Bonnet',
    author_email='mikeb@redhat.com',
    version='0.0.1',
    license='GPLv3',
    url='https://github.com/release-engineering/repotracker',
    packages=find_packages(),
    tests_require=['pytest', 'mock'],
    data_files=[
        ('/etc/repotracker', ['repotracker.ini']),
    ],
    entry_points={
        'console_scripts': [
            'repotracker = repotracker.cli:main',
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    zip_safe=False,
)
