#!/bin/sh

cd pantheon

sudo sysctl -w net.ipv4.ip_forward=1

cd src/wrappers/

chmod 755 sprout-ewma.py
chmod 755 sprout-ma.py
chmod 755 sprout-sewma.py
chmod 755 sprout-oracle.py
chmod 755 sprout-fadi.py

#The chmod for sprout delay variants might not be needed as they are still linked to the main one, but included for security

chmod 755 sprout-0.py
chmod 755 sprout-5.py
chmod 755 sprout-25.py
chmod 755 sprout-50.py
chmod 755 sprout-75.py

cd ..
cd ..

chmod -R 755 third_party/sprout-ewma/
chmod -R 755 third_party/sprout-ma/
chmod -R 755 third_party/sprout-sewma/
chmod -R 755 third_party/sprout-oracle/
chmod -R 755 third_party/sprout-fadi/

#Same applies here
chmod -R 755 third_party/sprout-0/
chmod -R 755 third_party/sprout-5/
chmod -R 755 third_party/sprout-25/
chmod -R 755 third_party/sprout-50/
chmod -R 755 third_party/sprout-75/

#Might want to consider downloading this package in the actual setup pantheon script
#Note: Eigen is header based and so there is no need to compile anything

mkdir third_party/sprout-fadi/src/extern_utils

cd third_party/sprout-fadi/src/extern_utils
wget https://gitlab.com/libeigen/eigen/-/archive/3.3.9/eigen-3.3.9.tar
tar -xvf eigen-3.3.9.tar

cd ../../../../

#Setup the schemes you want, but will be done later on as well
src/experiments/setup.py --schemes "cubic sprout vivace verus copa"

#Move back from pantheon dir
cd ..

### Will need most recent cmake version ###

sudo apt remove cmake #Uninstall current version

# Solve broken apt_pkg package
cd /usr/lib/python3/dist-packages/
sudo ln -s apt_pkg.cpython-36m-x86_64-linux-gnu.so apt_pkg.so

# Go back to main directory
cd /local/repository/scripts/

sudo bash install_kitware_repo.sh

sudo apt-get install cmake

### Install Frugally-Deep - Will allow us to port models to C++ ###

sudo bash install_frugally_deep.sh




