from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase
from django.utils import unittest
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from microcosm.views import MicrocosmView, ConversationView, CommentView

from microweb import settings
from microweb.helpers import build_url

class SeleniumAsUser(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        cls.selenium = WebDriver()
        super(SeleniumAsUser, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumAsUser, cls).tearDownClass()

    def setUp(self):
        # Set the HOST to the live_server_url so that persona audience matches.
        settings.HOST = self.live_server_url.split('//')[1]

    def test_all(self):
        """
        Run integration tests in a specific sequence, since we do not have test fixtures.
        """

        self.login()
        self.view_profile()
        self.edit_profile()

        microcosm_id = self.create_microcosm()
        self.edit_microcosm(microcosm_id)

        conversation_id = self.create_conversation(microcosm_id)
        self.edit_conversation(conversation_id)

        self.create_comment_on_item(ConversationView.single, conversation_id)

        # TODO: un-hardcode ID
        #self.edit_comment(1)

    def login(self):
        # Login with persona
        self.selenium.get(self.live_server_url)

        # Click 'login' and switch to persona window
        self.selenium.find_element_by_id('login_link').click()
        self.selenium.switch_to_window('__persona_dialog')

        # Enter email address and password
        # EC.element_to_be_visible was originally used here,
        # but did not seem to wait for the element to be active
        email_address_input = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="authentication_email"]')))
        email_address_input.send_keys(settings.PERSONA_USER)
        self.selenium.find_element_by_xpath('//*[@id="authentication_form"]/p[3]/button[1]').click()

        password_input = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="authentication_password"]')))
        password_input.send_keys(settings.PERSONA_PASS)

        # Submit login form and switch back to previous window
        self.selenium.find_element_by_xpath('//*[@id="authentication_form"]/p[3]/button[2]').click()
        self.selenium.switch_to_window('')

        # Persona login form will be submitted and page reloaded,
        # so wait until profile name is clickable
        profile_name = WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.ID, 'profile_name')))

        # By default profile_name will be set to the
        # local part (before the '@') of the email address
        assert profile_name.text == settings.PERSONA_USER.split('@')[0]

    def create_microcosm(self):
        self.selenium.get(self.live_server_url)

        create_microcosm = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'create_microcosm')))
        create_microcosm.click()

        title = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'id_title')))
        title.send_keys('Test microcosm')

        description = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'id_description')))
        description.send_keys('Created by selenium')

        self.selenium.find_element_by_id('submit').click()

        microcosm_title = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'microcosm_title')))
        assert microcosm_title.text == 'Test microcosm'

        microcosm_desc = self.selenium.find_element_by_id('microcosm_description')
        assert microcosm_desc.text == 'Created by selenium'

        return self.selenium.current_url.split('/')[-2]

    def edit_microcosm(self, microcosm_id):
        self.selenium.get(self.live_server_url + reverse(MicrocosmView.single, args=(microcosm_id,)))
        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'edit_microcosm'))).click()

        title = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'id_title')))
        title.send_keys(' edited')

        edit_reason = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'id_editReason')))
        edit_reason.send_keys('Selenium update')

        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'submit'))).click()

        title = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'microcosm_title')))
        assert 'Test microcosm edited' == title.text

    def view_profile(self):
        self.selenium.get(self.live_server_url)
        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'profile_name'))).click()

        profile_name = WebDriverWait(self.selenium, 10).until(
            EC.element_to_be_clickable((By.ID, 'profile_name')))
        assert profile_name.text == settings.PERSONA_USER.split('@')[0]

    def edit_profile(self):
        self.selenium.get(self.live_server_url)
        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'edit_profile'))).click()

        edit_reason = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'id_profileName')))
        edit_reason.send_keys('_edited')

        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'submit'))).click()

        profile_name = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'profile_name')))
        assert profile_name.text == 'personauser_edited'

    def create_conversation(self, microcosm_id):
        # Single microcosm view
        self.selenium.get(self.live_server_url + reverse(MicrocosmView.single, args=(microcosm_id,)))

        # Click through to item creation page
        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'create_item'))).click()

        # Click to load event creation form
        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'create_conversation'))).click()

        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'id_title'))).send_keys('Conversation test')

        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'submit'))).click()

        title = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'conversation_title')))
        assert title.text == 'Conversation test'

        return self.selenium.current_url.split('/')[-2]

    def edit_conversation(self, conversation_id):
        self.selenium.get(self.live_server_url + reverse(ConversationView.single, args=(conversation_id,)))

        old_title = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'conversation_title'))).text

        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'edit_conversation'))).click()

        title = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'id_title')))
        title.send_keys(' edited')

        edit_reason = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'id_editReason')))
        edit_reason.send_keys('Selenium update')

        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'submit'))).click()

        edited_title = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'conversation_title')))

        assert old_title + ' edited' == edited_title.text

    def create_comment_on_item(self, item_view, item_id):

        item_url = self.live_server_url + reverse(item_view, args=(item_id,))
        self.selenium.get(item_url)

        markdown = 'A test comment with *markdown*\n \
            , line breaks, and [links](http://example.org).'

        comment_box = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'id_markdown')))
        comment_box.send_keys(markdown)
        self.selenium.find_element_by_id('submit_comment').click()

        # Check that we've been redirected to the item page
        # TODO: this will break if there are any URL parameters
        assert item_url == self.selenium.current_url

        #TODO: return the comment ID from the article fragment.

    def edit_comment(self, comment_id):
        self.selenium.get(self.live_server_url + reverse(CommentView.edit, args=(comment_id,)))

        comment_box = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'id_markdown')))
        comment_box.send_keys(' edited')
        self.selenium.find_element_by_id('submit_comment').click()

    def create_event(self, microcosm_id):
        # Single microcosm view
        self.selenium.get(self.live_server_url + reverse(MicrocosmView.single, args=(microcosm_id,)))

        # Click through to item creation page
        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'create_item'))).click()

        # Click to load event creation form
        WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'create_event'))).click()

        # Wait for the first field to be active, and fill all fields
        title = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'id_title')))
        title.send_keys('Event created by selenium')
        self.selenium.find_element_by_id('id_where').send_keys('On the track')
        self.selenium.find_element_by_id('id_when').send_keys('2013-09-09 18:00:00')
        self.selenium.find_element_by_id('id_duration').send_keys('3600')
        self.selenium.find_element_by_id('id_rsvpLimit').send_keys('10')

        # Submit
        self.selenium.find_element_by_id('submit').click()

        # Assert title and other fields are present and correct
        event_title = WebDriverWait(self.selenium, 5).until(
            EC.element_to_be_clickable((By.ID, 'event_title')))
        assert event_title.text == 'Event created by selenium'

        assert 'On the track' == self.selenium.find_element_by_id('where').text
        assert '3600' == self.selenium.find_element_by_id('duration').text
        assert '10' == self.selenium.find_element_by_id('spaces_left').text


