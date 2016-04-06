"""
Tests for the bok-choy paver commands themselves.
Run just this test with: paver test_lib -t pavelib/paver_tests/test_paver_bok_choy_cmds.py
"""
import os
import unittest

from mock import patch, call
from test.test_support import EnvironmentVarGuard
from paver.easy import BuildFailure
from pavelib.utils.test.suites import BokChoyTestSuite, A11yCrawler

REPO_DIR = os.getcwd()


class TestPaverBokChoyCmd(unittest.TestCase):
    """
    Paver Bok Choy Command test cases
    """

    def _expected_command(self, name, store=None, verify_xss=False):
        """
        Returns the command that is expected to be run for the given test spec
        and store.
        """

        expected_statement = (
            "DEFAULT_STORE={default_store} "
            "SCREENSHOT_DIR='{repo_dir}/test_root/log{shard_str}' "
            "BOK_CHOY_HAR_DIR='{repo_dir}/test_root/log{shard_str}/hars' "
            "BOKCHOY_A11Y_CUSTOM_RULES_FILE='{repo_dir}/{a11y_custom_file}' "
            "SELENIUM_DRIVER_LOG_DIR='{repo_dir}/test_root/log{shard_str}' "
            "VERIFY_XSS='{verify_xss}' "
            "nosetests {repo_dir}/common/test/acceptance/{exp_text} "
            "--with-xunit "
            "--xunit-file={repo_dir}/reports/bok_choy{shard_str}/xunit.xml "
            "--verbosity=2 "
        ).format(
            default_store=store,
            repo_dir=REPO_DIR,
            shard_str='/shard_' + self.shard if self.shard else '',
            exp_text=name,
            a11y_custom_file='node_modules/edx-custom-a11y-rules/lib/custom_a11y_rules.js',
            verify_xss=verify_xss
        )
        return expected_statement

    def setUp(self):
        super(TestPaverBokChoyCmd, self).setUp()
        self.shard = os.environ.get('SHARD')
        self.env_var_override = EnvironmentVarGuard()

    def test_default(self):
        suite = BokChoyTestSuite('')
        name = 'tests'
        self.assertEqual(suite.cmd, self._expected_command(name=name))

    def test_suite_spec(self):
        spec = 'test_foo.py'
        suite = BokChoyTestSuite('', test_spec=spec)
        name = 'tests/{}'.format(spec)
        self.assertEqual(suite.cmd, self._expected_command(name=name))

    def test_class_spec(self):
        spec = 'test_foo.py:FooTest'
        suite = BokChoyTestSuite('', test_spec=spec)
        name = 'tests/{}'.format(spec)
        self.assertEqual(suite.cmd, self._expected_command(name=name))

    def test_testcase_spec(self):
        spec = 'test_foo.py:FooTest.test_bar'
        suite = BokChoyTestSuite('', test_spec=spec)
        name = 'tests/{}'.format(spec)
        self.assertEqual(suite.cmd, self._expected_command(name=name))

    def test_spec_with_draft_default_store(self):
        spec = 'test_foo.py'
        suite = BokChoyTestSuite('', test_spec=spec, default_store='draft')
        name = 'tests/{}'.format(spec)
        self.assertEqual(
            suite.cmd,
            self._expected_command(name=name, store='draft')
        )

    def test_invalid_default_store(self):
        # the cmd will dumbly compose whatever we pass in for the default_store
        suite = BokChoyTestSuite('', default_store='invalid')
        name = 'tests'
        self.assertEqual(
            suite.cmd,
            self._expected_command(name=name, store='invalid')
        )

    def test_serversonly(self):
        suite = BokChoyTestSuite('', serversonly=True)
        self.assertEqual(suite.cmd, "")

    def test_verify_xss(self):
        suite = BokChoyTestSuite('', verify_xss=True)
        name = 'tests'
        self.assertEqual(suite.cmd, self._expected_command(name=name, verify_xss=True))

    def test_verify_xss_env_var(self):
        self.env_var_override.set('VERIFY_XSS', 'True')
        with self.env_var_override:
            suite = BokChoyTestSuite('')
            name = 'tests'
            self.assertEqual(suite.cmd, self._expected_command(name=name, verify_xss=True))

    def test_test_dir(self):
        test_dir = 'foo'
        suite = BokChoyTestSuite('', test_dir=test_dir)
        self.assertEqual(
            suite.cmd,
            self._expected_command(name=test_dir)
        )

    def test_verbosity_settings_1_process(self):
        """
        Using 1 process means paver should ask for the traditional xunit plugin for plugin results
        """
        expected_verbosity_string = (
            "--with-xunit --xunit-file={repo_dir}/reports/bok_choy{shard_str}/xunit.xml --verbosity=2".format(
                repo_dir=REPO_DIR,
                shard_str='/shard_' + self.shard if self.shard else ''
            )
        )
        suite = BokChoyTestSuite('', num_processes=1)
        self.assertEqual(BokChoyTestSuite.verbosity_processes_string(suite), expected_verbosity_string)

    def test_verbosity_settings_2_processes(self):
        """
        Using multiple processes means specific xunit, coloring, and process-related settings should
        be used.
        """
        process_count = 2
        expected_verbosity_string = (
            "--with-xunitmp --xunitmp-file={repo_dir}/reports/bok_choy{shard_str}/xunit.xml"
            " --processes={procs} --no-color --process-timeout=1200".format(
                repo_dir=REPO_DIR,
                shard_str='/shard_' + self.shard if self.shard else '',
                procs=process_count
            )
        )
        suite = BokChoyTestSuite('', num_processes=process_count)
        self.assertEqual(BokChoyTestSuite.verbosity_processes_string(suite), expected_verbosity_string)

    def test_verbosity_settings_3_processes(self):
        """
        With the above test, validate that num_processes can be set to various values
        """
        process_count = 3
        expected_verbosity_string = (
            "--with-xunitmp --xunitmp-file={repo_dir}/reports/bok_choy{shard_str}/xunit.xml"
            " --processes={procs} --no-color --process-timeout=1200".format(
                repo_dir=REPO_DIR,
                shard_str='/shard_' + self.shard if self.shard else '',
                procs=process_count
            )
        )
        suite = BokChoyTestSuite('', num_processes=process_count)
        self.assertEqual(BokChoyTestSuite.verbosity_processes_string(suite), expected_verbosity_string)

    def test_invalid_verbosity_and_processes(self):
        """
        If an invalid combination of verbosity and number of processors is passed in, a
        BuildFailure should be raised
        """
        suite = BokChoyTestSuite('', num_processes=2, verbosity=3)
        with self.assertRaises(BuildFailure):
            BokChoyTestSuite.verbosity_processes_string(suite)


