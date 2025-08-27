# dp_config_builder
This is an ansible automation script that can create/modify/delete Radware DefensePro policies and/or profiles

# Prerequisites

1. Create inventory.ini and ansible.cfg files (see inventory_example.ini and ansible_example.cfg examples from the git repository)
2. Create vars/cc.yml (see example vars/cc_example.yml )

# How to run

create /vars/cc.yml (see cc_exmple.yml for a reference)
Run from the ./dp_config_builder directory "ansible-playbook playbooks/create_network_class.yml"

# Notes

Ensure to alwasy unlock the device in event of erros in one of the tasks


delete_network_class.yml

	filter_class_name is optional variable. If set, will print only specific network class details, if not set, will print all network class details



# Version control

V0.1.0 8/19/2025
- First draft release published
- Updated logic, optimizations, improvements
- Added delete, get network classes playbooks and modules
- Added session reuse management
- Added logging

V0.1.0.1
- Cosmetics- changed "server" variable to "cc_ip" under vars/cc.yml and all dependencies

V0.1.1 (booked for Rahul)

# TBD

Further proper logging (info, debug) for the rest of the playbooks