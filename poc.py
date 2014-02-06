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
    return [bp.name for bp in proj.valid_specifications if bp.direction_approved]


def get_invalid_blueprints(project, valid):
    lp = launchpad.Launchpad.login_anonymously('grabbing BPs',
                                               'production',
                                               LPCACHEDIR,
                                               version='devel')
    proj = lp.projects(project)
    if "openstack" not in proj.project_group.name:
        raise Exception("Not a OpenStack project!")
    all_bps = [bp.name for bp in proj.all_specifications]
    return [x for x in all_bps if x not in valid]


#taken from jeepyb
SPEC_RE = re.compile(r'\b(blueprint|bp)\b[ \t]*[#:]?[ \t]+(\S+)', re.I)


def get_blueprints(message):
    #taken from jeepyb
    bps = set([m.group(2) for m in SPEC_RE.finditer(message)])
    return list(bps)


def in_bps_list(bp, bps_list):
    return bp in bps_list or (bp[-1:]=='.' and bp[:-1] in bps_list)


def get_unapproved_blueprint_patches(approved_blueprints, invalid_blueprints):
    """Return a list of patches with unapproved blueprints."""
    result = {}  # URL: BP
    gerrit = gerritlib.gerrit.Gerrit("review.openstack.org", "jogo", 29418)
    for patch in gerrit.bulk_query('--commit-message project:openstack/nova status:open'):
        msg = patch.get('commitMessage')
        if msg is None:
            continue
        bps = get_blueprints(msg)
        if len(bps) > 0:
            for bp in bps:
                if not in_bps_list(bp, approved_blueprints):
                    if in_bps_list(bp, invalid_blueprints):
                        result[patch['url']]=bp
                    else:
                        result[patch['url']]=("%s (unknown)" % bp)
    return result


def main():
    approved_blueprints = get_approved_bluerpint("nova")
    invalid_blueprints = get_invalid_blueprints("nova", approved_blueprints)
    patches =  get_unapproved_blueprint_patches(approved_blueprints, invalid_blueprints)
    print "patches with unapproved blueprints"
    for k in patches:
        print "%s: %s" % (k, patches[k])

if __name__ == "__main__":
    main()
