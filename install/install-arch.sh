#! /bin/bash

# get the directory where the script was run
# get the directory where the script was run
if [ -L $0 ] ; then
    FULL_SCRIPT_NAME=$(readlink $0)
else
    FULL_SCRIPT_NAME=$0
fi
BASE_DIR=$(dirname $FULL_SCRIPT_NAME)

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

# check if this is arch linux
if [ -z "$(uname -a | grep -m 1 'ARCH')" ]; then
    echo "This installation is for arch linux only"
    exit 1
fi

# retrieve the current user, this user must be able to sudo
HOMEPI_USER=$(whoami)
if [ -z "$(groups | grep -m 1 'sudo')" ]; then
    # not a member of sudo
    echo "$HOMEPI_USER is not a member of sudo" >&2
    exit 1
fi
HOMEPI_USER_HOME=$HOME

echo "Updating the system first..."
sudo pacman -Syu --noconfirm --needed

echo "Installing base-devel..."
sudo pacman -S base-devel --noconfirm --needed

YAOURT=$(which yaourt)
if [ -z "$YAOURT" ]; then
    echo "Installing yaourt..."
    curl -O https://aur.archlinux.org/packages/pa/package-query/package-query.tar.gz
    tar zxvf package-query.tar.gz
    cd package-query
    sudo makepkg -si --asroot
    cd ..
    curl -O https://aur.archlinux.org/packages/ya/yaourt/yaourt.tar.gz
    tar zxvf yaourt.tar.gz
    cd yaourt
    sudo makepkg -si --asroot
    cd ..

    # clean up
    sudo rm -rf package-query*
    sudo rm -rf yaourt*
fi

echo "Installing PiGpioWeb..."

echo "Installing python2 ..."
sudo pacman -S python2 --noconfirm --needed
PYTHON=$(which python2)
if [ -z "$PYTHON" ]; then
    echo "Unable to install python 2" >&2
    exit 1
fi

# install pip
PIP=$(which pip2)
if [ -z "$PIP" ]; then
    echo "Installing pip..."
    sudo pacman -S python2-pip --noconfirm --needed
    PIP=$(which pip2)
fi

# install webpy
echo "Installing webpy..."
sudo pacman -S python2-webpy --noconfirm --needed

# install RPi.GPIO module
echo "Installing RPi.GPIO..."
sudo $PIP --exists-action=i install RPi.GPIO

# install systemd service
SYSTEMD_DIR=/usr/lib/systemd/system
sed -e 's|${PYTHON}|'$PYTHON'|g' -e 's|${HOMEPI_USER_HOME}|'$HOMEPI_USER_HOME'|g' \
    systemd/PiGpioWeb.template >systemd/PiGpioWeb.service
sudo mv systemd/PiGpioWeb.service $SYSTEMD_DIR/
sudo systemctl enable PiGpioWeb.service

LIRCD_INSTALL=$(prompt_yes_no "Do you want to install lirc package? (Y/N)")
if [ $LIRCD_INSTALL = "Y" ]; then
    LIRCD_DRIVER=$(prompt_ask_info "Please enter lirc driver to use (e.g. usb_uirt_raw):")
    LIRCD_DEVICE=$(prompt_ask_info "Please enter lirc device to use (e.g. /dev/usbuirt):")
    echo "Installing lirc package..."
    sudo pacman -S lirc --noconfirm --needed
    sudo systemctl disable lircd.service
    sudo systemctl disable lircmd.service
    LIRCD=$(which lircd)
    
    # setup PiLircd service
    sed -e 's|${LIRCD}|'$LIRCD'|g' -e 's|${LIRCD_DRIVER}|'$LIRCD_DRIVER'|g' \
        -e 's|${LIRCD_DEVICE}|'$LIRCD_DEVICE'|g' -e 's|${HOMEPI_USER_HOME}|'$HOMEPI_USER_HOME'|g' \
        systemd/PiLircd.template >systemd/PiLircd.service
    sudo mv systemd/PiLircd.service $SYSTEMD_DIR/
    sudo systemctl enable PiLircd.service

    # setup PiLircControl.service
    sudo $PIP --exists-action=i install python-lirc

    sed -e 's|${PYTHON}|'$PYTHON'|g' -e 's|${HOMEPI_USER_HOME}|'$HOMEPI_USER_HOME'|g' \
        systemd/PiLircControl.template >systemd/PiLircControl.service
    sudo mv systemd/PiLircControl.service $SYSTEMD_DIR/
    sudo systemctl enable PiLircControl.service
fi

# wakeonlan facility
sudo $PIP --exists-action=i install wakeonlan

# install pywapi for weather report
echo "Installing pywapi for weather reports..."
sudo $PIP install pywapi --allow-unverified pywapi --allow-external pywapi --exists-action=i

# install feedparser for news report
echo "Installing feedparser for news reports..."
sudo $PIP --exists-action=i install feedparser

# prepare environment for SpeechCommander
echo "Installing alsa..."
sudo pacman -S alsa-utils alsa-firmware alsa-lib alsa-plugins --noconfirm --needed

sudo usermod -a -G video,audio $HOMEPI_USER
amixer -c 0 set PCM 100%

# install bluetooth support
# sudo pacman -S pulseaudio-alsa bluez bluez-libs bluez-utils bluez-firmware --noconfirm --needed
# sudo systemctl enable bluetooth
# sudo systemctl start bluetooth

echo "It's easier to use bluez and btsco for bluetooth headset support."
echo "Bluez4 and btsco installation might take a while."
BLUETOOTH_INSTALL=$(prompt_yes_no "Do you want to install bluetooth support? (Y/N)")
if [ $BLUETOOTH_INSTALL = "Y" ]; then
    # install bluez4 from AUR
    $YAOURT -S bluez4 btsco --noconfirm --needed
fi

# install flac and mpg123
echo "Installing flac and mpg123..."
sudo pacman -S flac mpg123 --noconfirm --needed

