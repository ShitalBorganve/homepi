#! /bin/bash

prompt_yes_no() {
    while true; do
        read -p "$1" yn
        case $yn in
            [Yy]* ) echo "Y"; break;;
            [Nn]* ) echo "N"; break;;
            * ) echo "Please enter Y or N." >&2;;
        esac
    done
}

prompt_ask_info() {
    while true; do
        read -p "$1" response
        if [ ! -z "$response" ]; then
            echo "$response"; break
        else
            echo "Please provide input." >&2
        fi
    done
}

install_init() {
	if [ -f "$BASE_DIR/init.d/$1" ]; then
		sudo cp $BASE_DIR/init.d/$1 $INIT_DIR/
		rm -f $BASE_DIR/init.d/$1
		sudo chmod a+x $INIT_DIR/$1
		sudo update-rc.d $1 defaults
	fi
}

# get the directory where the script was run
if [ -L $0 ] ; then
    FULL_SCRIPT_NAME=$(readlink $0)
else
    FULL_SCRIPT_NAME=$0
fi
BASE_DIR=$(dirname $FULL_SCRIPT_NAME)

HOMEPI_USER=$(whoami)
HOMEPI_USER_HOME=$HOME
INIT_DIR=/etc/init.d

# refresh repository cache
# sudo apt-get update

# only compatible on python 2, do not use on python 3
PYTHON=$(which python2)
if [ -z "$PYTHON" ]; then
	sudo apt-get install python --yes
fi

# install python package install (pip)
PIP=$(which pip)
if [ -z "$PIP" ]; then
	sudo apt-get install python-pip --yes
	PIP=$(which pip)
fi

# install dependencies for PiGpioWeb
sudo apt-get install python-rpi.gpio python-webpy --yes

# install init for PiGpioWeb
sed -e 's|${::HOMEPI_USER::}|'$HOMEPI_USER'|g' $BASE_DIR/init.d/PiGpioWeb.template >$BASE_DIR/init.d/PiGpioWeb
install_init PiGpioWeb

# install lirc
LIRCD_INSTALL=$(prompt_yes_no "Do you want to install lirc package? (Y/N)")
if [ $LIRCD_INSTALL = "Y" ]; then
	# this is applicable only if using usbuirt
	sudo ln -sf $HOMEPI_USER_HOME/homepi/udev/rules.d/10-usb-serial.rules /etc/udev/rules.d/

    LIRCD_DRIVER=$(prompt_ask_info "Please enter lirc driver to use (e.g. usb_uirt_raw):")
    LIRCD_DEVICE=$(prompt_ask_info "Please enter lirc device to use (e.g. /dev/usbuirt):")
    echo "Installing lirc package..."
	sudo apt-get install lirc python-lirc --yes
    LIRCD=$(which lircd)
	sudo update-rc.d -f lirc remove
	sudo rm -f $INIT_DIR/lirc

    # setup PiLircd service
    sed -e 's|${::LIRCD_DRIVER::}|'$LIRCD_DRIVER'|g' -e 's|${::LIRCD_DEVICE::}|'$LIRCD_DEVICE'|g' \
		-e 's|${::HOMEPI_USER::}|'$HOMEPI_USER'|g' \
        $BASE_DIR/init.d/PiLircd.template >$BASE_DIR/init.d/PiLircd
	install_init PiLircd

	# install dependencies for PiLircControl
	sudo $PIP install wakeonlan pywapi feedparser

	# setup PiLircControl service
	sed -e 's|${::HOMEPI_USER::}|'$HOMEPI_USER'|g' \
		$BASE_DIR/init.d/PiLircControl.template >$BASE_DIR/init.d/PiLircControl
	install_init PiLircControl
fi
