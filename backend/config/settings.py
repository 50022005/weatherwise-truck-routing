import os
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent.parent.parent
DEBUG=os.getenv('DJANGO_DEBUG','0')=='1'
SECRET_KEY=os.getenv('DJANGO_SECRET_KEY','local-development-only-do-not-use-in-production')
if not DEBUG and SECRET_KEY.startswith('local-development'):
    # API is stateless (no accounts, sessions, cookies or signed data).
    import secrets
    SECRET_KEY=secrets.token_urlsafe(64)
ALLOWED_HOSTS=os.getenv('DJANGO_ALLOWED_HOSTS','localhost,127.0.0.1,testserver').split(',')
for variable in ['VERCEL_URL','VERCEL_PROJECT_PRODUCTION_URL']:
    if os.getenv(variable): ALLOWED_HOSTS.append(os.environ[variable])
INSTALLED_APPS=['django.contrib.staticfiles','routing']
MIDDLEWARE=['django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','django.middleware.common.CommonMiddleware']
ROOT_URLCONF='config.urls'
WSGI_APPLICATION='config.wsgi.application'
STATIC_URL='/assets/'
STATIC_ROOT=BASE_DIR/'staticfiles'
STATICFILES_DIRS=[BASE_DIR/'dist'/'assets'] if (BASE_DIR/'dist'/'assets').exists() else []
USE_TZ=True
TIME_ZONE='UTC'
DATA_UPLOAD_MAX_MEMORY_SIZE=16384
CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'weatherwise','TIMEOUT':600,'OPTIONS':{'MAX_ENTRIES':500}}}
SECURE_CONTENT_TYPE_NOSNIFF=True
# OSM requires a Referer on browser tile requests; Django defaults to same-origin.
SECURE_REFERRER_POLICY='strict-origin-when-cross-origin'
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')
