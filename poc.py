#!/usr/bin/env python

import os
import re
import pprint

import gerritlib.gerrit
from launchpadlib import launchpad

LPCACHEDIR = os.path.expanduser('~/.launchpadlib/cache')
GERRIT_USER = "johngarbutt"

"""
Blueprints

lp_attributes
['self_link', 'web_link', 'resource_type_link', 'http_etag', 'date_completed', 'date_created', 'date_started', 'definition_status', 'direction_approved', 'has_accepted_goal', 'implementation_status', 'information_type', 'is_complete', 'is_started', 'lifecycle_status', 'name', 'priority', 'specification_url', 'summary', 'title', 'whiteboard', 'workitems_text']
lp_collections
['bugs', 'dependencies', 'linked_branches']
lp_entries
['approver', 'assignee', 'completer', 'drafter', 'milestone', 'owner', 'starter', 'target']
lp_operations
['unlinkBranch', 'acceptGoal', 'linkBug', 'linkBranch', 'proposeGoal', 'unlinkBug', 'subscribe', 'unsubscribe', 'declineGoal']

Projects

lp_attributes
['self_link', 'web_link', 'resource_type_link', 'http_etag', 'active', 'branch_sharing_policy', 'bug_reported_acknowledgement', 'bug_reporting_guidelines', 'bug_sharing_policy', 'commercial_subscription_is_due', 'date_created', 'description', 'display_name', 'download_url', 'freshmeat_project', 'homepage_url', 'information_type', 'is_permitted', 'license_approved', 'license_info', 'licenses', 'name', 'official_bug_tags', 'private', 'programming_language', 'project_reviewed', 'qualifies_for_free_hosting', 'remote_product', 'reviewer_whiteboard', 'screenshots_url', 'sourceforge_project', 'specification_sharing_policy', 'summary', 'title', 'translationpermission', 'translations_usage', 'wiki_url']
lp_collections
['active_milestones', 'all_milestones', 'all_specifications', 'recipes', 'releases', 'series', 'valid_specifications']
lp_entries
['brand', 'bug_supervisor', 'bug_tracker', 'commercial_subscription', 'development_focus', 'driver', 'icon', 'logo', 'owner', 'project_group', 'registrant', 'translation_focus', 'translationgroup']
lp_operations
['searchTasks', 'get_timeline', 'getMergeProposals', 'getSupportedLanguages', 'getSeries', 'getBranches', 'userHasBugSubscriptions', 'getAnswerContactsForLanguage', 'getRelease', 'findSimilarQuestions', 'getSubscriptions', 'getQuestion', 'getTranslationImportQueueEntries', 'canUserAlterAnswerContact', 'findReferencedOOPS', 'getSubscription', 'getSpecification', 'searchQuestions', 'getMilestone', 'addAnswerContact', 'newCodeImport', 'newSeries', 'removeOfficialBugTag', 'addBugSubscriptionFilter', 'addOfficialBugTag', 'addBugSubscription', 'removeBugSubscription', 'removeAnswerContact']


series
lp_attributes
['self_link', 'web_link', 'resource_type_link', 'http_etag', 'active', 'bug_reported_acknowledgement', 'bug_reporting_guidelines', 'date_created', 'display_name', 'name', 'official_bug_tags', 'release_finder_url_pattern', 'status', 'summary', 'title', 'translations_autoimport_mode', 'translations_usage']
lp_collections
['active_milestones', 'all_milestones', 'all_specifications', 'drivers', 'releases', 'valid_specifications']
lp_entries
['branch', 'driver', 'owner', 'project']
lp_operations
['searchTasks', 'get_timeline', 'getSubscriptions', 'getTranslationTemplates', 'getTranslationImportQueueEntries', 'userHasBugSubscriptions', 'getSubscription', 'getSpecification', 'addBugSubscription', 'removeBugSubscription', 'newMilestone', 'addBugSubscriptionFilter']
<lazr.restfulclient.resource.Collection object at 0x1103228d0>


milestone
lp_attributes
['self_link', 'web_link', 'resource_type_link', 'http_etag', 'code_name', 'date_targeted', 'is_active', 'name', 'official_bug_tags', 'summary', 'title']
lp_collections
[]
lp_entries
['release', 'series_target', 'target']
lp_operations
['getTags', 'searchTasks', 'getSubscriptions', 'userHasBugSubscriptions', 'getSubscription', 'addBugSubscription', 'removeBugSubscription', 'createProductRelease', 'setTags', 'addBugSubscriptionFilter']
"""
def _inspect_object(obj):
    print "lp_attributes"
    print obj.lp_attributes
    print "lp_collections"
    print obj.lp_collections
    print "lp_entries"
    print obj.lp_entries
    print "lp_operations"
    print obj.lp_operations


