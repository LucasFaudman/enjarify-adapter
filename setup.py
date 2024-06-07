from setuptools import setup, find_packages
import setuptools_scm

setup(
    name='enjarify',
    version='1.0.0',
    use_scm_version=True,
    setup_requires=['setuptools_scm>=8', 'wheel'],
    description='Enjarify is a tool for translating Dalvik bytecode to equivalent Java bytecode. This enjarify-adapter fork exports the `enjarify` method for use in external scripts and is type optimized for building with mypyc.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Lucas Faudman',
    author_email='lucasfaudman@gmail.com',
    url='https://github.com/LucasFaudman/enjarify-adapter.git',
    packages=find_packages(where='src'), 
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[],
    python_requires='>=3.7',
    license='LICENSE.txt',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='enjarify Dalvik Java Bytecode Android APK Decompiler Disassembler Reverse Engineering',
    project_urls={
        'Homepage': 'https://github.com/LucasFaudman/enjarify-adapter.git',
        'Repository': 'https://github.com/LucasFaudman/enjarify-adapter.git',
    },
    entry_points={
        'console_scripts': [
            'enjarify = enjarify.main:main',
        ],
    },
)
