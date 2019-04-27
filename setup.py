'''
pytz setup script
'''

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

me = 'Abhinav Kotak'
memail = 'in.abhi9@gmail.com'

packages = ['drf_ext', 'drf_ext.db', 'drf_ext.notification', 'drf_ext.cloudstorage']
install_requires = open('requirements.txt', 'r').readlines()

setup(
    name='drf_ext',
    version='3.8.1',
    zip_safe=True,
    description='Extensions to drf',
    author=me,
    author_email=memail,
    maintainer=me,
    maintainer_email=memail,
    install_requires=install_requires,
    url='https://github.com/inabhi9/drf-ext',
    license=open('LICENSE', 'r').read(),
    keywords=['djangorestframework'],
    packages=packages,
    platforms=['Independant'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
