import unittest
import project
import project_utils
import os
import logging
import sys


logger = logging.getLogger('tests')

class FileExistsTestCase(unittest.TestCase):

    def setUp(self):
        project.configure_logger('tests.log', logging.DEBUG)
        project.authenticate_github_object()

    def test_tools_research_question(self):
        tools_file = project.analyze_research_question_tools()
        file_in_folder = os.path.isfile(tools_file)
        self.assertTrue(file_in_folder)

    def test_triggers_research_question(self):
        tools_file = project.analyze_research_question_triggers_stages()
        file_in_folder = os.path.isfile(tools_file)
        self.assertTrue(file_in_folder)

    def test_artifacts_research_question(self):
        tools_file = project.analyze_research_questions_artifacts()
        file_in_folder = os.path.isfile(tools_file)
        self.assertTrue(file_in_folder)


if __name__ == '__main__':
    unittest.main()
