from setuptools import setup

setup(name='matchminer',
      version='0.0.4',
      description="webserver to find clinical trial matching",
      author="James Lindsay",
      author_email="jlindsay@jimmy.harvard.edu",
      url="https://github.com/dfci/matchminer-api",
      py_modules=['matchminer'],
      install_requires=['nose', 'pandas', 'eve', 'requests'],
      scripts=["pymm_run.py"]
      )
