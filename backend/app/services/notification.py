import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("stocksense.notifications")


class NotificationProvider(ABC):
    """Abstract interface for external notification delivery (Email, SMS)."""

    @abstractmethod
    def send_email(self, to_email: str, subject: str, content: str) -> bool:
        """Send an email notification."""
        pass

    @abstractmethod
    def send_sms(self, to_phone: str, message: str) -> bool:
        """Send an SMS notification."""
        pass

    @abstractmethod
    def send_otp(self, recipient: str, otp_code: str, channel: str = "email") -> bool:
        """Send a one-time password (OTP) via the requested channel."""
        pass


class ConsoleNotificationProvider(NotificationProvider):
    """Development and testing provider that logs notifications to stdout."""

    def send_email(self, to_email: str, subject: str, content: str) -> bool:
        logger.info(f"[EMAIL DEV] To: {to_email} | Subject: {subject} | Content: {content}")
        return True

    def send_sms(self, to_phone: str, message: str) -> bool:
        logger.info(f"[SMS DEV] To: {to_phone} | Message: {message}")
        return True

    def send_otp(self, recipient: str, otp_code: str, channel: str = "email") -> bool:
        logger.info(
            f"===================================================\n"
            f"[OTP SERVICE] Channel: {channel.upper()} | Recipient: {recipient}\n"
            f"Your StockSense Verification Code is: >>> {otp_code} <<<\n"
            f"==================================================="
        )
        return True


class NotificationService:
    """Service to coordinate dispatching notifications through the active provider."""

    def __init__(self, provider: NotificationProvider | None = None) -> None:
        self.provider = provider or ConsoleNotificationProvider()

    def send_password_reset_otp(self, email: str, otp_code: str) -> bool:
        """Send password reset OTP code to user's registered email."""
        return self.provider.send_otp(recipient=email, otp_code=otp_code, channel="email")


# Global notification service instance
notification_service = NotificationService()
