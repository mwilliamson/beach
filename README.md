## Running tests

The tests use vagrant with the KVM plugin.

# Selecting a Vagrant provider

* vagrant plugin install vagrant-kvm
* vagrant plugin install vagrant-mutate
* vagrant mutate precise32 kvm
* vagrant mutate precise64 kvm
* vagrant mutate wheezy64 kvm
