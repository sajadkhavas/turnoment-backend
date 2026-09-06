from .base import *  # noqa: F403

DEBUG = True
OTP_SENDER_BACKEND = "apps.accounts.otp.ConsoleOtpSender"

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]
