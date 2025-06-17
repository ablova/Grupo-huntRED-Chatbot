import pytest
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth.models import AnonymousUser
from app.decorators import role_required, permission_required  # business_unit_required debe implementarse si es necesario


def mock_view(request):
    return HttpResponse('OK')

@pytest.fixture
def super_admin_user():
    class MockUser:
        def is_authenticated(self):
            return True
        def is_super_admin(self):
            return True
        def get_business_units(self):
            return ['BU1', 'BU2']
        def has_permission(self, perm):
            return True
    return MockUser()

@pytest.fixture
def consultant_user():
    class MockUser:
        def is_authenticated(self):
            return True
        def is_super_admin(self):
            return False
        def get_roles(self):
            return ['Consultant (BU Complete)']
        def get_business_units(self):
            return ['BU1']
        def has_permission(self, perm):
            return perm == 'view_data'
    return MockUser()

@pytest.fixture
def unauthorized_user():
    class MockUser:
        def is_authenticated(self):
            return True
        def is_super_admin(self):
            return False
        def get_roles(self):
            return ['Guest']
        def get_business_units(self):
            return []
        def has_permission(self, perm):
            return False
    return MockUser()

@pytest.fixture
def anonymous_user():
    return AnonymousUser()


def test_role_required_super_admin(super_admin_user):
    decorated_view = role_required('Consultant (BU Complete)')(mock_view)
    request = MagicMock()
    request.user = super_admin_user
    response = decorated_view(request)
    assert isinstance(response, HttpResponse)
    assert response.content == b'OK'


def test_role_required_authorized(consultant_user):
    decorated_view = role_required('Consultant (BU Complete)')(mock_view)
    request = MagicMock()
    request.user = consultant_user
    response = decorated_view(request)
    assert isinstance(response, HttpResponse)
    assert response.content == b'OK'


def test_role_required_unauthorized(unauthorized_user):
    decorated_view = role_required('Consultant (BU Complete)')(mock_view)
    request = MagicMock()
    request.user = unauthorized_user
    response = decorated_view(request)
    assert isinstance(response, HttpResponseForbidden)


def test_role_required_anonymous(anonymous_user):
    decorated_view = role_required('Consultant (BU Complete)')(mock_view)
    request = MagicMock()
    request.user = anonymous_user
    response = decorated_view(request)
    assert isinstance(response, HttpResponseForbidden)


def test_business_unit_required_authorized(consultant_user):
    decorated_view = business_unit_required('BU1')(mock_view)
    request = MagicMock()
    request.user = consultant_user
    response = decorated_view(request)
    assert isinstance(response, HttpResponse)
    assert response.content == b'OK'


def test_business_unit_required_unauthorized(consultant_user):
    decorated_view = business_unit_required('BU2')(mock_view)
    request = MagicMock()
    request.user = consultant_user
    response = decorated_view(request)
    assert isinstance(response, HttpResponseForbidden)


def test_permission_required_authorized(consultant_user):
    decorated_view = permission_required('view_data')(mock_view)
    request = MagicMock()
    request.user = consultant_user
    response = decorated_view(request)
    assert isinstance(response, HttpResponse)
    assert response.content == b'OK'


def test_permission_required_unauthorized(consultant_user):
    decorated_view = permission_required('edit_data')(mock_view)
    request = MagicMock()
    request.user = consultant_user
    response = decorated_view(request)
    assert isinstance(response, HttpResponseForbidden)
