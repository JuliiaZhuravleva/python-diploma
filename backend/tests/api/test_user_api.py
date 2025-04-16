from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from backend.models import ConfirmEmailToken, Contact

User = get_user_model()


class UserRegistrationTestCase(TestCase):
    """
    Тесты для API регистрации пользователя.
    """

    def setUp(self):
        """
        Подготовка тестового окружения.
        """
        self.client = APIClient()
        self.register_url = reverse('api:user-register')
        self.valid_user_data = {
            'email': 'test@example.com',
            'password': 'ValidPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'company': 'Test Company',
            'position': 'Developer'
        }

    def test_user_registration_success(self):
        """
        Тестирование успешной регистрации пользователя.
        """
        response = self.client.post(self.register_url, self.valid_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['status'])

        # Проверяем, что пользователь создан в базе данных
        self.assertTrue(User.objects.filter(email=self.valid_user_data['email']).exists())

        # Проверяем, что пользователь неактивен до подтверждения email
        user = User.objects.get(email=self.valid_user_data['email'])
        self.assertFalse(user.is_active)

        # Проверяем, что создан токен для подтверждения email
        self.assertTrue(ConfirmEmailToken.objects.filter(user=user).exists())

    def test_user_registration_invalid_email(self):
        """
        Тестирование регистрации с неверным форматом email.
        """
        invalid_data = self.valid_user_data.copy()
        invalid_data['email'] = 'invalid-email'

        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn('email', response.data['errors'])

    def test_user_registration_invalid_password(self):
        """
        Тестирование регистрации со слабым паролем.
        """
        invalid_data = self.valid_user_data.copy()
        invalid_data['password'] = '123'  # Слишком короткий

        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn('password', response.data['errors'])

    def test_user_registration_duplicate_email(self):
        """
        Тестирование регистрации с уже существующим email.
        """
        # Создаем пользователя с тем же email
        User.objects.create_user(
            email=self.valid_user_data['email'],
            password='SomePassword123!',
            is_active=True
        )

        response = self.client.post(self.register_url, self.valid_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        # В зависимости от вашей реализации, может проверяться либо 'email', либо '__all__'
        self.assertTrue('email' in response.data['errors'] or '__all__' in response.data['errors'])


class UserLoginTestCase(TestCase):
    """
    Тесты для API входа пользователя.
    """

    def setUp(self):
        """
        Подготовка тестового окружения.
        """
        self.client = APIClient()
        self.login_url = reverse('api:user-login')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'ValidPass123!'
        }

        # Создаем активного пользователя
        self.user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            is_active=True
        )

    def test_user_login_success(self):
        """
        Тестирование успешного входа пользователя.
        """
        response = self.client.post(self.login_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)

    def test_user_login_invalid_credentials(self):
        """
        Тестирование входа с неверными учетными данными.
        """
        invalid_data = self.user_data.copy()
        invalid_data['password'] = 'WrongPassword123!'

        response = self.client.post(self.login_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_inactive_user(self):
        """
        Тестирование входа с неактивным пользователем.
        """
        # Деактивируем пользователя
        self.user.is_active = False
        self.user.save()

        response = self.client.post(self.login_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ContactAPITestCase(TestCase):
    """
    Тесты для API работы с контактами пользователя.
    """

    def setUp(self):
        """
        Подготовка тестового окружения.
        """
        self.client = APIClient()
        self.contact_url = reverse('api:user-contact')

        # Создаем пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='ValidPass123!',
            is_active=True
        )

        # Аутентифицируем клиент
        self.client.force_authenticate(user=self.user)

        # Тестовые данные для контакта
        self.contact_data = {
            'city': 'Test City',
            'street': 'Test Street',
            'house': '123',
            'structure': 'A',
            'building': '1',
            'apartment': '42',
            'phone': '+12345678901'
        }

    def test_create_contact(self):
        """
        Тестирование создания нового контакта.
        """
        response = self.client.post(self.contact_url, self.contact_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что контакт создан в базе данных
        self.assertTrue(Contact.objects.filter(user=self.user).exists())
        contact = Contact.objects.get(user=self.user)
        self.assertEqual(contact.city, self.contact_data['city'])
        self.assertEqual(contact.street, self.contact_data['street'])
        self.assertEqual(contact.phone, self.contact_data['phone'])

    def test_get_contacts(self):
        """
        Тестирование получения списка контактов пользователя.
        """
        # Создаем несколько контактов
        Contact.objects.create(user=self.user, **self.contact_data)
        Contact.objects.create(
            user=self.user,
            city='Another City',
            street='Another Street',
            house='456',
            phone='+19876543210'
        )

        response = self.client.get(self.contact_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_update_contact(self):
        """
        Тестирование обновления контакта.
        """
        # Создаем контакт
        contact = Contact.objects.create(user=self.user, **self.contact_data)

        # Данные для обновления
        update_data = {
            'id': contact.id,
            'city': 'Updated City',
            'street': 'Updated Street'
        }

        response = self.client.put(self.contact_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что контакт обновлен в базе данных
        contact.refresh_from_db()
        self.assertEqual(contact.city, update_data['city'])
        self.assertEqual(contact.street, update_data['street'])
        # Другие поля должны остаться без изменений
        self.assertEqual(contact.phone, self.contact_data['phone'])

    def test_delete_contact(self):
        """
        Тестирование мягкого удаления контактов.
        """
        # Создаем несколько контактов
        contact1 = Contact.objects.create(user=self.user, **self.contact_data)
        contact2 = Contact.objects.create(
            user=self.user,
            city='Another City',
            street='Another Street',
            house='456',
            phone='+19876543210'
        )

        # Удаляем первый контакт
        response = self.client.delete(self.contact_url, {'items': str(contact1.id)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Обновляем объект из базы данных
        contact1 = Contact.objects.get(id=contact1.id)

        # Проверяем, что контакт помечен как удаленный
        self.assertTrue(contact1.is_deleted)

        # Проверяем, что физически контакт все еще существует
        self.assertTrue(Contact.objects.filter(id=contact1.id).exists())

        # Проверяем, что второй контакт не помечен как удаленный
        contact2 = Contact.objects.get(id=contact2.id)
        self.assertFalse(contact2.is_deleted)

