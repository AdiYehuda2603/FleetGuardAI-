"""
FleetGuard AI - Email Configuration Manager
===========================================
User-friendly email settings management with .env auto-configuration.

This module provides a GUI-based interface for configuring email sync settings,
eliminating the need for manual .env file editing.

Author: FleetGuard AI Team
Date: 2025-12-19
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import imaplib
import ssl
from dataclasses import dataclass


@dataclass
class EmailProvider:
    """Predefined email provider configurations."""
    name: str
    imap_server: str
    imap_port: int
    app_password_url: str
    folder_examples: List[str]


# ========================================
# Predefined Email Providers
# ========================================
PROVIDERS = {
    "Gmail": EmailProvider(
        name="Gmail",
        imap_server="imap.gmail.com",
        imap_port=993,
        app_password_url="https://myaccount.google.com/apppasswords",
        folder_examples=["INBOX", "[Gmail]/All Mail", "תווית מותאמת אישית"]
    ),
    "Outlook": EmailProvider(
        name="Outlook/Office 365",
        imap_server="outlook.office365.com",
        imap_port=993,
        app_password_url="https://account.microsoft.com/security",
        folder_examples=["INBOX", "Invoices", "חשבוניות"]
    ),
    "Yahoo": EmailProvider(
        name="Yahoo Mail",
        imap_server="imap.mail.yahoo.com",
        imap_port=993,
        app_password_url="https://login.yahoo.com/account/security",
        folder_examples=["INBOX", "Invoices"]
    )
}


class EmailConfigManager:
    """
    Manages email configuration with user-friendly interface.

    Features:
    - Test IMAP connection
    - Discover available email folders
    - Automatically save settings to .env file
    - Load current configuration
    """

    def __init__(self, env_path: str = ".env"):
        """
        Initialize EmailConfigManager.

        Args:
            env_path: Path to .env file (default: ".env")
        """
        self.env_path = Path(env_path)
        self.current_config = self._load_current_config()

    def test_connection(self, email_address: str, password: str, provider: str) -> Tuple[bool, str, List[str]]:
        """
        Test IMAP connection and retrieve available folders.

        Args:
            email_address: Email address
            password: App-specific password
            provider: Provider name (Gmail, Outlook, Yahoo)

        Returns:
            Tuple of (success, message, folders_list)
        """
        if provider not in PROVIDERS:
            return False, f"ספק לא נתמך: {provider}", []

        provider_config = PROVIDERS[provider]

        try:
            # Establish SSL/TLS connection
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED

            imap = imaplib.IMAP4_SSL(
                host=provider_config.imap_server,
                port=provider_config.imap_port,
                ssl_context=context
            )

            # Login
            imap.login(email_address, password)

            # Get folder list
            status, folder_data = imap.list()
            folders = []

            if status == 'OK':
                for item in folder_data:
                    if item:
                        try:
                            # Parse folder name from IMAP response
                            # Format: (flags) "delimiter" "folder_name"
                            # Try UTF-8 decoding first, then latin-1 as fallback
                            try:
                                decoded_item = item.decode('utf-8')
                            except UnicodeDecodeError:
                                decoded_item = item.decode('latin-1', errors='ignore')

                            parts = decoded_item.split('"')
                            if len(parts) >= 3:
                                folder_name = parts[-2]

                                # Handle IMAP UTF-7 encoding for Hebrew/special chars
                                # Gmail uses modified UTF-7 (mUTF-7) for folder names
                                try:
                                    # Try to decode as UTF-7 if it contains '&'
                                    if '&' in folder_name and folder_name != 'INBOX':
                                        import codecs
                                        # Gmail's modified UTF-7 encoding
                                        folder_name = self._decode_imap_utf7(folder_name)
                                except Exception:
                                    pass  # Keep original if decoding fails

                                folders.append(folder_name)
                        except Exception as e:
                            # If all else fails, try to get raw folder name
                            try:
                                raw = item.decode('utf-8', errors='replace')
                                if '"' in raw:
                                    folder_name = raw.split('"')[-2]
                                    folders.append(folder_name)
                            except Exception:
                                continue

            # Logout
            imap.logout()

            return True, "✅ החיבור הצליח!", folders

        except imaplib.IMAP4.error as e:
            error_msg = str(e).upper()
            if "AUTHENTICATIONFAILED" in error_msg or "AUTHENTICATE" in error_msg:
                return False, "❌ שגיאת אימות - בדוק את כתובת המייל והסיסמה", []
            return False, f"❌ שגיאת IMAP: {str(e)}", []

        except Exception as e:
            return False, f"❌ שגיאת חיבור: {str(e)}", []

    def save_configuration(self, provider: str, email_address: str, password: str,
                          folder: str, enabled: bool = True) -> Tuple[bool, str]:
        """
        Save email configuration to .env file.

        Args:
            provider: Provider name (Gmail, Outlook, Yahoo)
            email_address: Email address
            password: App-specific password
            folder: Email folder to monitor
            enabled: Enable/disable email sync

        Returns:
            Tuple of (success, message)
        """
        if provider not in PROVIDERS:
            return False, f"ספק לא נתמך: {provider}"

        provider_config = PROVIDERS[provider]

        try:
            # Read existing .env file
            if self.env_path.exists():
                # Try utf-8-sig first (handles BOM), fallback to utf-8
                try:
                    with open(self.env_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                        lines = f.readlines()
                except Exception:
                    with open(self.env_path, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
            else:
                lines = []

            # Email configuration to write
            email_config = {
                'EMAIL_FETCH_ENABLED': str(enabled).lower(),
                'EMAIL_IMAP_SERVER': provider_config.imap_server,
                'EMAIL_IMAP_PORT': str(provider_config.imap_port),
                'EMAIL_ADDRESS': email_address,
                'EMAIL_PASSWORD': password,
                'EMAIL_FOLDER': folder,
                'EMAIL_MARK_AS_READ': 'true',
                'EMAIL_MAX_FETCH': '50',
                'EMAIL_DATE_FILTER_DAYS': '30'
            }

            # Find email configuration section
            email_section_start = -1
            email_section_end = -1

            for i, line in enumerate(lines):
                if '# Email Invoice Fetcher Configuration' in line or '# ========================================' in line:
                    if email_section_start == -1:
                        # Check if next line mentions email
                        if i + 1 < len(lines) and 'Email' in lines[i + 1]:
                            email_section_start = i

                if email_section_start != -1 and email_section_end == -1:
                    # Look for next section or end of file
                    if line.startswith('#') and '=========' in line and i > email_section_start + 2:
                        email_section_end = i
                        break

            # Build new .env content
            new_lines = []

            if email_section_start != -1:
                # Keep everything before email section
                new_lines.extend(lines[:email_section_start])
            else:
                # Keep all existing lines
                new_lines.extend(lines)
                # Add separator
                if new_lines and not new_lines[-1].strip().endswith('\n'):
                    new_lines.append('\n')

            # Add email configuration section
            new_lines.append('\n')
            new_lines.append('# ========================================\n')
            new_lines.append('# Email Invoice Fetcher Configuration\n')
            new_lines.append('# ========================================\n')

            for key, value in email_config.items():
                new_lines.append(f'{key}={value}\n')

            # Add everything after email section (if it existed)
            if email_section_end != -1 and email_section_end < len(lines):
                new_lines.append('\n')
                new_lines.extend(lines[email_section_end:])

            # Write to .env file
            # Use utf-8-sig to handle BOM and ensure compatibility on Windows
            with open(self.env_path, 'w', encoding='utf-8-sig', errors='replace') as f:
                f.writelines(new_lines)

            # Reload configuration
            self.current_config = self._load_current_config()

            return True, "✅ ההגדרות נשמרו בהצלחה ל-.env!"

        except Exception as e:
            return False, f"❌ שגיאה בשמירת הגדרות: {str(e)}"

    def _load_current_config(self) -> Dict[str, str]:
        """
        Load current email configuration from .env file.

        Returns:
            Dictionary of email configuration
        """
        config = {}

        try:
            if self.env_path.exists():
                # Try utf-8-sig first (handles BOM on Windows), fallback to utf-8
                try:
                    with open(self.env_path, 'r', encoding='utf-8-sig', errors='replace') as f:
                        for line in f:
                            line = line.strip()
                            # Skip comments and empty lines
                            if line and not line.startswith('#'):
                                if '=' in line:
                                    key, value = line.split('=', 1)
                                    config[key.strip()] = value.strip()
                except Exception:
                    with open(self.env_path, 'r', encoding='utf-8', errors='replace') as f:
                        for line in f:
                            line = line.strip()
                            # Skip comments and empty lines
                            if line and not line.startswith('#'):
                                if '=' in line:
                                    key, value = line.split('=', 1)
                                    config[key.strip()] = value.strip()

        except Exception as e:
            print(f"Error loading config: {e}")

        return config

    def _decode_imap_utf7(self, folder_name: str) -> str:
        """
        Decode IMAP modified UTF-7 encoding to Unicode.

        Gmail uses modified UTF-7 (mUTF-7) for folder names with special characters.
        Example: "&APYA9g-" -> "שלום"

        Args:
            folder_name: Folder name in modified UTF-7

        Returns:
            Decoded folder name in UTF-8
        """
        try:
            # IMAP uses modified UTF-7 where:
            # - '&' is the shift character (like '+' in base64)
            # - '-' is the end shift character
            # - Characters between & and - are base64-encoded UTF-16BE

            import base64

            # Replace IMAP shift chars with standard base64
            # & becomes +, &- becomes & (literal ampersand)
            parts = []
            i = 0
            while i < len(folder_name):
                if folder_name[i] == '&':
                    # Find the end of encoded section
                    end = folder_name.find('-', i)
                    if end == -1:
                        end = len(folder_name)

                    encoded = folder_name[i+1:end]

                    if encoded == '':
                        # &- means literal &
                        parts.append('&')
                    else:
                        # Decode base64 to UTF-16BE
                        try:
                            # Replace ',' with '/' for standard base64
                            encoded = encoded.replace(',', '/')
                            # Add padding if needed
                            padding = (4 - len(encoded) % 4) % 4
                            encoded += '=' * padding

                            decoded_bytes = base64.b64decode(encoded)
                            decoded_str = decoded_bytes.decode('utf-16-be')
                            parts.append(decoded_str)
                        except Exception:
                            # If decoding fails, keep original
                            parts.append(folder_name[i:end+1])

                    i = end + 1
                else:
                    parts.append(folder_name[i])
                    i += 1

            return ''.join(parts)

        except Exception as e:
            # If anything fails, return original
            return folder_name

    def get_provider_info(self, provider: str) -> Optional[EmailProvider]:
        """
        Get provider information.

        Args:
            provider: Provider name

        Returns:
            EmailProvider dataclass or None
        """
        return PROVIDERS.get(provider)

    def get_available_providers(self) -> List[str]:
        """
        Get list of available providers.

        Returns:
            List of provider names
        """
        return list(PROVIDERS.keys())


# ========================================
# Example Usage
# ========================================
if __name__ == "__main__":
    # Example: Test connection
    manager = EmailConfigManager()

    # Test Gmail connection
    success, message, folders = manager.test_connection(
        email_address="test@gmail.com",
        password="your-app-password",
        provider="Gmail"
    )

    print(f"Connection: {message}")
    if success:
        print(f"Folders found: {len(folders)}")
        for folder in folders[:5]:
            print(f"  - {folder}")

    # Save configuration
    success, message = manager.save_configuration(
        provider="Gmail",
        email_address="test@gmail.com",
        password="your-app-password",
        folder="INBOX",
        enabled=True
    )

    print(f"Save: {message}")
