from distutils.core import setup

setup(
	name="Senselet",
	version="0.1.7",
	author="Pim P. Nijdam",
	author_email="pim.n@xs4all.nl",
	packages=["senselet", "senselet.core", "senselet.events", "senselet.actions"],
	url = "http://github.com/pimnijdam/eventScripting",
	license="LICENSE.TXT",
	description="Easily do some event based scripting.",
	long_description=open("README.txt").read(),
	install_requires=[
		"geopy",
		"oauth",
		#common-sense-python-lib, but it's not yet in the python packages
	],
)
