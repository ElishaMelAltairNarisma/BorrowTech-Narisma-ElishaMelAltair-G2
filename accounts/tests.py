from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

User = get_user_model()


class CustomUserModelTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='student1',
            email='student1@university.edu',
            password='TestPassword123!',
            role=User.Role.STUDENT,
            first_name='Juan',
            last_name='Dela Cruz',
            student_id='2024-IT-001'
        )
        self.custodian = User.objects.create_user(
            username='custodian1',
            email='custodian1@university.edu',
            password='TestPassword123!',
            role=User.Role.CUSTODIAN,
            first_name='Maria',
            last_name='Santos',
            student_id='LAB-STAFF-01'
        )

    def test_user_roles(self):
        self.assertTrue(self.student.is_student_user())
        self.assertFalse(self.student.is_custodian_user())
        self.assertEqual(self.student.get_dashboard_url(), '/dashboard/student/')

        self.assertTrue(self.custodian.is_custodian_user())
        self.assertFalse(self.custodian.is_student_user())
        self.assertEqual(self.custodian.get_dashboard_url(), '/dashboard/custodian/')

    def test_password_is_hashed(self):
        self.assertTrue(self.student.check_password('TestPassword123!'))
        self.assertNotEqual(self.student.password, 'TestPassword123!')


class AccountRegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')

    def test_registration_page_loads(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_successful_student_registration(self):
        data = {
            'username': 'newstudent',
            'email': 'newstudent@university.edu',
            'first_name': 'Carlos',
            'last_name': 'Reyes',
            'student_id': '2024-IT-0999',
            'role': User.Role.STUDENT,
            'department': 'College of Computer Studies',
            'year_level': '2nd Year',
            'contact_number': '+639170001111',
            'password': 'SecurePassword2026!',
            'password_confirm': 'SecurePassword2026!',
        }
        response = self.client.post(self.register_url, data)
        # Should redirect to student dashboard
        self.assertRedirects(response, '/dashboard/student/')

        # Verify user created in DB with hashed password
        created_user = User.objects.get(username='newstudent')
        self.assertTrue(created_user.check_password('SecurePassword2026!'))
        self.assertEqual(created_user.role, User.Role.STUDENT)
        self.assertEqual(created_user.email, 'newstudent@university.edu')

    def test_registration_password_mismatch(self):
        data = {
            'username': 'mismatchuser',
            'email': 'mismatch@university.edu',
            'first_name': 'Test',
            'last_name': 'User',
            'student_id': '2024-IT-0002',
            'role': User.Role.STUDENT,
            'contact_number': '+639170002222',
            'password': 'Password123!',
            'password_confirm': 'PasswordMismatch!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatchuser').exists())
        self.assertFormError(response.context['form'], 'password_confirm', 'Passwords do not match. Please verify your password confirmation.')

    def test_registration_duplicate_username_and_email(self):
        User.objects.create_user(
            username='existinguser',
            email='existing@university.edu',
            password='ExistingPass123!'
        )

        data = {
            'username': 'existinguser',
            'email': 'existing@university.edu',
            'first_name': 'Duplicate',
            'last_name': 'User',
            'student_id': '2024-IT-0003',
            'role': User.Role.STUDENT,
            'contact_number': '+639170003333',
            'password': 'Password123!',
            'password_confirm': 'Password123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.has_error('username'))
        self.assertTrue(form.has_error('email'))


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='john_doe',
            email='john@university.edu',
            password='MySecretPassword123!',
            role=User.Role.STUDENT,
            first_name='John',
            last_name='Doe'
        )
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')

    def test_login_with_username(self):
        response = self.client.post(self.login_url, {
            'username_or_email': 'john_doe',
            'password': 'MySecretPassword123!'
        })
        self.assertRedirects(response, '/dashboard/student/')

    def test_login_with_email(self):
        response = self.client.post(self.login_url, {
            'username_or_email': 'john@university.edu',
            'password': 'MySecretPassword123!'
        })
        self.assertRedirects(response, '/dashboard/student/')

    def test_login_invalid_credentials(self):
        response = self.client.post(self.login_url, {
            'username_or_email': 'john_doe',
            'password': 'WrongPassword999!'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Invalid username/email or password' in m.message for m in messages))

    def test_logout_ends_session(self):
        self.client.login(username='john_doe', password='MySecretPassword123!')
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, reverse('login'))
        # Ensure session is terminated
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login/' in response.url)


class RoleBasedDashboardAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='itstudent',
            email='itstudent@univ.edu',
            password='StudentPassword123!',
            role=User.Role.STUDENT
        )
        self.custodian = User.objects.create_user(
            username='custodian_staff',
            email='custodian@univ.edu',
            password='CustodianPassword123!',
            role=User.Role.CUSTODIAN
        )

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(reverse('student_dashboard'))
        self.assertRedirects(response, f"/login/?next={reverse('student_dashboard')}")

        response = self.client.get(reverse('custodian_dashboard'))
        self.assertRedirects(response, f"/login/?next={reverse('custodian_dashboard')}")

    def test_student_can_access_student_dashboard(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'IT Student Portal')

    def test_student_cannot_access_custodian_dashboard(self):
        """Typing the URL of another role's dashboard must be denied!"""
        self.client.force_login(self.student)
        response = self.client.get(reverse('custodian_dashboard'))
        # Must be denied and redirected to student dashboard
        self.assertRedirects(response, reverse('student_dashboard'))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Access Denied' in m.message for m in messages))

    def test_custodian_can_access_custodian_dashboard(self):
        self.client.force_login(self.custodian)
        response = self.client.get(reverse('custodian_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Laboratory Custodian Console')

    def test_custodian_cannot_access_student_dashboard(self):
        """Custodian typing Student Dashboard URL must be redirected to Custodian Dashboard."""
        self.client.force_login(self.custodian)
        response = self.client.get(reverse('student_dashboard'))
        self.assertRedirects(response, reverse('custodian_dashboard'))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Access Denied' in m.message for m in messages))


class UserProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='profile_user',
            email='profile@university.edu',
            password='TestPassword123!',
            role=User.Role.STUDENT,
            first_name='OriginalFirst',
            last_name='OriginalLast',
            contact_number='+639171112222',
            department='College of Computer Studies'
        )
        self.profile_url = reverse('profile')

    def test_profile_requires_login(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login/' in response.url)

    def test_user_can_view_own_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'OriginalFirst')
        self.assertContains(response, 'profile@university.edu')

    def test_user_can_update_own_profile(self):
        self.client.force_login(self.user)
        data = {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
            'email': 'updated_email@university.edu',
            'contact_number': '+639179998888',
            'student_id': '2024-IT-9999',
            'department': 'Information Technology Dept',
            'year_level': '3rd Year',
        }
        response = self.client.post(self.profile_url, data)
        self.assertRedirects(response, self.profile_url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'UpdatedFirst')
        self.assertEqual(self.user.last_name, 'UpdatedLast')
        self.assertEqual(self.user.email, 'updated_email@university.edu')
        self.assertEqual(self.user.contact_number, '+639179998888')
