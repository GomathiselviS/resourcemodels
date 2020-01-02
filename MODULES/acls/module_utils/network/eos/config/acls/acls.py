#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos_acls class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.common.utils import remove_empties
from ansible.module_utils.network.eos.facts.facts import Facts


class Acls(ConfigBase):
    """
    The eos_acls class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'acls',
    ]

    def __init__(self, module):
        super(Acls, self).__init__(module)

    def get_acls_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        acls_facts = facts['ansible_network_resources'].get('acls')
        if not acls_facts:
            return []
        return acls_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_acls_facts = self.get_acls_facts()
        else:
            existing_acls_facts = []
        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_acls_facts))
        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                for command in commands:
                    self._connection.edit_config(commands)
            result['changed'] = True
        if self.state in self.ACTION_STATES:
            result['commands'] = commands
        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_acls_facts = self.get_acls_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        elif self.state == 'parsed':
            result['parsed'] = self.get_acls_facts(data=self._module.params['running_config'])
        else:
            changed_acls_facts = []
        if self.state in self.ACTION_STATES:
            result['before'] = existing_acls_facts
            if result['changed']:
                result['after'] = changed_acls_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_acls_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_acls_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        config = self._module.params.get('config')
        want = []
        if config:
            for w in config:
                want.append(remove_empties(w))
        have = existing_acls_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        if self.state in ('merged', 'replaced', 'overridden') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(self.state))
        state = self._module.params['state']
        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged':
            commands = self._state_merged(want, have)
        elif state == 'replaced':
            commands = self._state_replaced(want, have)
        return commands

    @staticmethod
    def _state_replaced(want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        return commands

    @staticmethod
    def _state_overridden(want, have):
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
        import q
        commands = []
        for w in want:
            commands.append(set_commands(want, have))
        return commands

    @staticmethod
    def _state_deleted(want, have):
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
        return_command = add_commands(w)
        for command in return_command:
            commands.append(command)
    return commands

def add_commands(want):
    commandset = []
    if not want:
        return commandset
    import q
    q(want)
    command = ""
    afi = "ip" if want["afi"] == "ipv4" else "ipv6"
    for acl in want["acls"]:
        if "standard" in acl.keys() and acl["standard"]:
            command = afi + " access-list standard " + acl["name"]
        else:
            command = afi + " access-list " + acl["name"]
        commandset.append(command)
        for ace in want["aces"]:
            command = ""
            if "sequence" in ace.keys():
                command = ace["sequence"]
            command = command + " " + ace["grant"]
            if "protocol" in ace.keys():
                command = command + " " + ace["protocol"]
            if "source" in ace.keys():
                if "any" in ace["source"].keys():
                    command = command + " any"
                elif "subnet_address" in ace["source"].keys():
                    command = command + " " + ace["source"]["subnet_address"]
                elif "host" in ace["source"].keys():
                    command = command + " host " + ace["source"]["host"] 
                elif "address" in ace["source"].keys():
                    command = command + " " + ace["source"]["address"] + " " + ace["source"]["wildcard_bits"]
                if "port_protocol" in ace["source"].keys():
                    for op in ace["source"]["port_protocol"].keys():
                        command = command + " " + op + " " + ace["source"]["port_protocol"][op]
            if "destination" in ace.keys():
                if "any" in ace["destination"].keys():
                    command = command + " any"
                elif "subnet_address" in ace["destination"].keys():
                    command = command + " " + ace["destination"]["subnet_address"]
                elif "host" in ace["destination"].keys():
                    command = command + " host " + ace["destination"]["host"]
                elif "address" in ace["destination"].keys():
                    command = command + " " + ace["destination"]["address"] + " " + ace["destination"]["wildcard_bits"]    
                if "port_protocol" in ace["destination"].keys():
                    for op in ace["destination"]["port_protocol"].keys():
                        command = command + " " + op + " " + ace["destination"]["port_protocol"][op]
            if "protocol_options" in ace.keys():
                
    q(commandset)
    q("***********************")
    return commandset
