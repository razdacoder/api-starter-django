from django.core.cache import cache
from django.utils.crypto import get_random_string


def generate_otp(user, purpose, ttl=600, cooldown=60):
    """
    Generate a One-Time Password (OTP) for a specific user and purpose.
    Add a cooldown period for resending OTPs.
    """
    cache_key = f"otp:{purpose}:{user.pk}"
    otp_cooldown_key = f"otp_cooldown:{purpose}:{user.pk}"
    
    if cache.get(otp_cooldown_key):
        raise Exception("Please wait before requesting another OTP.")
    
    existing_otp = cache.get(cache_key)
    if existing_otp:
        return existing_otp  # Reuse the existing OTP if it's still valid

    otp = get_random_string(length=6, allowed_chars="0123456789")
    cache.set(cache_key, otp, ttl)
    cache.set(otp_cooldown_key, True, cooldown)  # Set cooldown timer
    return otp


def validate_otp(user, purpose, provided_otp):
    """
    Validate the provided OTP for a specific user and purpose.

    Args:
        user (User): The user object for whom the OTP was generated.
        purpose (str): The purpose of the OTP (e.g., 'activation', 'password_reset').
        provided_otp (str): The OTP provided by the user.

    Returns:
        bool: True if the OTP is valid, False otherwise.

    Raises:
        ValueError: If the OTP is invalid or expired.
    """
    cache_key = f"otp:{purpose}:{user.pk}"
    stored_otp = cache.get(cache_key)

    if stored_otp is None:
        raise ValueError("The OTP has expired. Please request a new one.")

    if stored_otp != provided_otp:
        raise ValueError("Invalid OTP. Please try again.")

    # OTP is valid, delete it to prevent reuse
    cache.delete(cache_key)
    return True