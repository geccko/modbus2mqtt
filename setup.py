#!/usr/bin/python3
import os
from setuptools import setup, find_packages
import codecs


def read(fname):
    with codecs.open(os.path.join(__file__), 'r') as fp:
        return fp.read()


def set_data_files():
    data_files = [
        ('/etc/modbus2mqtt/', [modbus2mqtt.conf]),
        ('/etc/modbus2mqtt/', [DDS238.csv]),
        ('/etc/systemd/system/', ['modbus2mqtt.service']),
    ]
    if not os.path.isfile('/etc/modbus2mqtt/modbus2mqtt.conf'):
        data_files.append(('/etc/modbus2mqtt/', ['modbus2mqtt.conf']))
    return data_files


setup(
    name='modbus2mqtt',
    version='0.6',
    packages=find_packages(),
    scripts=['modbus2mqtt.py'],
    package_data={
        '': ['*.rst'],
    },
    include_package_data=True,
    data_files=set_data_files(),
    description=
    'Modbus to MQTT server',
    license='MIT',
    long_description=read("README.rst"),
    author='Louis Lagendijk based on version by Oliver Wagner owagner@tellerulam.com',
    author_email='louis.lagendijk@gmail.com',
    install_requires=['configparser', 'paho-mqtt', 'argparse', 'modbus-tk'],
    classifiers=[
        "Environment :: No Input/Output (Daemon)",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: "
    ])
