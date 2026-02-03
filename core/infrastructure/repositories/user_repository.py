"""
Infrastructure Layer: User Repository
دسترسی به مدل User و انجام عملیات DB
"""
from django.contrib.auth.models import User
from typing import Optional


class UserRepository:
    """
    Repository برای مدیریت دسترسی به مدل User
    """
    
    @staticmethod
    def get_user_by_username_and_email(username: str, email: str) -> Optional[User]:
        """
        گرفتن کاربر بر اساس username و email
        
        Args:
            username: نام کاربری
            email: ایمیل
        
        Returns:
            User یا None
        """
        try:
            return User.objects.get(username=username, email=email)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """
        گرفتن کاربر بر اساس username
        
        Args:
            username: نام کاربری
        
        Returns:
            User یا None
        """
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def update_password(user: User, new_password: str) -> None:
        """
        بروزرسانی پسورد کاربر
        
        Args:
            user: شیء User
            new_password: پسورد جدید (plain text)
        """
        user.set_password(new_password)
        user.save(update_fields=['password'])
    
    @staticmethod
    def user_exists_by_username(username: str) -> bool:
        """
        بررسی وجود کاربر بر اساس username
        
        Args:
            username: نام کاربری
        
        Returns:
            bool: آیا کاربر وجود دارد
        """
        return User.objects.filter(username=username).exists()
    
    @staticmethod
    def user_exists_by_email(email: str) -> bool:
        """
        بررسی وجود کاربر بر اساس email
        
        Args:
            email: ایمیل
        
        Returns:
            bool: آیا کاربر وجود دارد
        """
        return User.objects.filter(email=email).exists()
