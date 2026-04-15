import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from api.models import Video, Like

User = get_user_model()

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def user_owner():
    return User.objects.create_user(username='owner', password='111')

@pytest.fixture
def user_guest():
    return User.objects.create_user(username='guest', password='111')

@pytest.fixture
def video_pub(user_owner):
    return Video.objects.create(owner=user_owner, name='Public Video', is_published=True)

@pytest.fixture
def video_priv(user_owner):
    return Video.objects.create(owner=user_owner, name='Private Video', is_published=False)



# Маркер django_db разрешает тестам создавать записи в тестовой базе данных
@pytest.mark.django_db
class TestVideoAPI:

    # Тесты детального просмотра видео (GET /v1/videos/{id}/)
    def test_get_published_video(self, client, video_pub):
        response = client.get(f'/v1/videos/{video_pub.id}/')
        assert response.status_code == 200
        assert response.data['name'] == 'Public Video'

    def test_get_private_video_by_owner(self, client, user_owner, video_priv):
        client.force_authenticate(user=user_owner)
        response = client.get(f'/v1/videos/{video_priv.id}/')
        assert response.status_code == 200

    def test_get_private_video_by_guest_returns_403(self, client, user_guest, video_priv):
        client.force_authenticate(user=user_guest)
        response = client.get(f'/v1/videos/{video_priv.id}/')
        assert response.status_code == 403

    def test_video_detail_user_expand(self, client, video_pub):
        response = client.get(f'/v1/videos/{video_pub.id}/?user_expand=true')
        assert response.status_code == 200
        assert isinstance(response.data['owner'], dict)
        assert response.data['owner']['username'] == 'owner'

    # Тест списка видео (GET /v1/videos/)
    def test_get_video_list(self, client, video_pub):
        response = client.get('/v1/videos/')
        assert response.status_code == 200
        assert len(response.data) > 0

        # Защита от пагинации, данные лежат в 'results'
        data = response.data['results'] if 'results' in response.data else response.data
        assert 'id' in data[0]
        assert 'name' in data[0]
        assert 'owner_id' in data[0]

    # Проверка логики лайков (POST /v1/videos/{id}/likes/)
    def test_like_toggle_logic(self, client, user_guest, video_pub):
        client.force_authenticate(user=user_guest)

        # Ставим лайк
        response = client.post(f'/v1/videos/{video_pub.id}/likes/')
        # проверяем на зарегистрированном юзере
        assert response.status_code == 201
        assert Like.objects.filter(user=user_guest, video=video_pub).exists()
        client.logout()
        # проверяем на анониме
        response = client.post(f'/v1/videos/{video_pub.id}/likes/')
        assert  response.status_code in (401, 403)

    # Статистика (GET /v1/videos/statistics-*/)
    def test_get_statistics_group_by(self, client, user_owner, video_pub):
        response = client.get('/v1/videos/statistics-group-by/')
        assert response.status_code == 200

        # Проверяем наличие ключей, которые требовались в ТЗ
        data = response.data['results'] if 'results' in response.data else response.data
        if len(data) > 0:
            assert 'id' in data[0]
            assert 'total_likes' in data[0]

    def test_get_statistics_subquery(self, client, user_owner, video_pub):
        response = client.get('/v1/videos/statistics-subquery/')
        assert response.status_code == 200

        # Проверяем наличие ключей, которые требовались в ТЗ
        data = response.data['results'] if 'results' in response.data else response.data
        if len(data) > 0:
            assert 'id' in data[0]
            assert 'total_likes' in data[0]