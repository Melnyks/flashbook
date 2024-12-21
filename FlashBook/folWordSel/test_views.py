from django.test import TestCase, Client
from django.contrib.auth.models import User as UserBuiltIn
from homepage.models import *
from django.urls import reverse
import base64
from datetime import date
import json

class FolderTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create(
            user_id=1,
            user='testuser',
            fname='Test',
            lname='User',
            email='testuser@example.com',
            password='testpassword'
        )

        self.user_built_in = UserBuiltIn.objects.create_user(
            username='testuser',
            password='testpassword',
            first_name='Test',
            last_name='User',
            email='testuser@example.com'
        )

        self.client = Client()
        
        login_url = reverse('login')
        response = self.client.get(login_url)
        csrf_token = response.cookies['csrftoken'].value
        
        response = self.client.post(
            login_url,
            {   
                'csrfmiddlewaretoken': csrf_token,
                'username': 'testuser',
                'password': 'testpassword'
            }
        )

        # Create initial folders for the user
        self.folder1 = Folder.objects.create(user=self.user, folder_name='Folder1')
        self.folder2 = Folder.objects.create(user=self.user, folder_name='Folder2')


    def test_folder_view(self):

        response = self.client.get(reverse('folder'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Folder1')
        self.assertTemplateUsed(response, 'folder.html')

    def test_add_folder(self):
        response = self.client.post(reverse('add_folder'), {'folder_name': 'NewFolder'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('folder'))
        self.assertTrue(Folder.objects.filter(user=self.user, folder_name='NewFolder').exists())

    def test_add_duplicate_folder(self):
        """Test adding a duplicate folder."""
        response = self.client.post(reverse('add_folder'), {'folder_name': 'Folder1'})
        self.assertRedirects(response, reverse('folder'))
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('A folder with this name already exists.' in str(m) for m in messages))

    def test_edit_folder(self):
        """Test editing an existing folder."""
        response = self.client.post(reverse('edit_folder', args=[self.folder1.folder_id]), {
            'action': 'edit',
            'folder_name': 'UpdatedFolder'
        })
        self.assertEqual(Folder.objects.get(user=self.user,folder_id=self.folder1.folder_id).folder_name, 'UpdatedFolder')
    
    def test_edit_duplicate_name_folder(self):
        """Test editing an existing folder."""
        response = self.client.post(reverse('edit_folder', args=[self.folder1.folder_id]), {
            'action': 'edit',
            'folder_name': 'Folder2'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('folder'))

    def test_delete_folder(self):
        """Test deleting an existing folder."""
        response = self.client.post(reverse('edit_folder', args=[self.folder1.folder_id]), {'action': 'delete'})
        self.assertFalse(Folder.objects.filter(user=self.user,folder_id=self.folder1.folder_id).exists())

    def test_folder_search_success(self):
        """Test searching for a folder."""
        response = self.client.get(reverse('search_folder') + '?query=Folder1')
        self.assertContains(response, 'Folder1')
        self.assertNotContains(response, 'Folder2')

    def test_folder_search_failure(self):
        """Test searching for a folder."""
        response = self.client.get(reverse('search_folder') + '?query=Folder3')
        self.assertNotContains(response, 'Folder1')
        self.assertNotContains(response, 'Folder2')

    def test_folder_search_empty(self):
        """Test searching for a folder."""
        response = self.client.get(reverse('search_folder') + '?query=')
        self.assertContains(response, 'Folder1')
        self.assertContains(response, 'Folder2')

class WordTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create(
            user_id=1,
            user='testuser',
            fname='Test',
            lname='User',
            email='testuser@example.com',
            password='testpassword'
        )

        self.user_built_in = UserBuiltIn.objects.create_user(
            username='testuser',
            password='testpassword',
            first_name='Test',
            last_name='User',
            email='testuser@example.com'
        )

        self.client = Client()
        
        login_url = reverse('login')

        # Get the CSRF token first by making a GET request
        response = self.client.get(login_url)
        csrf_token = response.cookies['csrftoken'].value  # Extract the CSRF token

        # Now submit the POST request with the CSRF token
        response = self.client.post(
            login_url,
            {   
                'csrfmiddlewaretoken': csrf_token,
                'username': 'testuser',
                'password': 'testpassword'
            }
        )

        # Create initial folders and words
        self.folder = Folder.objects.create(user=self.user, folder_name='Folder')

        self.word1 = Word.objects.create(user=self.user, folder=self.folder,word='testword1',meaning='testmeaning1')
        self.word2 = Word.objects.create(user=self.user, folder=self.folder,word='testword2',meaning='testmeaning2')

    def test_word_view(self):
        response = self.client.get(reverse('word', args=[self.folder.folder_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testword1')
        self.assertContains(response, 'testword2')
        self.assertTemplateUsed(response, 'word.html')

    def test_add_word(self):
        response = self.client.post(reverse('add_word', args=[self.folder.folder_id]), {
            'action': 'add',
            'word_name': 'NewWord',
            'meaning': 'NewMeaning'
        })
        self.assertTrue(Word.objects.filter(user=self.user,folder=self.folder, word='NewWord').exists())

    def test_add_duplicate_word(self):
        response = self.client.post(reverse('add_word', args=[self.folder.folder_id]), {
            'action': 'add',
            'word_name': 'testword1',
            'meaning': 'testmeaning1'
        })
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Word with this name already exists.' in str(m) for m in messages))

    def test_edit_word(self):
        response = self.client.post(reverse('edit_word', args=[self.folder.folder_id, self.word1.word_id]), {
            'action': 'edit',
            'word_name': 'testword3',
            'meaning': 'testmeaning3'
        })
        word = Word.objects.get(word_id=self.word1.word_id)
        self.assertEqual(word.word, 'testword3')
        self.assertEqual(word.meaning, 'testmeaning3')

    def test_edit_duplicate_name_word(self):
        response = self.client.post(reverse('edit_word', args=[self.folder.folder_id, self.word1.word_id]), {
            'action': 'edit',
            'word_name': 'testword2',
            'meaning': 'testmeaning2'
        })
        self.assertEqual(response.status_code, 200)

    def test_delete_word(self):
        """Test deleting a word in a folder."""
        response = self.client.post(reverse('edit_word', args=[self.folder.folder_id, self.word1.word_id]), {
            'action': 'delete'
        })
        self.assertFalse(Word.objects.filter(user=self.user,folder=self.folder,word=self.word1.word).exists())

    def test_search_word_success(self):
        """Test searching for a word."""
        response = self.client.get(reverse('search_word', args=[self.folder.folder_id]) + '?query=testword1')
        self.assertContains(response, 'testword1')
        self.assertNotContains(response, 'testword2')

    def test_search_word_failure(self):
        """Test searching for a word."""
        response = self.client.get(reverse('search_word', args=[self.folder.folder_id]) + '?query=testword3')
        self.assertNotContains(response, 'testword1')
        self.assertNotContains(response, 'testword2')

    def test_search_word_empty(self):
        """Test searching for a word."""
        response = self.client.get(reverse('search_word', args=[self.folder.folder_id]) + '?query=')
        self.assertContains(response, 'testword1')
        self.assertContains(response, 'testword2')

    def test_time_set_view(self):
        """Test loading of the timeSet page"""
        response = self.client.get(reverse('time_set', args=[self.folder.folder_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Set time")

    def test_select_game_view(self):
        """Test loading of the selectGame page"""
        response = self.client.get(reverse('select_game', args=[self.folder.folder_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select Game")  # Check that the page contains the phrase "Select Game"

    def test_back_button(self):
        """Test the functionality of the Back button"""
        response = self.client.get(reverse('mode_set', args=[self.folder.folder_id]))
        self.assertContains(response, '<button class="back-button"')  # Check if the Back button is present in modeSet.html
        self.assertContains(response, 'onclick="window.history.back()"')  # Check if the Back button's onclick uses the goBack() function

    def test_select_game_buttons(self):
        """Test the functionality of the buttons on the selectGame page"""
        response = self.client.get(reverse('select_game', args=[self.folder.folder_id]))
        self.assertContains(response, 'timeSet')  # Check if the Flashcard button links to '/folder/timeSet'
        self.assertContains(response, 'modeSet')  # Check if the Wordguess button links to '/folder/modeSet'

class ScoreViewTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create(
            user_id=1,
            user='testuser',
            fname='Test',
            lname='User',
            email='testuser@example.com',
            password='testpassword'
        )

        self.user_built_in = UserBuiltIn.objects.create_user(
            username='testuser',
            password='testpassword',
            first_name='Test',
            last_name='User',
            email='testuser@example.com'
        )

        self.client = Client()
        
        login_url = reverse('login')

        # Get the CSRF token first by making a GET request
        response = self.client.get(login_url)
        csrf_token = response.cookies['csrftoken'].value  # Extract the CSRF token

        # Now submit the POST request with the CSRF token
        response = self.client.post(
            login_url,
            {   
                'csrfmiddlewaretoken': csrf_token,
                'username': 'testuser',
                'password': 'testpassword'
            }
        )

        # Create test folders
        self.folder1 = Folder.objects.create(user=self.user, folder_name="Folder 1")
        self.folder2 = Folder.objects.create(user=self.user, folder_name="Folder 2")

        # Create test scores for different games
        self.game_1_score_1 = Highscore.objects.create(
            user=self.user, folder=self.folder1, game_id=1, play_time=1, score=100
        )
        self.game_1_score_2 = Highscore.objects.create(
            user=self.user, folder=self.folder1, game_id=1, play_time=2, score=150
        )

        self.game_2_score = Highscore.objects.create(
            user=self.user, folder=self.folder2, game_id=2, play_time=1, score=200
        )

        self.game_3_score = Highscore.objects.create(
            user=self.user, folder=self.folder2, game_id=3, play_time=1, score=250
        )

    def test_score_view_no_query(self):
        """Test the score view with no search query."""
        response = self.client.get(reverse('score'))
        self.assertEqual(response.status_code, 200)

        # Check if the graph is present in the response context
        self.assertIn('graph', response.context)
        self.assertIn('folders', response.context)
        self.assertEqual(len(response.context['folders']), 2)  # return both folders

        # Validate the graph data
        graph_data = response.context['graph']
        self.assertIsNotNone(graph_data)
        self.assertTrue(base64.b64decode(graph_data))  # Validate base64 data
        self.assertTrue(isinstance(graph_data, str))

    def test_score_view_with_query(self):
        """Test the score view with a search query."""
        response = self.client.get(reverse('score'), {'query': 'Folder 1'})
        self.assertEqual(response.status_code, 200)

        # Check filtered folders
        self.assertIn('folders', response.context)
        self.assertEqual(len(response.context['folders']), 1)  # Only "Folder 1" should match
        self.assertEqual(response.context['folders'][0].folder_name, "Folder 1")
        self.assertIsNotNone(response.context['graph'])

    def test_score_view_no_matching_query(self):
        """Test the score view with a query that doesn't match any folders."""
        response = self.client.get(reverse('score'), {'query': 'Nonexistent'})
        self.assertEqual(response.status_code, 200)

        # Check notification message
        self.assertIn('noti', response.context)
        self.assertEqual(
            response.context['noti'], "No scores found matching Nonexistent. Try another search term."
        )

        # Check folders returned
        self.assertIn('folders', response.context)
        self.assertEqual(len(response.context['folders']), 2)  # Should return all folders
        self.assertIsNotNone(response.context['graph'])

    def test_score_view_no_folders(self):
        """Test the score view when no folders exist."""
        Folder.objects.all().delete()  # Delete all folders

        response = self.client.get(reverse('score'))
        self.assertEqual(response.status_code, 200)

        # # Check that no graphs are returned
        self.assertNotIn('graph', response.context)
        self.assertNotIn('folders', response.context)

    def test_graph_generation(self):
        """Test graph generation with sample data."""
        response = self.client.get(reverse('score'))
        self.assertEqual(response.status_code, 200)

        # Check that graph is properly generated
        graph_data = response.context['graph']
        # Base64-encoded PNG files often start with this header
        self.assertTrue(graph_data.startswith('iVBORw0')) 

class CheckIn(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create(
            user_id=1,
            user='testuser',
            fname='Test',
            lname='User',
            email='testuser@example.com',
            password='testpassword'
        )

        self.user_built_in = UserBuiltIn.objects.create_user(
            username='testuser',
            password='testpassword',
            first_name='Test',
            last_name='User',
            email='testuser@example.com'
        )

        self.client = Client()
        
        login_url = reverse('login')

        # Get the CSRF token first by making a GET request
        response = self.client.get(login_url)
        csrf_token = response.cookies['csrftoken'].value  # Extract the CSRF token

        # Now submit the POST request with the CSRF token
        response = self.client.post(
            login_url,
            {   
                'csrfmiddlewaretoken': csrf_token,
                'username': 'testuser',
                'password': 'testpassword'
            }
        )
    
    def test_first_time_check_in(self):
        initial_day_streak = self.user.day_streak
        response = self.client.get(reverse('check_in'))
        self.user.refresh_from_db()
        
        # redirect
        self.assertRedirects(response, reverse('folder'))
        self.assertEqual(response.status_code, 302)

        # day streak add 1
        self.assertEqual(self.user.day_streak,initial_day_streak + 1)

        # last_check_in was updated
        self.assertEqual(self.user.last_check_in, date.today())

    def test_consecutive_check_in(self):
        yesterday = date.today() - timedelta(days=1)
        self.user.last_check_in = yesterday
        self.user.day_streak = 5
        self.user.save()

        response = self.client.get(reverse('check_in'))
        self.user.refresh_from_db()

        self.assertRedirects(response, reverse('folder'))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.user.day_streak, 6)
        self.assertEqual(self.user.last_check_in, date.today())

    def test_missed_check_in(self):
        two_days_ago = date.today() - timedelta(days=2)
        self.user.last_check_in = two_days_ago
        self.user.day_streak = 5
        self.user.day_streak_left = 5
        self.user.save()

        response = self.client.get(reverse('check_in'))
        self.user.refresh_from_db()

        self.assertRedirects(response, reverse('folder'))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.user.day_streak, 1)  # reset day streak
        self.assertEqual(self.user.last_check_in, date.today())

    def test_check_in_same_day(self):
        today = date.today()
        self.user.last_check_in = today
        self.user.day_streak = 5
        self.user.day_streak_left = 5
        self.user.save()

        response = self.client.get(reverse('check_in'))
        self.user.refresh_from_db()

        self.assertEqual(self.user.day_streak, 5)  # nothing changed
        self.assertEqual(self.user.last_check_in, date.today())

class Reward(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create(
            user_id=1,
            user='testuser',
            fname='Test',
            lname='User',
            email='testuser@example.com',
            password='testpassword',
            credits=200,
            day_streak=5,
            day_streak_left=5,
            hint_ava=0
        )

        self.user_built_in = UserBuiltIn.objects.create_user(
            username='testuser',
            password='testpassword',
            first_name='Test',
            last_name='User',
            email='testuser@example.com'
        )

        self.client = Client()
        
        login_url = reverse('login')

        # Get the CSRF token first by making a GET request
        response = self.client.get(login_url)
        csrf_token = response.cookies['csrftoken'].value  # Extract the CSRF token

        # Now submit the POST request with the CSRF token
        response = self.client.post(
            login_url,
            {   
                'csrfmiddlewaretoken': csrf_token,
                'username': 'testuser',
                'password': 'testpassword'
            }
        )

    def test_reward_page_view(self):
        response = self.client.get(reverse('reward'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,'reward.html')

    def test_redeem_credits_reward(self):
        initial_credit = self.user.credits
        initial_day_streak = self.user.day_streak
        initial_day_streak_left = self.user.day_streak_left

        # trade credits reward_id equals 0
        response = self.client.get(reverse('redeem_reward', args=[0]))
        self.user.refresh_from_db()

        # 3 day streak earn 10 credits
        self.assertEqual(self.user.credits, initial_credit + 10)  # earn 10 credits
        self.assertEqual(self.user.day_streak, initial_day_streak) # Day streak is not deducted
        self.assertEqual(self.user.day_streak_left, initial_day_streak_left - 3)  # day_streak_left decreased by 3
        self.assertIn('Redeem Success!', response.context['noti'])

    def test_redeem_hint_reward(self):
        initial_credit = self.user.credits
        initial_hint = self.user.hint_ava

        # trade hints reward_id equals 999
        response = self.client.get(reverse('redeem_reward', args=[999]))
        self.user.refresh_from_db()
        self.assertEqual(self.user.hint_ava, initial_hint + 1)  # hint_ava incresed by  1
        self.assertEqual(self.user.credits, initial_credit - 50)  # credits decreased by 50
        self.assertIn('Redeem Success!', response.context['noti'])

    def test_redeem_title_reward(self):
        initial_credit = self.user.credits

        # trade title reward_id equals 1 to 9
        response = self.client.get(reverse('redeem_reward', args=[1]))
        self.user.refresh_from_db()
        title_ava = self.user.title_ava

        self.assertIn('Letter Seeker', title_ava)  # Title added
        self.assertEqual(self.user.credits, initial_credit - 10)  # credits decreased by 10

    def test_redeem_card_color_reward(self):
        initial_credit = self.user.credits

        # trade card color reward_id equals 10 to 18
        response = self.client.get(reverse('redeem_reward', args=[10]))
        self.user.refresh_from_db()
        card_color_ava = self.user.card_color_ava

        self.assertIn('#FF5733', card_color_ava)  # Card color added
        self.assertEqual(self.user.credits, initial_credit - 100)  # credits decreased by 100

    def test_redeem_lucky_chest_earn_not_duplicated(self):
        initial_credit = self.user.credits
        initial_amount_card_color_ava = len(self.user.card_color_ava)

        # trade lucky chest reward_id equals 50
        response = self.client.get(reverse('redeem_reward', args=[50]))
        self.user.refresh_from_db()
        card_color_ava = self.user.card_color_ava

        self.assertEqual(self.user.credits, initial_credit - 150)  # credits decreased by 150
        self.assertEqual(len(card_color_ava), initial_amount_card_color_ava + 1) # 1 random color added

        # random check card color in lucky chest add to user's card color
        self.assertTrue(any(color in card_color_ava for color in [
            "#D3D3D3", "#F0F0F0", "#8B8B8B", "#B0B0B0", "#A9A9A9", 
        "#FF8C00", "#FF6347", "#FFD700", "#87CEFA", "#98FB98",
        "#FF69B4", "#00BFFF", "#32CD32", "#FF4500", "#9932CC",
        "#FF1493", "#8A2BE2", "#7FFF00", "#FF6347", "#00CED1",
        "linear-gradient(45deg, #D3D3D3, #F0F0F0)", "linear-gradient(45deg, #FF8C00, #FF6347)",
        "linear-gradient(45deg, #FFD700, #98FB98)", "linear-gradient(45deg, #87CEFA, #FFD700)",
        "linear-gradient(45deg, #FF69B4, #FF4500)", "linear-gradient(45deg, #00BFFF, #32CD32)",
        "linear-gradient(45deg, #9932CC, #FF69B4)", "linear-gradient(45deg, #FF4500, #00BFFF)"
        ]))


    def test_redeem_lucky_chest_earn_duplicated(self):
        initial_credit = self.user.credits
        # trade lucky chest reward_id equals 50

        lucky_chest = [
            "#D3D3D3", "#F0F0F0", "#8B8B8B", "#B0B0B0", "#A9A9A9", 
        "#FF8C00", "#FF6347", "#FFD700", "#87CEFA", "#98FB98",
        "#FF69B4", "#00BFFF", "#32CD32", "#FF4500", "#9932CC",
        "#FF1493", "#8A2BE2", "#7FFF00", "#FF6347", "#00CED1",
        "linear-gradient(45deg, #D3D3D3, #F0F0F0)", "linear-gradient(45deg, #FF8C00, #FF6347)",
        "linear-gradient(45deg, #FFD700, #98FB98)", "linear-gradient(45deg, #87CEFA, #FFD700)",
        "linear-gradient(45deg, #FF69B4, #FF4500)", "linear-gradient(45deg, #00BFFF, #32CD32)",
        "linear-gradient(45deg, #9932CC, #FF69B4)", "linear-gradient(45deg, #FF4500, #00BFFF)"
        ]

        # make user.card_color_ava have got all colors in lucky chest
        self.user.card_color_ava = lucky_chest
        self.user.save()

        response = self.client.get(reverse('redeem_reward', args=[50]))
        initial_amount_card_color_ava = len(self.user.card_color_ava)
        self.user.refresh_from_db()

        card_color_ava = self.user.card_color_ava

        self.assertEqual(self.user.credits, initial_credit - 150)  # credits decreased by 150

        # random check card color in lucky chest add to user's card color
        self.assertTrue(any(color in card_color_ava for color in lucky_chest))

        message = response.context['noti']
        self.assertIn('You already have this color.', message) # check noti message contains
        self.assertEqual(initial_amount_card_color_ava, len(card_color_ava))

    def test_invalid_reward_id(self):
        response = self.client.get(reverse('redeem_reward', args=[9999]))
        self.assertIn('Invalid reward_id!', response.context['noti'])