import os

EMAIL_BACKEND = "djrill.mail.backends.djrill.DjrillBackend"
MANDRILL_API_KEY = os.environ.get('APP_MANDRILL_API_KEY') or 'TKGm8q_XVAjZZ8moDEbzmQ'  # test key

PUSHER_APP_ID = os.environ.get('APP_PUSHER_APP_ID')
PUSHER_KEY = os.environ.get('APP_PUSHER_KEY')
PUSHER_SECRET = os.environ.get('APP_PUSHER_SECRET')
PUSHER_CLUSTER = os.environ.get('APP_PUSHER_CUSTER')
