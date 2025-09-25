#!/usr/bin/env python
"""Health check script for Docker container"""
import sys
import os

sys.path.insert(0, '/app')

try:
    from bot.config import get_config
    config = get_config()
    print('✅ Health check passed')
    sys.exit(0)
except Exception as e:
    print(f'❌ Health check failed: {e}')
    sys.exit(1)