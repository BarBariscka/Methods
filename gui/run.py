"""Точка входа для запуска GUI."""
import sys
import os

# Добавляем родительскую директорию в path для импорта server.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import main

if __name__ == "__main__":
    main()
