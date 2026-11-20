from setuptools import find_packages, setup

package_name = 'umwelt_robot'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Madaki Elisha',
    maintainer_email='madakielisha@users.noreply.github.com',
    description='Robot-side nodes for umwelt: belief publishing and task execution.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'belief_node = umwelt_robot.belief_node:main',
        ],
    },
)