class BuildURLTests(unittest.TestCase):
    """
    Verify that helpers.build_url() builds valid URLs.
    """

    def testWithTrailingSeparator(self):
        url = build_url('a.microco.sm', ['resource/', '1/', 'extra/'])
        assert url == 'https://a.microco.sm/resource/1/extra'

    def testWithPrependedSeparator(self):
        url = build_url('a.microco.sm', ['/resource', '/1', '/extra'])
        assert url == 'https://a.microco.sm/resource/1/extra'

    def testWithDuplicateSeparator(self):
        url = build_url('a.microco.sm', ['resource/', '/1/', '/extra/'])
        assert url == 'https://a.microco.sm/resource/1/extra'

    def testWithNoSeparator(self):
        url = build_url('a.microco.sm', ['resource', '1', 'extra'])
        assert url == 'https://a.microco.sm/resource/1/extra'

    def testEmptyFragments(self):
        url = build_url('a.microco.sm', [])
        assert url == 'https://a.microco.sm'

    def testInvalidFragment(self):
        with self.assertRaises(AssertionError):
            build_url('a.microco.sm', ['resource', '1', 'ex/tra'])

    def testFailCustomDomains(self):
        with self.assertRaises(AssertionError):
            build_url('a.example.org', ['resource', '1', 'ex/tra'])
