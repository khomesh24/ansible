#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_role
version_added: "2.3"
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Ansible Tower role.
description:
    - Create, update, or destroy Ansible Tower roles. See
      U(https://www.ansible.com/tower) for an overview.
options:
    user:
      description:
        - User that receives the permissions specified by the role.
      required: False
      default: null
    team:
      description:
        - Team that receives the permissions specified by the role.
      required: False
      default: null
    role:
      description:
        - The role type to grant/revoke.
      required: True
      choices: ["admin", "read", "member", "execute", "adhoc", "update", "use", "auditor"]
    target_team:
      description:
        - Team that the role acts on.
      required: False
      default: null
    inventory:
      description:
        - Inventory the role acts on.
      required: False
      default: null
    job_template:
      description:
        - The job template the role acts on.
      required: False
      default: null
    credential:
      description:
        - Credential the role acts on.
      required: False
      default: null
    organization:
      description:
        - Organization the role acts on.
      required: False
      default: null
    project:
      description:
        - Project the role acts on.
      required: False
      default: null
    state:
      description:
        - Desired state of the resource.
      required: False
      default: "present"
      choices: ["present", "absent"]
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- name: Add jdoe to the member role of My Team
  tower_role:
    user: jdoe
    target_team: "My Team"
    role: member
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''

from ansible.module_utils.ansible_tower import tower_argument_spec, tower_auth_config, tower_check_mode, HAS_TOWER_CLI

try:
    import tower_cli
    import tower_cli.utils.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def update_resources(module, p):
    '''update_resources attempts to fetch any of the resources given
    by name using their unique field (identity)
    '''
    params = p.copy()
    identity_map = {
        'user': 'username',
        'team': 'name',
        'target_team': 'name',
        'inventory': 'name',
        'job_template': 'name',
        'credential': 'name',
        'organization': 'name',
        'project': 'name',
    }
    for k, v in identity_map.items():
        try:
            if params[k]:
                key = 'team' if k == 'target_team' else k
                result = tower_cli.get_resource(key).get(**{v: params[k]})
                params[k] = result['id']
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update role, {0} not found: {1}'.format(k, excinfo), changed=False)
    return params


def main():

    argument_spec = tower_argument_spec()
    argument_spec.update(dict(
        user=dict(),
        team=dict(),
        role=dict(choices=["admin", "read", "member", "execute", "adhoc", "update", "use", "auditor"]),
        target_team=dict(),
        inventory=dict(),
        job_template=dict(),
        credential=dict(),
        organization=dict(),
        project=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    role_type = module.params.pop('role')
    state = module.params.get('state')

    json_output = {'role': role_type, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        role = tower_cli.get_resource('role')

        params = update_resources(module, module.params)
        params['type'] = role_type

        try:
            if state == 'present':
                result = role.grant(**params)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = role.revoke(**params)
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update role: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
