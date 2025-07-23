#!/bin/bash

# Activate your Python virtual environment
source ~/.venvs/emailai/bin/activate

# Run Python code inside Django shell
python manage.py shell -c "
import imaplib
import smtplib

EMAIL = 'ashewatkar713@gmail.com'
APP_PASSWORD = 'mgfnnttafnnybrey'

# Test IMAP connection
try:
    imap = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    imap.login(EMAIL, APP_PASSWORD)
    print('✓ IMAP connection successful')
    imap.logout()
except Exception as e:
    print(f'✗ IMAP connection failed: {e}')

# Test SMTP connection
try:
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.starttls()
    smtp.login(EMAIL, APP_PASSWORD)
    print('✓ SMTP connection successful')
    smtp.quit()
except Exception as e:
    print(f'✗ SMTP connection failed: {e}')
"
