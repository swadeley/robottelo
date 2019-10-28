# -*- encoding: utf-8 -*-
"""Test for bootstrap script (bootstrap.py).

:Requirement: Bootstrap Script

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Bootstrap

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import stubbed, tier1, tier4, upgrade
from robottelo.test import CLITestCase
from robottelo.config import settings
from nailgun import entities
from robottelo.containers import Container
from robottelo.constants import (
    RHEL_7_MAJOR_VERSION,
    RHEL_6_MAJOR_VERSION,
)


class BootstrapScriptTestCase(CLITestCase):
    """Test class for bootstrap script."""

    @classmethod
    def setUpClass(cls):
        """Set up organization and location for tests."""
        super(BootstrapScriptTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.loc = entities.Location(organization=[cls.org]).create()
        # create an activation key
        cls.ak = entities.ActivationKey().create()

        # Get OS ID
        cls.os = entities.OperatingSystem().search(query={
            u'search': u'name="RedHat" AND (major="{0}" OR major="{1}")'
                       .format(RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION)
                })[0].read()

        cls.domain = entities.Domain(
            location=[cls.loc],
            organization=[cls.org],
                ).create()

        # create a host group
        cls.hostgroup = entities.HostGroup(
            location=[cls.loc],
            organization=[cls.org],
            operatingsystem=[cls.os.id],
        ).create()

    @tier4
    def test_positive_register(self):
        """System is registered.

        :id: e34561fd-e0d6-4587-84eb-f86bd131aab1

        :Steps:

            1. create a container with host name
            2. register system using bootstrap.py
            3. assert subscription-identity is true

        :expectedresults: system is registered, host is created

        :CaseAutomation: automated

        :CaseImportance: High
        """
        my_host = Container(agent=True)
        host_name = my_host.execute("hostname")
        my_host.execute("curl -O http://{}/pub/bootstrap.py".format(settings.server.hostname))
        my_host.execute("python bootstrap.py -l admin -p changme -s {} -o '{}' \
                         -L '{}' -g {} -a {} --fqdn {}.{}"
                        .format(settings.server.hostname, self.org.name, self.loc.name,
                                self.hostgroup.name, self.ak.name, host_name, self.domain))
        result = my_host.execute("subscription-manager status")
        assert "Registered" in result, 'Not registered'
        Container.delete(my_host)

    @tier1
    @upgrade
    def test_positive_reregister(self):
        """Registered system is re-registered.

        :id: d8a7aef1-7522-47a8-8478-77e81ca236be

        :Steps:

            1. register a system using commands
            2. assure system is registered
            3. register system once again using bootstrap.py
            4. assure system is registered

        :expectedresults: system is newly registered, host is created

        :CaseAutomation: automated

        :CaseImportance: Mediumtests/foreman/cli/test_bootstrap_script.py
        """
        my_host = Container(agent=True)
        host_name = my_host.execute("hostname")
        my_host.register('{},{}'.format(settings.server.hostname, self.ak.name))
        my_host.execute("subscription-manager attach --auto")
        # Check and assert the host is registered
        result = my_host.execute("subscription-manager status")
        assert result.return_code == 0, 'Not registered'
        # register host again using bootstrap.py
        my_host.execute("curl -O http://{}/pub/bootstrap.py".format(settings.server.hostname))
        my_host.execute("python bootstrap.py -l admin -p changme -s {} -o '{}' \
                         -L '{}' -g {} -a {} --fqdn {}.{}".format
                        (settings.server.hostname, self.org.name, self.loc.name,
                         self.hostgroup.name, self.ak.name, host_name, self.domain))
        # Check and assert the host is registered
        result = my_host.execute("subscription-manager status")
        assert result.return_code == 0, 'Not registered'
        Container.delete(my_host)

    @tier1
    @stubbed()
    def test_positive_migrate(self):
        """RHN registered system is migrated.

        :id: 26911dce-f2e3-4aef-a490-ad55236493bf

        :Steps:

            1. register system to SAT5 (or use precreated stored registration)
            2. assure system is registered with rhn classic
            3. migrate system

        :expectedresults: system is migrated, ie. registered

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    def test_negative_register_no_subs(self):
        """Attempt to register when no subscriptions are available.

        :id: 26f04562-6242-4542-8852-4242156f6e45

        :Steps:

            1. create AK with no available subscriptions
            2. try to register a system

        :expectedresults: ends gracefully, reason displayed to user

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    def test_negative_register_bad_hostgroup(self):
        """Attempt to register when hostgroup doesn't meet all criteria.

        :id: 29551e22-ae63-47f2-86f3-5f1444df8493

        :Steps:

            1. create hostgroup not matching required criteria for
               bootstrapping (Domain can't be blank...)
            2. try to register a system

        :expectedresults: ends gracefully, reason displayed to user

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    def test_positive_register_host_collision(self):
        """Attempt to register with already created host.

        :id: ec39c981-5b8a-43a3-84f1-71871a951c53

        :Steps:

            1. create host profile
            2. register a system

        :expectedresults: system is registered, pre-created host profile is
            used

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    def test_negative_register_missing_sattools(self):
        """Attempt to register when sat tools not available.

        :id: 88f95080-a6f1-4a4f-bd7a-5d030c0bd2e0

        :Steps:

            1. create env without available sat tools repo (AK or hostgroup
               being used doesn't provide CV that have sattools)
            2. try to register a system

        :expectedresults: ends gracefully, reason displayed to user

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """
