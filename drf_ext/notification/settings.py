import os

EMAIL_BACKEND = "djrill.mail.backends.djrill.DjrillBackend"
MANDRILL_API_KEY = os.environ.get('APP_MANDRILL_API_KEY') or 'TKGm8q_XVAjZZ8moDEbzmQ'  # test key
