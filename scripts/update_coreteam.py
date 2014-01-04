"""
You need to install the requests package first::

    $ pip install requests

"""

import os.path
import requests

API_URL = 'https://api.github.com/%s'

RST_FORMAT = '* `%s <%s>`_'
MISSING_NAMES = {
    'khinsen': 'Konrad Hinsen',
}
# We have three concealed members on the hylang organization
# and GitHub only shows public members if the requester is not
# an owner of the organization.
CONCEALED_MEMBERS = [
    ('aldeka', 'Karen Rustad'),
    ('tuturto', 'Tuukka Turto'),
]


def get_dev_name(login):
    name = requests.get(API_URL % 'users/' + login).json()['name']
    if not name:
        return MISSING_NAMES.get(login)
    return name

coredevs = requests.get(API_URL % 'orgs/hylang/members')

result = set()
for dev in coredevs.json():
    result.add(RST_FORMAT % (get_dev_name(dev['login']), dev['html_url']))

for login, name in CONCEALED_MEMBERS:
    result.add(RST_FORMAT % (name, 'https://github.com/' + login))

filename = os.path.abspath(os.path.join(os.path.pardir,
                                        'docs', 'coreteam.rst'))
with open(filename, 'w+') as fobj:
    fobj.write('\n'.join(result) + '\n')
