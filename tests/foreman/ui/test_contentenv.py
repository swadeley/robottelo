# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Life cycle environments UI"""

from fauxfactory import gen_string
from nose.plugins.attrib import attr
from robottelo import entities
from robottelo.common.decorators import run_only_on
from robottelo.test import UITestCase
from robottelo.ui.factory import make_lifecycle_environment
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
class ContentEnvironment(UITestCase):
    """Implements Life cycle content environment tests in UI"""

    @classmethod
    def setUpClass(cls):
        cls.org_name = entities.Organization().create()['name']

        super(ContentEnvironment, cls).setUpClass()

    @attr('ui', 'contentenv', 'implemented')
    def test_positive_create_content_environment_1(self):
        """@Test: Create content environment with minimal input parameters

        @Feature: Content Environment - Positive Create

        @Assert: Environment is created

        """

        name = gen_string("alpha", 6)
        description = gen_string("alpha", 6)
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=name, description=description)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))

    @attr('ui', 'contentenv', 'implemented')
    def test_positive_create_content_environment_2(self):
        """@Test: Create Content Environment in a chain

        @Feature: Content Environment - Positive Create

        @Assert: Environment is created

        """

        env_1_name = gen_string("alpha", 6)
        env_2_name = gen_string("alpha", 6)
        description = gen_string("alpha", 6)
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=env_1_name,
                                       description=description)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))
            self.contentenv.create(env_2_name, description, prior=env_1_name)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))

    @attr('ui', 'contentenv', 'implemented')
    def test_positive_delete_content_environment_1(self):
        """@Test: Create Content Environment and delete it

        @Feature: Content Environment - Positive Delete

        @Assert: Environment is deleted

        """

        name = gen_string("alpha", 6)
        description = gen_string("alpha", 6)
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=name, description=description)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))
            self.contentenv.delete(name, "true")
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))

    @attr('ui', 'contentenv', 'implemented')
    def test_positive_update_content_environment_1(self):
        """@Test: Create Content Environment and update it

        @Feature: Content Environment - Positive Update

        @Assert: Environment is updated

        """

        name = gen_string("alpha", 6)
        new_name = gen_string("alpha", 6)
        description = gen_string("alpha", 6)
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=name)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))
            self.contentenv.update(name, new_name, description)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))