class TestPaverPa11ycrawlerCmd(unittest.TestCase):

    """
    Paver pa11ycrawler command test cases.  Most of the functionality is
    inherited from BokChoyTestSuite, so those tests aren't duplicated.
    """

    def setUp(self):
        super(TestPaverPa11ycrawlerCmd, self).setUp()

        # Mock shell commands
        mock_sh = patch('pavelib.utils.test.suites.bokchoy_suite.sh')
        self._mock_sh = mock_sh.start()

        # Cleanup mocks
        self.addCleanup(mock_sh.stop)

    def _expected_command(self, report_dir):
        """
        Returns the expected command to run pa11ycrawler.
        """
        cms_start_url = (
            "http://localhost:8031/auto_auth?redirect=true&course_id=course-v1"
            "%3AedX%2BTest101%2Bcourse&staff=true"
        )

        lms_start_url = (
            "http://localhost:8003/auto_auth?redirect=true&course_id=course-v1"
            "%3AedX%2BTest101%2Bcourse&staff=true"
        )

        expected_statement = (
            'pa11ycrawler run "{cms_start_url}" "{lms_start_url}" '
            '--pa11ycrawler-allowed-domains=localhost '
            '--pa11ycrawler-reports-dir={report_dir} '
            '--pa11ycrawler-deny-url-matcher=logout '
            '--pa11y-reporter="1.0-json" '
            '--depth-limit=6 '
        ).format(
            cms_start_url=cms_start_url,
            lms_start_url=lms_start_url,
            report_dir=report_dir,
        )
        return expected_statement

    def test_default(self):
        suite = A11yCrawler('')
        self.assertEqual(
            suite.cmd, self._expected_command(suite.pa11y_report_dir))

    def test_get_test_course(self):
        suite = A11yCrawler('')
        suite.get_test_course()
        self._mock_sh.assert_has_calls([
            call(
                'wget {targz} -O {dir}demo_course.tar.gz'.format(targz=suite.tar_gz_file, dir=suite.imports_dir)),
            call(
                'tar zxf {dir}demo_course.tar.gz -C {dir}'.format(dir=suite.imports_dir)),
        ])

    def test_generate_html_reports(self):
        suite = A11yCrawler('')
        suite.generate_html_reports()
        self._mock_sh.assert_has_calls([
            call(
                'pa11ycrawler json-to-html --pa11ycrawler-reports-dir={}'.format(suite.pa11y_report_dir)),
        ])
