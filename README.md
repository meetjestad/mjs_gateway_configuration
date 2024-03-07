Ansible and system names
------------------------
All managed systems are listed in `inventory.yaml`, to let Ansible know
where to find them and what hardware they use.

By default, Ansible deploys changes to all listed hosts. To deploy to
only those, you can use the `--limit` option.

The inventory contains a `rockpi-s` entry, which is intended to be used
for local testing until a host gets a proper name.

Below, all commands use `--limit some_host` to run against a single host, make
sure to change that to whatever host you are working with.

Setting up a Rock Pi S
----------------------
Start with a base Debian image, minimal flavor. Can be downloaded from:

  https://www.armbian.com/rockpi-s/

Steps:
 - Flash image on SD card
 - Login (with root:1234) and walk through the setup wizard (create user
   debian, passwords do not matter)
 - Setup key authentication for root (e.g. with ssh-copy-id)
 - Add to inventory (or use existing maybe)
 - Run initial sync:

        ansible-playbook -i inventory.yaml playbook.yaml --limit rockpi-s
