from glob import glob

from setuptools import find_packages, setup

package_name = 'umwelt_viewer'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/web', glob('web/*.*')),
        ('share/' + package_name + '/web/vendor/three', glob('web/vendor/three/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Madaki Elisha',
    maintainer_email='madakielisha@users.noreply.github.com',
    description='Browser viewer that draws robot beliefs from the operator point of view.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'viewer_bridge = umwelt_viewer.bridge:main',
        ],
    },
)
