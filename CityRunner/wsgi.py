"""
WSGI config for CityRunner project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CityRunner.settings')

application = get_wsgi_application()

try:
    from django.core.management import call_command

    call_command('migrate', interactive=False, verbosity=0)
except Exception as exc:
    print(f'Inicialização do Django concluída com aviso: {exc}')

app = application
