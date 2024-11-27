VENV=venv
VENV_ACTIVATE=. $(VENV)/bin/activate

PYTHON=python
PYTHON_VENV=$(VENV)/bin/python

.PHONY: default
default: compile

.PHONY: venv
venv: $(VENV)/touchfile

$(VENV)/touchfile: requirements.txt
	test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	$(VENV_ACTIVATE) && pip install -Ur requirements.txt
	touch $(VENV)/touchfile

.PHONY: install-ubuntu-dependencies
install-ubuntu-dependencies: venv
	$(VENV_ACTIVATE) && apt-get update && apt-get upgrade -y && \
    apt-get -y install --no-install-suggests --no-install-recommends \
    automake \
    bison flex \
    build-essential \
    chrpath \
    git zip zsh openssh-client \
    clang clang-tools \
    python3 python3-dev python3-setuptools \
    libglib2.0-dev gcc-arm-none-eabi \
    libtool libtool-bin \
    wget curl vim \
    apt-utils apt-transport-https ca-certificates gnupg dialog \
    libpixman-1-dev \
    virtualenv python3-ipython \
    python3 python3-pip libc++-dev libcurl4-openssl-dev libelf-dev libffi-dev libdwarf-dev libelf-dev libwiretap-dev wireshark-dev python3-pycparser \
    protobuf-compiler protobuf-c-compiler python3-protobuf libprotoc-dev libprotobuf-dev libprotobuf-c-dev libjsoncpp-dev \
    gdb-multiarch python3-pip qemu-utils libcapstone-dev \
	&& apt-get update \
	&& apt-get install -y gcc-9-mipsel-linux-gnu gcc-9-multilib \
	&& update-alternatives --install /usr/bin/mipsel-linux-gnu-gcc mipsel-linux-gnu-gcc /usr/bin/mipsel-linux-gnu-gcc-9 10 \
	&& pip3 install https://foss.heptapod.net/pypy/cffi/-/archive/branch/default/cffi-branch-default.tar.gz

.PHONY: install-macos-brew-dependencies
install-macos-brew-dependencies:
	# not complete
	brew install libelf dwarfutils \
	wireshark jsoncpp capstone

.PHONY: configure

panda/build/Makefile:
	$(MAKE) configure

configure: $(VENV)/touchfile
	mkdir -p panda/build
	$(VENV_ACTIVATE) && \
	cd panda/build && \
    ../configure --disable-werror --target-list=arm-softmmu,aarch64-softmmu \
    --cc=gcc \
    --cxx=g++ \
	--extra-cxxflags="${CXXFLAGS}" \
    --disable-sdl \
    --disable-user \
    --disable-linux-user \
    --disable-pyperipheral3 \
    --disable-bsd-user \
    --disable-vte \
    --disable-curses \
    --disable-vnc \
    --disable-vnc-sasl \
    --disable-vnc-jpeg \
    --disable-vnc-png \
    --disable-cocoa \
    --disable-virtfs \
    --disable-xen \
    --disable-xen-pci-passthrough \
    --disable-brlapi \
    --disable-curl \
    --disable-bluez \
    --disable-kvm \
    --disable-hax \
    --disable-rdma \
    --disable-vde \
    --disable-netmap \
    --disable-linux-aio \
    --disable-cap-ng \
    --disable-attr \
    --disable-vhost-net \
    --disable-spice \
    --disable-rbd \
    --disable-gtk \
    --disable-gnutls \
    --disable-gcrypt \
    --disable-libiscsi \
    --disable-libnfs \
    --disable-smartcard \
    --disable-libusb \
    --disable-usb-redir \
    --disable-lzo \
    --disable-snappy \
    --disable-bzip2 \
    --disable-seccomp \
    --disable-coroutine-pool \
    --disable-glusterfs \
    --disable-tpm \
    --disable-libssh2 \
    --disable-numa \
    --disable-tcmalloc \
    --disable-jemalloc \
    --disable-replication \
    --disable-vhost-vsock \
    --disable-opengl \
    --disable-virglrenderer

.PHONY: compile
compile: venv panda/build/Makefile
	$(VENV_ACTIVATE) && cd panda/build && \
	$(MAKE) #-j `nproc` #MAKEFLAGS= # -j `nproc`
	$(VENV_ACTIVATE) && cd panda/panda/python/core/ && \
  	python3 setup.py install

	
