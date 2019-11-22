#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos_static_routes class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, dict_diff
from ansible.module_utils.network.eos.facts.facts import Facts
import re


class Static_routes(ConfigBase):
    """
    The eos_static_routes class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'static_routes',
    ]

    def __init__(self, module):
        super(Static_routes, self).__init__(module)

    def get_static_routes_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        static_routes_facts = facts['ansible_network_resources'].get('static_routes')
        if not static_routes_facts:
            return []
        return static_routes_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()
        import q
        existing_static_routes_facts = self.get_static_routes_facts()
        commands.extend(self.set_config(existing_static_routes_facts))
        if commands:
            if not self._module.check_mode:
                for command in commands:
                    self._connection.edit_config(command)
            result['changed'] = True
        result['commands'] = commands

        changed_static_routes_facts = self.get_static_routes_facts()

        result['before'] = existing_static_routes_facts
        if result['changed']:
            result['after'] = changed_static_routes_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_static_routes_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        import q
        commands = []
        data = self._connection.get('show running-config | grep route')
        want = self._module.params['config']
        have = existing_static_routes_facts
        resp = self.set_state(want, have)
        onbox_configs = data.split('\n')
        q(onbox_configs)
        for want_config in resp:
            if want_config not in onbox_configs:
                q(want_config)
                commands.append(want_config) 
        q(commands)
        return commands

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        state = self._module.params['state']
        if state == 'overridden':
            kwargs = {}
            commands = self._state_overridden(**kwargs)
        elif state == 'deleted':
            kwargs = {}
            commands = self._state_deleted(**kwargs)
        elif state == 'merged':
            kwargs = {}
            commands = self._state_merged(want,have)
        elif state == 'replaced':
            kwargs = {}
            commands = self._state_replaced(**kwargs)
        return commands
    @staticmethod
    def _state_replaced(**kwargs):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []


        return commands

    @staticmethod
    def _state_overridden(**kwargs):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        return set_commands(want, have)

    @staticmethod
    def _state_deleted(**kwargs):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        return commands
    
def set_commands(want, have):
    commands = []
    for w in want:
        import q
        return_command = add_commands(w)
        for command in return_command:
            commands.append(command)
    return commands
        # if not obj_in_have:
        #    commands = self.add_commands(w)
        # else:
        #    diff = self.diff_of_dicts(w, obj_in_have)
        #    commands = self.add_commands(diff)
        # return commands

def add_commands(want):
    commandset = []
    if not want:
        return commands
    import q
    vrf = want["vrf"] if want["vrf"] else None
    for address_family in want["address_families"]:
        for route in address_family["routes"]:
            for next_hop in route["next_hops"]:
                commands = []
                if address_family["afi"] == "ipv4":
                    commands.append('ip route')
                else:
                    commands.append('ipv6 route')
                if vrf:
                    commands.append(' vrf ' + vrf)
                if not re.search(r'/', route["dest"]):
                    mask = route["dest"].split( )[1]
                    cidr = get_net_size(mask)
                    commands.append(' ' + route["dest"].split( )[0] + '/' + cidr)
                else:
                    commands.append(' ' + route["dest"])
                q(commands)
                commands.append(' ' + next_hop["interface"])
                if next_hop["forward_router_address"]:
                    commands.append(' ' + next_hop["forward_router_address"])
                if next_hop["mpls_label"]:
                    commands.append(' label ' + str(next_hop["mpls_label"]))
                if next_hop["track"]:
                    commands.append(' track '+next_hop["track"])
                if next_hop["admin_distance"]:
                    commands.append(' '+str(next_hop["admin_distance"]))
                if next_hop["description"]:
                    commands.append(' name '+str(next_hop["description"]))
                if next_hop["tag"]:
                    commands.append(' tag '+str(next_hop["tag"]))

                config_commands = "".join(commands)
                commandset.append(config_commands)
    return commandset

def get_net_size(netmask):
    import q
    q(netmask)
    binary_str = ''
    netmask = netmask.split('.')
    for octet in netmask:
        q(octet)
        binary_str += bin(int(octet))[2:].zfill(8)
    return str(len(binary_str.rstrip('0')))