def get_milestone_bluerpints(project="nova", series="icehouse", milestone="icehouse-3"):
    lp = launchpad.Launchpad.login_anonymously('grabbing BPs',
                                               'production',
                                               LPCACHEDIR,
                                               version='devel')
    proj = lp.projects(project)
    if "openstack" not in proj.project_group.name:
        raise Exception("Not a OpenStack project!")

    series_icehouse = [s for s in proj.series if series == s.name.lower()][0]
    milestone = [m for m in series_icehouse.active_milestones if milestone == m.name.lower()][0]
    pprint.pprint(milestone)

    #TODO - need to cache these really...
    icehouse = [bp for bp in proj.all_specifications if bp.milestone and milestone == bp.milestone]
    print "%s blueprints:" % milestone
    print len(icehouse)

    not_approved = [bp for bp in icehouse if not bp.direction_approved]
    print ""
    print "Unapproved blueprints:"
    for bp in not_approved:
        print bp.web_link

    approved = [bp for bp in icehouse if bp.direction_approved]
    print ""
    print "Approved blueprints:"
    print len(approved)

    complete = [bp for bp in approved if not bp.is_complete]
    print ""
    print "Completed blueprints:"
    print len(complete)
    for bp in complete:
        print bp.web_link

    not_complete = [bp for bp in approved if not bp.is_complete]
    print ""
    print "Not complete:"
    print len(not_complete)

    return not_complete, not_approved


def _get_blueprint(message):
    """If no blueprint, return None."""
    #taken from jeepyb
    m = re.search(r'\b(blueprint|bp)\b[ \t]*[#:]?[ \t]*([\S]+)', message, re.I)
    if not m:
        return None
    else:
        return m.group(2)


def get_blueprint_patches(project="nova"):
    """Return a list of patches with unapproved blueprints."""
    result = {}  # blueprint: [patches]
    gerrit = gerritlib.gerrit.Gerrit("review.openstack.org", GERRIT_USER, 29418)
    print "Fetching patches..."
    all_patches = gerrit.bulk_query('--commit-message project:openstack/%s' % project)
    print len(all_patches)

    for patch in all_patches:
        msg = patch.get('commitMessage')
        if msg is None:
            continue
        bp = _get_blueprint(msg)
        # TODO - do bugs here too
        if bp:
            if bp not in result:
                result[bp] = []
            result[bp].append(patch)
    return result


def main():
    not_complete, not_approved = get_milestone_bluerpints()
    patches_by_blueprint = get_blueprint_patches()

    with_patches_names = []
    no_patches_names = []
    for bp in not_complete:
        patches = patches_by_blueprint.get(bp.name)
        if patches:
            with_patches.append(bp)
        else:
            no_patches.append(bp)

    with_patches = [bp for bp in not_complete if bp.name in with_patches_names]
    no_patches = [bp for bp in not_complete if bp.name in no_patches_names]

    unexpected_bp_patches = {}
    for bp_name, patches in patches_by_blueprint:
        if (bp_name not in no_patches_names) and (bp_name not in with_patches_names):
            for patch in patches:
                if patch["status"].lower() == "new":
                    patch["bp_name"] = bp_name
                    unexpected_bp_patches.append(patch)

    print ""
    print "Not complete blueprint with patches:"
    print len(with_patches)
    print ""
    for bp in with_patches:
        print "%s  status:%s" % (bp.web_link, bp.implementation_status)
        patches = patches_by_blueprint.get(bp.name)
        for patch in patches:
            print "%s  open:%s status:%s subject:%s" % (patch["url"], patch["open"], patch["status"], patch["subject"])

    print ""
    print "Not complete blueprint with no patches:"
    print len(no_patches)
    print ""
    for bp_name in no_patches:
        print "%s  status:%s" % (bp.web_link, bp.implementation_status)

    print ""
    print "Patches for blueprints we don't expect:"
    print len(unexpected_bp_patches)
    print ""
    for patch in unexpected_bp_patches:
        print "%s  blueprint:%s" % (patch["url"], patch["bp_name"])


if __name__ == "__main__":
    main()
