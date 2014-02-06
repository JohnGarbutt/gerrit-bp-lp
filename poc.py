#!/usr/bin/env python

import os
import re

import gerritlib.gerrit
from launchpadlib import launchpad

LPCACHEDIR = os.path.expanduser('~/.launchpadlib/cache')


def get_approved_bluerpint(project):
    lp = launchpad.Launchpad.login_anonymously('grabbing BPs',
                                               'production',
                                               LPCACHEDIR,
                                               version='devel')
    proj = lp.projects(project)
    if "openstack" not in proj.project_group.name:
        raise Exception("Not a OpenStack project!")
    return [bp.name for bp in proj.valid_specifications]


def get_blueprint(message):
    """If no blueprint, return None."""
    m = re.search('blueprint ([^\s.]*)', message)
    if not m:
        return None
    else:
        return m.group(1)


def get_unapproved_blueprint_patches(approved_blueprints):
    """Return a list of patches with unapproved blueprints."""
    result = {} #URL: BP
    gerrit = gerritlib.gerrit.Gerrit("review.openstack.org", "jogo", 29418)
    for patch in gerrit.bulk_query('--commit-message project:openstack/nova status:open'):
        msg = patch.get('commitMessage')
        if msg is None:
            continue
        bp = get_blueprint(msg)
        if bp is not None:
            if bp not in approved_blueprints:
                result[patch['url']]=bp
    return result


def main():
    approved_blueprints = get_approved_bluerpint("nova")
    patches =  get_unapproved_blueprint_patches(approved_blueprints)
    print "patches with unapproved blueprints"
    for k in patches:
        print "%s: %s" % (k, patches[k])

if __name__ == "__main__":
    main()
