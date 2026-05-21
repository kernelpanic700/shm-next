from app.api.v1.auth import AuthController
from app.api.v1.abonents import AbonentController
from app.api.v1.tariffs import TariffController
from app.api.v1.services import ServiceController
from app.api.v1.payments import PaymentController
from app.api.v1.dashboard import DashboardController

__all__ = [
    'AuthController',
    'AbonentController',
    'TariffController',
    'ServiceController',
    'PaymentController',
    'DashboardController',
]
