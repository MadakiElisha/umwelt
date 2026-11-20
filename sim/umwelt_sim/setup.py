from glob import glob

from setuptools import find_packages, setup

package_name = 'umwelt_sim'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/worlds', glob('worlds/*.sdf')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Madaki Elisha',
    maintainer_email='madakielisha@users.noreply.github.com',
    description='Gazebo worlds and launch files for umwelt.',
    license='Apache-2.0',
    tests_require=['pytest'],
)
