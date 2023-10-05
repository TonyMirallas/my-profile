import unittest
# from models import Tweet
from context import functions

class TestFunctions(unittest.TestCase):

    def setUp(self):

# def get_root_path(folder = None, file = None, extension = None):

# def get_filename_path(twitter_url, extension = None):


        self.input = {
            "folder" : "csv",
            "file" : "Zequiodzilla",
            "extension" : ".csv",
            "twitter_url" : "https://twitter.com/Zequiodzilla"
        }

        self.output = {
            "root_path" : "/home/tony/python/scraping/my_profile/project",
            "filename_path" : "/home/tony/python/scraping/my_profile/project/csv/Zequiodzilla.csv",
            "filename": "Zequiodzilla",
            "file": "Zequiodzilla.csv"
        }

    """Test for get_root_path()"""
    def test_get_root_path(self):
        root_path = functions.get_root_path()
        self.assertEqual(root_path, self.output['root_path'])

        root_path = functions.get_root_path(self.input['folder'], self.input['file'], self.input['extension'])
        self.assertEqual(root_path, self.output['filename_path'])

    """Test for get_filename_path()"""
    def test_get_filename_path(self):
        filename_path = functions.get_filename_path(self.input['twitter_url'])
        self.assertEqual(filename_path, self.output['filename'])

        filename_path = functions.get_filename_path(self.input['twitter_url'], self.input['extension'])
        self.assertEqual(filename_path, self.output['file'])

    # def test_store_three_responses(self):
    #     """Test that three individual responses are stored properly"""
    #     for response in self.responses:
    #         self.my_tweet.store_response(response)

    #     for response in self.responses:
    #         self.assertIn(response, self.my_tweet.responses)



if __name__ == '__main__':
    unittest.main()