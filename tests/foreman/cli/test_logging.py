"""CLI tests for logging.

:Requirement: FIXME

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: logging

:TestType: Functional

:CaseImportance: Medium

:Upstream: No
"""
from robottelo.cli.factory import (
    make_lifecycle_environment,
    make_org,
    make_product,
    make_product_wait,
    make_repository,
)
from fauxfactory import gen_alphanumeric, gen_string
from robottelo.constants import (
    DISTROS_SUPPORTED,
)
from robottelo.products import (
    YumRepository,
    RepositoryCollection,
    SatelliteToolsRepository,
)
from datetime import datetime, timedelta
import pytest
import logging
log = logging.getLogger(__name__)
from robottelo.helpers import get_nailgun_config
from robottelo import ssh
from robottelo.test import CLITestCase
import re
from robottelo.config import settings


class SimpleLoggingTestCase(CLITestCase):
    """Test class for default logging to files"""

    org = None
    product = None

    def setUp(self):
        """Tests for logging to files"""
        super(SimpleLoggingTestCase, self).setUp()

        # need own org for the manifest refresh test

        if SimpleLoggingTestCase.org is None:
            SimpleLoggingTestCase.org = make_org(cached=True)
        if SimpleLoggingTestCase.product is None:
            SimpleLoggingTestCase.product = make_product_wait(
                {u'organization-id': SimpleLoggingTestCase.org['id']},
            )

    def _make_repository(self, options=None):
        """Makes a new repository and asserts its success"""
        if options is None:
            options = {}

        if options.get('product-id') is None:
            options[u'product-id'] = self.product['id']

        return make_repository(options)

    def test_positive_logging_from_foreman_core(self):
        """Check that GET command to Hosts API is logged and it has the request ID."""
        GET_line_found = 0
        # log the start of the test in case of problems with slow systems
        self.logger.info("Testing test_positive_logging_from_foreman_core")
        with ssh.get_connection() as connection:
            result = connection.run('hammer host list')
            self.assertEqual(result.return_code, 0)
            # extract last ten lines from log
            result = connection.run('tail /var/log/foreman/production.log > /var/tmp/logfile')
            self.assertEqual(result.return_code, 0)
        # use same location on remote and local for log file extract
        logfile_location = '/var/tmp/logfile'
        ssh.download_file(logfile_location)
        # search the log file extract for the line with GET to host API
        with open("/var/tmp/logfile", "r") as logfile:
            for line in logfile:
                if re.search(r'Started GET \"\/api/hosts\?page=1', line):
                    self.logger.info('Found:', line)
                    GET_line_found = 1
                    break
            # Confirm the request ID was logged in the line with GET
            match = re.search(r'\[I\|app\|\w{8}\]', line)
            if match:
                self.logger.info("Request ID found")
            else:
                with pytest.raises(AssertionError) as context:
                    assert match == 1, "Request ID not found"
        with pytest.raises(AssertionError) as context:
            assert GET_line_found == 1, "The GET command to list hosts was not found in logs."

    def test_positive_logging_from_proxy(self):
        """Check PUT to API, parameters, then response."""
        with ssh.get_connection() as connection:
            result = connection.run('hammer proxy refresh feature')
            self.assertEqual(result.return_code, 0)
            # extract last ten lines from log
            result = connection.run('tail /var/log/foreman/production.log > /var/tmp/logfile')
            self.assertEqual(result.return_code, 0)
        # use same location on remote and local for log file extract
        logfile_location = '/var/tmp/logfile'
        ssh.download_file(logfile_location)
        # search the log file extract for the line with GET to host API
        with open("/var/tmp/logfile", "r") as logfile:
            for line in logfile:
                if re.search(r'Started PUT \"\/api\/smart_proxies\/1\/refresh', line):
                    self.logger.info('Found:', line)
                    PUT_line_found = 1
                    break
        with pytest.raises(AssertionError) as context:
            assert PUT_line_found == 1, "The PUT command to refresh proxies was not found in logs."

    def test_positive_logging_from_candlepin(self):
        """Check logging after load or manifest refresh."""

    def test_positive_logging_from_dynflow(self):
        """Check logging after enabling a repo."""
        new_repo = self._make_repository({u'name': gen_string('alpha')})
        with ssh.get_connection() as connection:
            # extract last ten lines from log
            result = connection.run('tail /var/log/foreman/production.log > /var/tmp/logfile')
            self.assertEqual(result.return_code, 0)
        # use same location on remote and local for log file extract
        logfile_location = '/var/tmp/logfile'
        ssh.download_file(logfile_location)
        # search the log file extract for the line with GET to host API
        with open("/var/tmp/logfile", "r") as logfile:
            for line in logfile:
                if re.search(r'Started POST \"/katello\/api\/repositories', line):
                    self.logger.info('Found:', line)
                    POST_line_found = 1
                    break
        with pytest.raises(AssertionError) as context:
            assert POST_line_found == 1, "The POST command to enable a repo was not found in logs."

    def test_positive_setup_journald_and_rsyslog(self):
        """Ensure all packages installed"""
        result = ssh.command('rpm -q foreman-proxy-journald')
        self.assertEqual(result.return_code, 0)
        result = ssh.command('yum install -y foreman-proxy-journald')
        self.assertEqual(result.return_code, 0)
