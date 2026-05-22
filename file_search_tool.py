#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件搜索工具

import fnmatch
import linecache
import os
import re
import shutil
import stat
import subprocess
import sys
import ctypes
import ctypes.wintypes
import threading
from collections import deque
from datetime import datetime
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QSettings, QTimer, QMutex, QPoint, QEvent,
    QRect, QCoreApplication, QPropertyAnimation, QEasingCurve, QVariantAnimation,
    pyqtProperty, QObject
)
from PyQt5.QtGui import (
    QFont, QIcon, QMouseEvent, QPainter, QPolygon, QColor, QPalette, QPen,
    QBrush, QLinearGradient
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox, QTableWidget,
    QTableWidgetItem, QFileDialog, QHeaderView, QMessageBox, QProgressBar,
    QGroupBox, QSplitter, QAbstractItemView, QMenu, QInputDialog, QDialog,
    QGridLayout, QTabWidget, QTextEdit, QTextBrowser, QStatusBar,
    QSpinBox, QRadioButton, QScrollArea, QSizePolicy, QStyle,
    QStylePainter, QStyleOptionComboBox, QStyleOptionSpinBox, QStyleOptionButton,
    QAction,
    QGraphicsOpacityEffect, QGraphicsColorizeEffect
)
try:
    import send2trash
    SEND2TRASH_AVAILABLE = True
except ImportError:
    SEND2TRASH_AVAILABLE = False

BORDER_WIDTH = 8
CHUNK_SIZE = 64 * 1024
FILTER_DELAY_MS = 100
PREVIEW_LINES_PER_PAGE = 500
MAX_PREVIEW_SIZE = 5 * 1024 * 1024
MAX_PREVIEW_LINES = 5000
TEXT_EXTENSIONS = {
    '.txt', '.py', '.json', '.xml', '.html', '.htm', '.js', '.css', '.md',
    '.log', '.ini', '.cfg', '.yaml', '.yml', '.csv', '.sh', '.bat', '.ps1',
    '.c', '.cpp', '.h', '.hpp', '.java', '.go', '.rs', '.swift', '.kt',
    '.sql', '.r', '.rmd', '.tex', '.markdown', '.rst', '.vue', '.jsx', '.tsx',
    '.scss', '.sass', '.less', '.toml', '.dockerfile', '.makefile', '.cmake'
}

IGNORED_DIRS = {
    '.git', '.svn', '.hg', 'node_modules', '__pycache__', '.idea',
    '.vscode', '.vs', 'dist', 'build', 'target', 'bin', 'obj',
    '.gradle', '.mvn', '.cache', '.tox', '.mypy_cache', '.pytest_cache',
    'venv', '.venv', 'env', '.env', '.direnv', 'vendor', 'Pods',
    '.next', '.nuxt', '.svelte-kit', 'coverage', '.coverage',
    '__pypackages__', '.pytype', 'htmlcov', '.sass-cache',
}
# 深色模式样式 - 修复了下拉箭头和微调框箭头
DARK_STYLE = """
QMainWindow { background-color: #1e1e1e; }
QWidget { background-color: #1e1e1e; color: #d4d4d4; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; }
QGroupBox { 
    border: 1px solid #3c3c3c; 
    border-radius: 6px; 
    margin-top: 12px; 
    padding: 16px 10px 10px 10px; 
    color: #e0e0e0; 
    font-weight: bold;
    font-size: 11px;
}
QGroupBox::title { 
    subcontrol-origin: margin; 
    left: 12px; 
    padding: 0 8px; 
    color: #0078d4;
}
QLineEdit { 
    background-color: #2d2d2d; 
    color: #d4d4d4; 
    border: 1px solid #3c3c3c; 
    border-radius: 5px; 
    padding: 8px 10px;
    selection-background-color: #264f78;
}
QLineEdit:focus { 
    border-color: #0078d4; 
    background-color: #323232;
}
QLineEdit:hover {
    border-color: #555;
}
QPushButton { 
    background-color: #3c3c3c; 
    color: #d4d4d4; 
    border: 1px solid #3c3c3c; 
    border-radius: 5px; 
    padding: 8px 16px;
    font-weight: 500;
}
QPushButton:hover { 
    background-color: #4a4a4a; 
    border-color: #555;
}
QPushButton:pressed { 
    background-color: #555; 
}
QPushButton:checked { 
    background-color: #0078d4; 
    border-color: #0078d4;
    color: #fff; 
}
QPushButton:disabled { 
    background-color: #2d2d2d; 
    color: #555;
    border-color: #2d2d2d;
}
QComboBox { 
    background-color: #2d2d2d; 
    color: #d4d4d4; 
    border: 1px solid #3c3c3c; 
    border-radius: 5px; 
    padding: 4px 8px;
    min-width: 60px;
}
QComboBox:hover {
    border-color: #555;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 20px;
    border: none;
    background: transparent;
}
/* 修复下拉箭头：使用 border 绘制三角形，并明确位置 */
QComboBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border: solid;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #d4d4d4;
    margin-right: 6px;
    background: transparent;
}
QComboBox QAbstractItemView { 
    background-color: #2d2d2d; 
    color: #d4d4d4; 
    selection-background-color: #0078d4;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
}
QTableWidget { 
    background-color: #1e1e1e; 
    color: #d4d4d4; 
    gridline-color: #2d2d2d; 
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    outline: none;
}
QTableWidget::item { 
    padding: 4px 8px;
    outline: none;
}
QTableWidget::item:selected { 
    background-color: #264f78; 
    color: #d4d4d4;
    outline: none;
}
QTableWidget::item:hover {
    background-color: #2a2d2e;
}
QHeaderView::section { 
    background-color: #252526; 
    color: #b4b4b4; 
    border: none;
    border-bottom: 1px solid #3c3c3c;
    border-right: 1px solid #3c3c3c;
    padding: 8px 10px;
    font-weight: 500;
}
QHeaderView::section:hover {
    background-color: #2d2d2d;
}
QTableCornerButton::section { 
    background-color: #252526; 
    border: none;
    border-bottom: 1px solid #3c3c3c;
}
QProgressBar { 
    background-color: #2d2d2d; 
    border: none;
    border-radius: 4px; 
    text-align: center; 
    color: #d4d4d4;
    height: 8px;
}
QProgressBar::chunk { 
    background-color: #0078d4; 
    border-radius: 4px; 
}
QCheckBox { 
    color: #d4d4d4;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
}
QCheckBox::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}
QCheckBox::indicator:hover {
    border-color: #0078d4;
}
QRadioButton { 
    color: #d4d4d4;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 9px;
}
QRadioButton::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}
QRadioButton::indicator:hover {
    border-color: #0078d4;
}
QSpinBox { 
    background-color: #2d2d2d; 
    color: #d4d4d4; 
    border: 1px solid #3c3c3c; 
    border-radius: 5px; 
    padding: 2px;
    min-width: 50px;
    max-width: 80px;
}
QSpinBox:hover {
    border-color: #555;
}
QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 16px;
    height: 12px;
    border: none;
    border-top-right-radius: 4px;
    background-color: #3c3c3c;
}
QSpinBox::up-button:hover {
    background-color: #4a4a4a;
}
QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 16px;
    height: 12px;
    border: none;
    border-bottom-right-radius: 4px;
    background-color: #3c3c3c;
}
QSpinBox::down-button:hover {
    background-color: #4a4a4a;
}
/* 修复微调框箭头：使用 border 绘制三角形，并明确位置 */
QSpinBox::up-arrow {
    image: none;
    width: 0;
    height: 0;
    border-style: solid;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #d4d4d4;
    background: transparent;
}
QSpinBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-style: solid;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #d4d4d4;
    background: transparent;
}
QStatusBar { 
    background-color: #007acc; 
    color: #fff;
    font-weight: 500;
    padding: 4px 8px;
}
QTabWidget::pane { 
    border: 1px solid #3c3c3c;
    border-radius: 6px;
}
QTabBar::tab { 
    background-color: #2d2d2d; 
    color: #888; 
    padding: 10px 18px; 
    border: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected { 
    background-color: #3c3c3c; 
    color: #fff;
}
QTabBar::tab:hover:!selected {
    background-color: #353535;
    color: #aaa;
}
QMenu { 
    background-color: #2d2d2d; 
    color: #d4d4d4; 
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item { 
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected { 
    background-color: #264f78; 
}
QMenu::separator { 
    height: 1px; 
    background: #3c3c3c; 
    margin: 4px 8px; 
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #555;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #666;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #555;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #666;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}
QSplitter::handle { 
    background-color: #3c3c3c;
    width: 6px;
}
QSplitter::handle:hover {
    background-color: #0078d4;
}
QSplitter::handle:horizontal {
    width: 6px;
}
QSplitter::handle:vertical {
    height: 6px;
}
QLabel { color: #d4d4d4; }
QDialog { background-color: #1e1e1e; color: #d4d4d4; }
QScrollArea { background-color: #1e1e1e; border: none; }
QTextEdit { 
    background-color: #2d2d2d; 
    color: #d4d4d4; 
    border: 1px solid #3c3c3c; 
    border-radius: 5px;
}
QTextBrowser { background-color: #1e1e1e; color: #d4d4d4; border: none; }
QToolTip { 
    background-color: #2d2d2d; 
    color: #d4d4d4; 
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 4px 8px;
}
#titleBar {
    background-color: #323336;
    border-bottom: 1px solid #252526;
}
#titleBar QPushButton {
    background-color: transparent;
    border: none;
    color: #d4d4d4;
    padding: 6px 12px;
    font-size: 14px;
    border-radius: 0px;
}
#titleBar QPushButton:hover {
    background-color: #454545;
}
#titleBar QPushButton#closeButton:hover {
    background-color: #e81123;
    color: white;
}
"""
# 浅色模式样式 - 修复了下拉箭头和微调框箭头
LIGHT_STYLE = """
QMainWindow { background-color: #f8f8f8; }
QWidget { background-color: #f8f8f8; color: #1e1e1e; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; }
QGroupBox { 
    border: 1px solid #ddd; 
    border-radius: 6px; 
    margin-top: 12px; 
    padding: 16px 10px 10px 10px; 
    color: #333; 
    font-weight: bold;
    font-size: 11px;
}
QGroupBox::title { 
    subcontrol-origin: margin; 
    left: 12px; 
    padding: 0 8px; 
    color: #0078d4;
}
QLineEdit { 
    background-color: #fff; 
    color: #1e1e1e; 
    border: 1px solid #ddd; 
    border-radius: 5px; 
    padding: 8px 10px;
    selection-background-color: #cce4f7;
}
QLineEdit:focus { 
    border-color: #0078d4; 
    background-color: #fff;
}
QLineEdit:hover {
    border-color: #bbb;
}
QPushButton { 
    background-color: #f0f0f0; 
    color: #1e1e1e; 
    border: 1px solid #ddd; 
    border-radius: 5px; 
    padding: 8px 16px;
    font-weight: 500;
}
QPushButton:hover { 
    background-color: #e5e5e5; 
    border-color: #ccc;
}
QPushButton:pressed { 
    background-color: #d5d5d5; 
}
QPushButton:checked { 
    background-color: #0078d4; 
    border-color: #0078d4;
    color: #fff; 
}
QPushButton:disabled { 
    background-color: #f5f5f5; 
    color: #999;
    border-color: #e5e5e5;
}
QComboBox { 
    background-color: #fff; 
    color: #1e1e1e; 
    border: 1px solid #ddd; 
    border-radius: 5px; 
    padding: 4px 8px;
    min-width: 60px;
}
QComboBox:hover {
    border-color: #bbb;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 20px;
    border: none;
    background: transparent;
}
/* 修复下拉箭头 */
QComboBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-style: solid;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #1e1e1e;
    margin-right: 6px;
    background: transparent;
}
QComboBox QAbstractItemView { 
    background-color: #fff; 
    color: #1e1e1e; 
    selection-background-color: #0078d4;
    selection-color: #fff;
    border: 1px solid #ddd;
    border-radius: 4px;
}
QTableWidget { 
    background-color: #fff; 
    color: #1e1e1e; 
    gridline-color: #eee; 
    border: 1px solid #ddd;
    border-radius: 6px;
    outline: none;
}
QTableWidget::item { 
    padding: 4px 8px;
    outline: none;
}
QTableWidget::item:selected { 
    background-color: #cce4f7; 
    color: #1e1e1e;
    outline: none;
}
QTableWidget::item:hover {
    background-color: #f5f5f5;
}
QHeaderView::section { 
    background-color: #fafafa; 
    color: #555; 
    border: none;
    border-bottom: 1px solid #ddd;
    border-right: 1px solid #eee;
    padding: 8px 10px;
    font-weight: 500;
}
QHeaderView::section:hover {
    background-color: #f0f0f0;
}
QTableCornerButton::section { 
    background-color: #fafafa; 
    border: none;
    border-bottom: 1px solid #ddd;
}
QProgressBar { 
    background-color: #e5e5e5; 
    border: none;
    border-radius: 4px; 
    text-align: center; 
    color: #1e1e1e;
    height: 8px;
}
QProgressBar::chunk { 
    background-color: #0078d4; 
    border-radius: 4px; 
}
QCheckBox { 
    color: #1e1e1e;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    background-color: #fff;
    border: 1px solid #ccc;
    border-radius: 4px;
}
QCheckBox::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}
QCheckBox::indicator:hover {
    border-color: #0078d4;
}
QRadioButton { 
    color: #1e1e1e;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    background-color: #fff;
    border: 1px solid #ccc;
    border-radius: 9px;
}
QRadioButton::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}
QRadioButton::indicator:hover {
    border-color: #0078d4;
}
QSpinBox { 
    background-color: #fff; 
    color: #1e1e1e; 
    border: 1px solid #ddd; 
    border-radius: 5px; 
    padding: 2px;
    min-width: 50px;
    max-width: 80px;
}
QSpinBox:hover {
    border-color: #bbb;
}
QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 16px;
    height: 12px;
    border: none;
    border-top-right-radius: 4px;
    background-color: #f0f0f0;
}
QSpinBox::up-button:hover {
    background-color: #e5e5e5;
}
QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 16px;
    height: 12px;
    border: none;
    border-bottom-right-radius: 4px;
    background-color: #f0f0f0;
}
QSpinBox::down-button:hover {
    background-color: #e5e5e5;
}
/* 修复微调框箭头 */
QSpinBox::up-arrow {
    image: none;
    width: 0;
    height: 0;
    border-style: solid;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #1e1e1e;
    background: transparent;
}
QSpinBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-style: solid;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #1e1e1e;
    background: transparent;
}
QStatusBar { 
    background-color: #007acc; 
    color: #fff;
    font-weight: 500;
    padding: 4px 8px;
}
QTabWidget::pane { 
    border: 1px solid #ddd;
    border-radius: 6px;
}
QTabBar::tab { 
    background-color: #f0f0f0; 
    color: #666; 
    padding: 10px 18px; 
    border: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected { 
    background-color: #fff; 
    color: #1e1e1e;
}
QTabBar::tab:hover:!selected {
    background-color: #e5e5e5;
    color: #333;
}
QMenu { 
    background-color: #fff; 
    color: #1e1e1e; 
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item { 
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected { 
    background-color: #cce4f7; 
}
QMenu::separator { 
    height: 1px; 
    background: #eee; 
    margin: 4px 8px; 
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #ccc;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #bbb;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #ccc;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #bbb;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}
QSplitter::handle { 
    background-color: #ddd;
    width: 6px;
}
QSplitter::handle:hover {
    background-color: #0078d4;
}
QSplitter::handle:horizontal {
    width: 6px;
}
QSplitter::handle:vertical {
    height: 6px;
}
QLabel { color: #1e1e1e; }
QDialog { background-color: #f8f8f8; color: #1e1e1e; }
QScrollArea { background-color: #f8f8f8; border: none; }
QTextEdit { 
    background-color: #fff; 
    color: #1e1e1e; 
    border: 1px solid #ddd; 
    border-radius: 5px;
}
QTextBrowser { background-color: #fff; color: #1e1e1e; border: none; }
QToolTip { 
    background-color: #fff; 
    color: #1e1e1e; 
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 4px 8px;
}
#titleBar {
    background-color: #f0f0f0;
    border-bottom: 1px solid #ddd;
}
#titleBar QPushButton {
    background-color: transparent;
    border: none;
    color: #1e1e1e;
    padding: 6px 12px;
    font-size: 14px;
    border-radius: 0px;
}
#titleBar QPushButton:hover {
    background-color: #e5e5e5;
}
#titleBar QPushButton#closeButton:hover {
    background-color: #e81123;
    color: white;
}
"""


def translate_context_menu(menu: QMenu):
    """将标准上下文菜单项翻译为中文（健壮匹配）"""
    for action in menu.actions():
        if action.isSeparator():
            continue
        text = action.text()
        clean = text.replace('&', '').replace('_', '').strip()
        lower = clean.lower()

        if 'undo' in lower:
            action.setText('撤销(&U)')
        elif 'redo' in lower:
            action.setText('重做(&R)')
        elif 'cut' in lower:
            action.setText('剪切(&T)')
        elif 'copy' in lower:
            action.setText('复制(&C)')
        elif 'paste' in lower:
            action.setText('粘贴(&P)')
        elif 'delete' in lower:
            action.setText('删除(&D)')
        elif 'select all' in lower or 'selectall' in lower:
            action.setText('全选(&A)')
        elif 'clear' in lower:
            action.setText('清除')


def is_regex_safe(pattern: str) -> bool:
    if len(pattern) > 500:
        return False
    if re.search(r'\([^\)]*\)\{[\d,]+\}', pattern):
        return False
    if re.search(r'\[[^\]]*\]\{[\d,]+\}', pattern):
        return False
    if pattern.count('(') > 20 or pattern.count('[') > 20:
        return False
    return True


def parse_extension_list(s: str) -> List[str]:
    if not s.strip():
        return []
    items = [item.strip() for item in s.split(',') if item.strip()]
    normalized = []
    for item in items:
        if not item.startswith('.'):
            item = '.' + item
        normalized.append(item.lower())
    return list(dict.fromkeys(normalized))


def is_system_dark_mode() -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
    except Exception:
        return False


class AnimatedPushButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._scale = 1.0
        self._opacity = 1.0
        self._hover_color = QColor(0, 120, 212)
        self._animation = QPropertyAnimation(self, b"scale")
        self._animation.setDuration(100)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)

    def get_scale(self):
        return self._scale

    def set_scale(self, value):
        self._scale = value
        self.update()

    scale = pyqtProperty(float, fget=get_scale, fset=set_scale)

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        if self._opacity_effect:
            self._opacity_effect.setOpacity(value)

    opacity = pyqtProperty(float, fget=get_opacity, fset=set_opacity)

    def animate_click(self):
        self._animation.setStartValue(1.0)
        self._animation.setKeyValueAt(0.5, 0.92)
        self._animation.setEndValue(1.0)
        self._animation.start()

    def animate_press(self):
        self._animation.stop()
        self._animation.setStartValue(self._scale)
        self._animation.setEndValue(0.92)
        self._animation.start()

    def animate_release(self):
        self._animation.stop()
        self._animation.setStartValue(self._scale)
        self._animation.setEndValue(1.0)
        self._animation.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.animate_press()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.animate_release()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        center = self.rect().center()
        painter.translate(center)
        painter.scale(self._scale, self._scale)
        painter.translate(-center)
        painter.drawControl(QStyle.CE_PushButton, opt)


class AnimatedProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self._progress = 0
        self._minimum = 0
        self._maximum = 100
        self._stripe_offset = 0
        self._is_indeterminate = True
        self._stripe_timer = QTimer(self)
        self._stripe_timer.timeout.connect(self._update_stripe)
        self._pulse_phase = 0

    def setRange(self, minimum: int, maximum: int):
        self._minimum = minimum
        self._maximum = maximum
        if minimum == 0 and maximum == 0:
            self._is_indeterminate = True
            if self.isVisible():
                self._stripe_timer.start(30)
        else:
            self._is_indeterminate = False
            self._stripe_timer.stop()
        self.update()

    def setValue(self, value: int):
        self._progress = value
        self._is_indeterminate = False
        self._stripe_timer.stop()
        self.update()

    def value(self) -> int:
        return self._progress

    def reset(self):
        self._progress = self._minimum
        self.update()

    def set_progress(self, value: int):
        self._progress = value
        self._is_indeterminate = False
        self._stripe_timer.stop()
        self.update()

    def set_indeterminate(self, indeterminate: bool):
        self._is_indeterminate = indeterminate
        if indeterminate:
            self._stripe_timer.start(30)
        self.update()

    def _update_stripe(self):
        self._stripe_offset = (self._stripe_offset + 3) % 20
        self._pulse_phase = (self._pulse_phase + 0.1) % (2 * 3.14159)
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if self._is_indeterminate:
            self._stripe_timer.start(30)

    def hideEvent(self, event):
        super().hideEvent(event)
        self._stripe_timer.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        is_dark = self.palette().window().color().lightness() < 128
        bg_color = QColor("#2d2d2d") if is_dark else QColor("#e5e5e5")
        progress_color = QColor("#0078d4")
        painter.fillRect(rect, bg_color)
        painter.setPen(Qt.NoPen)
        if self._is_indeterminate:
            bar_width = rect.width() // 4
            x = int((self._stripe_offset / 20) * rect.width() * 2 - bar_width)
            x = x % (rect.width() + bar_width) - bar_width
            gradient = QLinearGradient(x, 0, x + bar_width, 0)
            gradient.setColorAt(0, QColor(0, 120, 212, 100))
            gradient.setColorAt(0.5, QColor(0, 120, 212, 255))
            gradient.setColorAt(1, QColor(0, 120, 212, 100))
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(QRect(x, 0, bar_width, rect.height()), 4, 4)
            stripe_width = 10
            for i in range(-stripe_width * 2, rect.width() + stripe_width * 2, stripe_width):
                stripe_x = i + self._stripe_offset
                if stripe_x < 0 or stripe_x >= rect.width():
                    continue
                stripe_gradient = QLinearGradient(stripe_x - stripe_width // 2, 0, stripe_x + stripe_width // 2, 0)
                stripe_gradient.setColorAt(0, QColor(255, 255, 255, 0))
                stripe_gradient.setColorAt(0.5, QColor(255, 255, 255, 40))
                stripe_gradient.setColorAt(1, QColor(255, 255, 255, 0))
                painter.setBrush(QBrush(stripe_gradient))
                painter.drawRect(QRect(stripe_x - stripe_width // 2, 0, stripe_width, rect.height()))
        else:
            range_span = self._maximum - self._minimum
            if range_span <= 0:
                progress_pct = 0
            else:
                progress_pct = (self._progress - self._minimum) / range_span
            progress_width = int(rect.width() * progress_pct)
            if progress_width > 0:
                gradient = QLinearGradient(0, 0, progress_width, 0)
                gradient.setColorAt(0, QColor(0, 100, 180))
                gradient.setColorAt(0.5, QColor(0, 140, 230))
                gradient.setColorAt(1, QColor(0, 100, 180))
                painter.setBrush(QBrush(gradient))
                painter.drawRoundedRect(QRect(0, 0, progress_width, rect.height()), 4, 4)
                for i in range(0, progress_width + 10, 10):
                    stripe_x = i - self._stripe_offset
                    if stripe_x < 0 or stripe_x >= progress_width:
                        continue
                    stripe_gradient = QLinearGradient(stripe_x - 5, 0, stripe_x + 5, 0)
                    stripe_gradient.setColorAt(0, QColor(255, 255, 255, 0))
                    stripe_gradient.setColorAt(0.5, QColor(255, 255, 255, 50))
                    stripe_gradient.setColorAt(1, QColor(255, 255, 255, 0))
                    painter.setBrush(QBrush(stripe_gradient))
                    painter.drawRect(QRect(stripe_x - 5, 0, 10, rect.height()))
        painter.end()


class FadeTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fade_opacity = 1.0
        self._fade_animation = QPropertyAnimation(self, b"fadeOpacity")
        self._fade_animation.setDuration(200)
        self._fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)

    def get_fade_opacity(self):
        return self._fade_opacity

    def set_fade_opacity(self, value):
        self._fade_opacity = value
        if self._opacity_effect:
            self._opacity_effect.setOpacity(value)

    fadeOpacity = pyqtProperty(float, fget=get_fade_opacity, fset=set_fade_opacity)

    def fade_in(self):
        self._fade_animation.stop()
        self._fade_animation.setStartValue(0.3)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.start()

    def fade_out(self):
        self._fade_animation.stop()
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.3)
        self._fade_animation.start()

    def setRowCount(self, rows):
        super().setRowCount(rows)
        if rows > 0:
            self.fade_in()


class AnimatedTitleBarButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._hover_progress = 0.0
        self._animation = QPropertyAnimation(self, b"hoverProgress")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._is_close_button = False

    def get_hover_progress(self):
        return self._hover_progress

    def set_hover_progress(self, value):
        self._hover_progress = value
        self.update()

    hoverProgress = pyqtProperty(float, fget=get_hover_progress, fset=set_hover_progress)

    def set_close_button(self, is_close: bool):
        self._is_close_button = is_close

    def enterEvent(self, event):
        self._animation.stop()
        self._animation.setStartValue(self._hover_progress)
        self._animation.setEndValue(1.0)
        self._animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animation.stop()
        self._animation.setStartValue(self._hover_progress)
        self._animation.setEndValue(0.0)
        self._animation.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        if self._is_close_button and self._hover_progress > 0:
            color = QColor(232, 17, 35)
            color.setAlphaF(self._hover_progress)
            painter.fillRect(rect, color)
        elif self._hover_progress > 0:
            color = QColor(69, 69, 69)
            color.setAlphaF(self._hover_progress)
            painter.fillRect(rect, color)
        painter.end()
        super().paintEvent(event)


class AnimatedStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._flash_animation = None
        self._original_style = ""
        self._flash_count = 0
        self._flash_timer = QTimer(self)
        self._flash_timer.timeout.connect(self._do_flash)

    def flash_success(self, duration: int = 300):
        self._original_style = self.styleSheet()
        self._flash_count = 0
        self._flash_timer.start(50)

    def _do_flash(self):
        self._flash_count += 1
        if self._flash_count >= 6:
            self._flash_timer.stop()
            self.setStyleSheet(self._original_style)
            return
        if self._flash_count % 2 == 1:
            self.setStyleSheet("background-color: #107c10; color: #fff; font-weight: 500;")
        else:
            self.setStyleSheet(self._original_style)


class ThemeTransitionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 0.0
        self._color = QColor("#1e1e1e")
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0.0)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.hide()

    def start_transition(self, is_dark: bool, callback=None):
        self._color = QColor("#1e1e1e") if is_dark else QColor("#f8f8f8")
        self._opacity = 0.5
        self._opacity_effect.setOpacity(0.5)
        self.raise_()
        self.show()
        animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        animation.setDuration(200)
        animation.setStartValue(0.5)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        if callback:
            animation.finished.connect(callback)
        animation.start()
        self._animation = animation

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._color)
        painter.end()


class ChineseLineEdit(QLineEdit):
    """支持中文右键菜单的单行编辑框"""
    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        translate_context_menu(menu)
        menu.exec_(event.globalPos())


class ChineseTextEdit(QTextEdit):
    """支持中文右键菜单的多行文本编辑器"""
    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        translate_context_menu(menu)
        menu.exec_(event.globalPos())


class ChineseSpinBox(QSpinBox):
    """支持中文右键菜单的数字调节框，完全自绘，支持长按"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineEdit().installEventFilter(self)
        self.setButtonSymbols(QSpinBox.NoButtons)

        self._timer = QTimer(self)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._on_timer_timeout)
        self._step_direction = 0
        self._btn_width = 20

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ContextMenu and obj == self.lineEdit():
            menu = obj.createStandardContextMenu()
            translate_context_menu(menu)
            menu.exec_(event.globalPos())
            return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        line_edit = self.lineEdit()
        if line_edit:
            rect = self.rect()
            line_rect = QRect(rect.left() + 8, rect.top() + 4,
                              rect.width() - self._btn_width - 12, rect.height() - 8)
            line_edit.setGeometry(line_rect)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect()
        is_dark = self.palette().window().color().lightness() < 128
        bg = QColor("#2d2d2d") if is_dark else QColor("#ffffff")
        border = QColor("#3c3c3c") if is_dark else QColor("#ddd")
        arrow_color = QColor("#d4d4d4") if is_dark else QColor("#1e1e1e")
        btn_bg = QColor("#3c3c3c") if is_dark else QColor("#f0f0f0")

        painter.fillRect(rect, bg)
        painter.setPen(QPen(border, 1))
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 5, 5)

        btn_rect = QRect(rect.right() - self._btn_width, rect.top(),
                         self._btn_width, rect.height())
        up_rect = QRect(btn_rect.left(), btn_rect.top(),
                        self._btn_width, btn_rect.height() // 2)
        down_rect = QRect(btn_rect.left(), up_rect.bottom(),
                          self._btn_width, btn_rect.height() - up_rect.height())

        painter.fillRect(up_rect, btn_bg)
        painter.fillRect(down_rect, btn_bg)
        painter.setPen(QPen(border, 1))
        painter.drawLine(btn_rect.left(), up_rect.bottom(),
                         btn_rect.right(), up_rect.bottom())

        painter.setPen(Qt.NoPen)
        painter.setBrush(arrow_color)
        up_center = up_rect.center()
        up_tri = QPolygon([
            QPoint(up_center.x() - 4, up_center.y() + 2),
            QPoint(up_center.x() + 4, up_center.y() + 2),
            QPoint(up_center.x(), up_center.y() - 3)
        ])
        painter.drawPolygon(up_tri)

        down_center = down_rect.center()
        down_tri = QPolygon([
            QPoint(down_center.x() - 4, down_center.y() - 2),
            QPoint(down_center.x() + 4, down_center.y() - 2),
            QPoint(down_center.x(), down_center.y() + 3)
        ])
        painter.drawPolygon(down_tri)
        painter.end()

    def _button_rects(self):
        rect = self.rect()
        btn_rect = QRect(rect.right() - self._btn_width, rect.top(),
                         self._btn_width, rect.height())
        up_rect = QRect(btn_rect.left(), btn_rect.top(),
                        self._btn_width, btn_rect.height() // 2)
        down_rect = QRect(btn_rect.left(), up_rect.bottom(),
                          self._btn_width, btn_rect.height() - up_rect.height())
        return btn_rect, up_rect, down_rect

    def mousePressEvent(self, event):
        btn_rect, up_rect, down_rect = self._button_rects()
        if btn_rect.contains(event.pos()):
            if up_rect.contains(event.pos()):
                self._step_direction = 1
                self.stepUp()
            elif down_rect.contains(event.pos()):
                self._step_direction = -1
                self.stepDown()
            else:
                return
            self._timer.start()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._timer.stop()
        self._step_direction = 0
        super().mouseReleaseEvent(event)

    def _on_timer_timeout(self):
        if self._step_direction == 1:
            self.stepUp()
        elif self._step_direction == -1:
            self.stepDown()


class DropLineEdit(ChineseLineEdit):
    """支持拖拽目录的单行编辑框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isdir(path):
                self.setText(path)
            elif os.path.isfile(path):
                self.setText(os.path.dirname(path))
        event.acceptProposedAction()


class PreviewTextBrowser(QTextBrowser):
    """预览浏览器，支持双击复制选中文本"""
    doubleClicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        translate_context_menu(menu)
        menu.exec_(event.globalPos())


class CustomComboBox(QComboBox):
    """自定义下拉框，完全自绘"""
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect()
        is_dark = self.palette().window().color().lightness() < 128
        bg_color = QColor("#2d2d2d") if is_dark else QColor("#ffffff")
        border_color = QColor("#3c3c3c") if is_dark else QColor("#ddd")
        text_color = QColor("#d4d4d4") if is_dark else QColor("#1e1e1e")

        painter.fillRect(rect, bg_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 5, 5)

        text = self.currentText()
        if text:
            painter.setPen(text_color)
            font = self.font()
            painter.setFont(font)
            text_rect = rect.adjusted(8, 4, -25, -4)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, text)

        arrow_rect = QRect(rect.right() - 20, rect.top(), 20, rect.height())
        arrow_width = 10
        arrow_height = 6
        x = arrow_rect.center().x() - arrow_width // 2
        y = arrow_rect.center().y() - arrow_height // 2

        points = QPolygon([
            QPoint(x, y),
            QPoint(x + arrow_width, y),
            QPoint(x + arrow_width // 2, y + arrow_height)
        ])

        painter.setBrush(text_color)
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(points)
        painter.end()


class FilePropertiesDialog(QDialog):
    def __init__(self, name: str, path: str, ext: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.path = path
        self.ext = ext
        self._preview_lines = 50
        self._total_lines = 0
        self._file_lines = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f'{self.name} 属性')
        self.setMinimumSize(450, 500)
        layout = QVBoxLayout(self)
        tab_widget = QTabWidget()
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        info_grid = QGridLayout()
        row = 0
        info_grid.addWidget(QLabel('文件名:'), row, 0)
        name_edit = ChineseLineEdit(self.name)
        name_edit.setReadOnly(True)
        info_grid.addWidget(name_edit, row, 1)
        copy_btn = QPushButton('复制')
        copy_btn.setFixedWidth(60)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.name))
        info_grid.addWidget(copy_btn, row, 2)
        row += 1
        info_grid.addWidget(QLabel('类型:'), row, 0)
        type_label = QLabel('文件夹' if self.ext == '<DIR>' else f'文件 ({self.ext})')
        info_grid.addWidget(type_label, row, 1)
        row += 1
        info_grid.addWidget(QLabel('位置:'), row, 0)
        location_text = os.path.dirname(self.path)
        location_edit = ChineseLineEdit(location_text)
        location_edit.setReadOnly(True)
        info_grid.addWidget(location_edit, row, 1)
        copy_btn2 = QPushButton('复制')
        copy_btn2.setFixedWidth(60)
        copy_btn2.clicked.connect(lambda: QApplication.clipboard().setText(location_text))
        info_grid.addWidget(copy_btn2, row, 2)
        row += 1
        info_grid.addWidget(QLabel('完整路径:'), row, 0)
        full_path_edit = ChineseLineEdit(self.path)
        full_path_edit.setReadOnly(True)
        info_grid.addWidget(full_path_edit, row, 1)
        copy_btn3 = QPushButton('复制')
        copy_btn3.setFixedWidth(60)
        copy_btn3.clicked.connect(lambda: QApplication.clipboard().setText(self.path))
        info_grid.addWidget(copy_btn3, row, 2)
        if self.ext != '<DIR>':
            row += 1
            info_grid.addWidget(QLabel('大小:'), row, 0)
            try:
                size = os.path.getsize(self.path)
                size_label = QLabel(self.format_size(size))
            except OSError:
                size_label = QLabel('无法获取')
            info_grid.addWidget(size_label, row, 1)
        row += 1
        info_grid.addWidget(QLabel('创建时间:'), row, 0)
        try:
            ctime = os.path.getctime(self.path)
            ctime_label = QLabel(datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S'))
        except OSError:
            ctime_label = QLabel('无法获取')
        info_grid.addWidget(ctime_label, row, 1)
        row += 1
        info_grid.addWidget(QLabel('修改时间:'), row, 0)
        try:
            mtime = os.path.getmtime(self.path)
            mtime_label = QLabel(datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S'))
        except OSError:
            mtime_label = QLabel('无法获取')
        info_grid.addWidget(mtime_label, row, 1)
        row += 1
        info_grid.addWidget(QLabel('访问时间:'), row, 0)
        try:
            atime = os.path.getatime(self.path)
            atime_label = QLabel(datetime.fromtimestamp(atime).strftime('%Y-%m-%d %H:%M:%S'))
        except OSError:
            atime_label = QLabel('无法获取')
        info_grid.addWidget(atime_label, row, 1)
        row += 1
        info_grid.addWidget(QLabel('属性:'), row, 0)
        try:
            attrs = self.get_attributes(self.path)
            attrs_label = QLabel(attrs)
        except OSError:
            attrs_label = QLabel('无法获取')
        info_grid.addWidget(attrs_label, row, 1)
        general_layout.addLayout(info_grid)
        general_layout.addStretch()
        tab_widget.addTab(general_tab, '常规')
        if self.ext != '<DIR>':
            content_tab = QWidget()
            content_layout = QVBoxLayout(content_tab)
            content_layout.addWidget(QLabel('文件内容预览:'))
            self.preview_text = ChineseTextEdit()
            self.preview_text.setReadOnly(True)
            self.preview_text.setMinimumHeight(200)
            content_layout.addWidget(self.preview_text)
            btn_row = QHBoxLayout()
            self.load_more_btn = QPushButton('加载更多内容')
            self.load_more_btn.clicked.connect(self._load_more)
            btn_row.addWidget(self.load_more_btn)
            self.load_all_btn = QPushButton('加载完整文件')
            self.load_all_btn.clicked.connect(self._load_all)
            btn_row.addWidget(self.load_all_btn)
            btn_row.addStretch()
            content_layout.addLayout(btn_row)
            content_layout.addStretch()
            self._load_content_chunk()
            tab_widget.addTab(content_tab, '内容')
        layout.addWidget(tab_widget)
        btn_layout = QHBoxLayout()
        open_btn = QPushButton('打开文件')
        open_btn.clicked.connect(lambda: os.startfile(self.path) if self.ext != '<DIR>' else None)
        if self.ext == '<DIR>':
            open_btn.setEnabled(False)
        btn_layout.addWidget(open_btn)
        open_folder_btn = QPushButton('打开所在文件夹')
        open_folder_btn.clicked.connect(self._open_in_explorer)
        btn_layout.addWidget(open_folder_btn)
        copy_path_btn = QPushButton('复制完整路径')
        copy_path_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.path))
        btn_layout.addWidget(copy_path_btn)
        btn_layout.addStretch()
        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _load_content_chunk(self):
        if self.ext == '<DIR>':
            return
        try:
            if not self._file_lines:
                with open(self.path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f):
                        self._file_lines.append(line)
                        if i >= self._preview_lines - 1:
                            break
                self._total_lines = -1
            display_lines = self._file_lines[:self._preview_lines]
            self.preview_text.setPlainText(''.join(display_lines) if display_lines else '(空文件)')
            self._update_buttons()
        except Exception as e:
            self.preview_text.setPlainText(f'无法读取文件内容: {e}')
            self._file_lines = []
            self._total_lines = 0

    def _update_buttons(self):
        self._ensure_total_lines()
        if self._preview_lines >= self._total_lines:
            self.load_more_btn.setEnabled(False)
            self.load_all_btn.setEnabled(False)
        else:
            self.load_more_btn.setEnabled(True)
            self.load_all_btn.setEnabled(True)

    def _ensure_total_lines(self):
        if self._total_lines >= 0:
            return
        try:
            count = 0
            with open(self.path, 'r', encoding='utf-8', errors='ignore') as f:
                for _ in f:
                    count += 1
            self._total_lines = count
        except Exception:
            self._total_lines = 0

    def _load_more_lines(self, count: int):
        current = len(self._file_lines)
        try:
            with open(self.path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if i < current:
                        continue
                    self._file_lines.append(line)
                    if len(self._file_lines) >= current + count:
                        break
        except Exception:
            pass

    def _load_more(self):
        if not self._file_lines and self.ext != '<DIR>':
            return
        self._preview_lines += 50
        if len(self._file_lines) < self._preview_lines:
            self._load_more_lines(self._preview_lines - len(self._file_lines))
        display_lines = self._file_lines[:self._preview_lines]
        self.preview_text.setPlainText(''.join(display_lines))
        self._update_buttons()

    def _load_all(self):
        if not self._file_lines and self.ext != '<DIR>':
            return
        self._ensure_total_lines()
        if self._total_lines > len(self._file_lines):
            self._load_more_lines(self._total_lines - len(self._file_lines))
        self._preview_lines = self._total_lines
        self.preview_text.setPlainText(''.join(self._file_lines))
        self._update_buttons()

    def _open_in_explorer(self):
        abs_path = os.path.abspath(self.path)
        if not os.path.exists(abs_path):
            return
        if self.ext == '<DIR>':
            subprocess.run(['explorer', abs_path])
        else:
            subprocess.run(['explorer', '/select,', abs_path])

    def format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f'{size:.2f} {unit}' if unit != 'B' else f'{size} {unit}'
            size /= 1024
        return f'{size:.2f} PB'

    def get_attributes(self, path: str) -> str:
        attrs = []
        st = os.stat(path)
        if os.access(path, os.R_OK):
            attrs.append('可读')
        if os.access(path, os.W_OK):
            attrs.append('可写')
        if os.access(path, os.X_OK):
            attrs.append('可执行')
        try:
            if sys.platform == 'win32' and hasattr(st, 'st_file_attributes'):
                if st.st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
                    attrs.append('只读')
                if st.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN:
                    attrs.append('隐藏')
                if st.st_file_attributes & stat.FILE_ATTRIBUTE_SYSTEM:
                    attrs.append('系统')
                if st.st_file_attributes & stat.FILE_ATTRIBUTE_ARCHIVE:
                    attrs.append('存档')
        except Exception:
            pass
        try:
            if os.path.isfile(path) and os.path.islink(path):
                attrs.append('快捷方式')
        except Exception:
            pass
        if os.path.isdir(path):
            attrs.append('目录')
        return ', '.join(attrs) if attrs else '普通'


class CancellableWorker(QThread):
    finished_search = pyqtSignal(int, list)
    progress = pyqtSignal(str)

    def __init__(self, epoch: int):
        super().__init__()
        self.epoch = epoch
        self._cancel_event = threading.Event()

    def cancel(self):
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()


class SearchWorker(CancellableWorker):
    def __init__(self, folder_path: str, pattern: str, case_sensitive: bool,
                 exact_match: bool, use_regex: bool, algorithm: str, search_type: str,
                 enable_whitelist: bool, whitelist: List[str],
                 enable_blacklist: bool, blacklist: List[str],
                 ignore_common_dirs: bool, epoch: int):
        super().__init__(epoch)
        self.folder_path = folder_path
        self.pattern = pattern
        self.case_sensitive = case_sensitive
        self.exact_match = exact_match
        self.use_regex = use_regex
        self.algorithm = algorithm
        self.search_type = search_type
        self.enable_whitelist = enable_whitelist
        self.whitelist = whitelist
        self.enable_blacklist = enable_blacklist
        self.blacklist = blacklist
        self.ignore_common_dirs = ignore_common_dirs

    def _should_skip_dir(self, name: str) -> bool:
        if self.ignore_common_dirs and name in IGNORED_DIRS:
            return True
        return False

    def _should_include_file(self, ext: str) -> bool:
        if ext == '<DIR>':
            return True
        if self.enable_whitelist and ext not in self.whitelist:
            return False
        if self.enable_blacklist and ext in self.blacklist:
            return False
        return True

    def match_name(self, name: str) -> bool:
        if not self.pattern:
            return True
        if self.exact_match:
            if self.case_sensitive:
                return name == self.pattern
            else:
                return name.lower() == self.pattern.lower()
        elif self.use_regex:
            try:
                flags = 0 if self.case_sensitive else re.IGNORECASE
                return bool(re.search(self.pattern, name, flags))
            except re.error:
                return False
        else:
            if self.case_sensitive:
                return fnmatch.fnmatch(name, self.pattern)
            else:
                return fnmatch.fnmatch(name.lower(), self.pattern.lower())

    def search_bfs(self, search_files: bool, search_dirs: bool) -> List[Tuple[str, str, str]]:
        results = []
        queue = deque([self.folder_path])
        while queue and not self.is_cancelled():
            current_path = queue.popleft()
            try:
                for entry in os.scandir(current_path):
                    if self.is_cancelled():
                        break
                    if entry.is_dir():
                        if not self._should_skip_dir(entry.name):
                            queue.append(entry.path)
                        if search_dirs and self.match_name(entry.name):
                            results.append((entry.name, entry.path, '<DIR>'))
                    elif entry.is_file():
                        ext = os.path.splitext(entry.name)[1] or '<无后缀>'
                        if search_files and self.match_name(entry.name) and self._should_include_file(ext):
                            results.append((entry.name, entry.path, ext))
            except OSError:
                continue
        return results

    def search_dfs(self, search_files: bool, search_dirs: bool) -> List[Tuple[str, str, str]]:
        results = []
        stack = [self.folder_path]
        while stack and not self.is_cancelled():
            current_path = stack.pop()
            try:
                entries = list(os.scandir(current_path))
                for entry in entries:
                    if self.is_cancelled():
                        break
                    if entry.is_dir():
                        if search_dirs and self.match_name(entry.name):
                            results.append((entry.name, entry.path, '<DIR>'))
                        if not self._should_skip_dir(entry.name):
                            stack.append(entry.path)
                    elif entry.is_file():
                        ext = os.path.splitext(entry.name)[1] or '<无后缀>'
                        if search_files and self.match_name(entry.name) and self._should_include_file(ext):
                            results.append((entry.name, entry.path, ext))
            except OSError:
                continue
        return results

    def search_file_priority(self, search_files: bool, search_dirs: bool) -> List[Tuple[str, str, str]]:
        files_first = []
        dirs_later = []
        queue = deque([self.folder_path])
        while queue and not self.is_cancelled():
            current_path = queue.popleft()
            try:
                for entry in os.scandir(current_path):
                    if self.is_cancelled():
                        break
                    if entry.is_file():
                        ext = os.path.splitext(entry.name)[1] or '<无后缀>'
                        if search_files and self.match_name(entry.name) and self._should_include_file(ext):
                            files_first.append((entry.name, entry.path, ext))
                    elif entry.is_dir():
                        if not self._should_skip_dir(entry.name):
                            queue.append(entry.path)
                        if search_dirs and self.match_name(entry.name):
                            dirs_later.append((entry.name, entry.path, '<DIR>'))
            except OSError:
                continue
        return files_first + dirs_later

    def search_dir_priority(self, search_files: bool, search_dirs: bool) -> List[Tuple[str, str, str]]:
        dirs_first = []
        files_later = []
        queue = deque([self.folder_path])
        while queue and not self.is_cancelled():
            current_path = queue.popleft()
            try:
                for entry in os.scandir(current_path):
                    if self.is_cancelled():
                        break
                    if entry.is_dir():
                        if not self._should_skip_dir(entry.name):
                            queue.append(entry.path)
                        if search_dirs and self.match_name(entry.name):
                            dirs_first.append((entry.name, entry.path, '<DIR>'))
                    elif entry.is_file():
                        ext = os.path.splitext(entry.name)[1] or '<无后缀>'
                        if search_files and self.match_name(entry.name) and self._should_include_file(ext):
                            files_later.append((entry.name, entry.path, ext))
            except OSError:
                continue
        return dirs_first + files_later

    def search_by_extension(self, search_files: bool, search_dirs: bool) -> List[Tuple[str, str, str]]:
        results = []
        files_by_ext = {}
        dirs = []
        queue = deque([self.folder_path])
        while queue and not self.is_cancelled():
            current_path = queue.popleft()
            try:
                for entry in os.scandir(current_path):
                    if self.is_cancelled():
                        break
                    if entry.is_file():
                        ext = os.path.splitext(entry.name)[1] or '<无后缀>'
                        if search_files and self.match_name(entry.name) and self._should_include_file(ext):
                            if ext not in files_by_ext:
                                files_by_ext[ext] = []
                            files_by_ext[ext].append((entry.name, entry.path, ext))
                    elif entry.is_dir():
                        if not self._should_skip_dir(entry.name):
                            queue.append(entry.path)
                        if search_dirs and self.match_name(entry.name):
                            dirs.append((entry.name, entry.path, '<DIR>'))
            except OSError:
                continue
        for ext in sorted(files_by_ext.keys()):
            results.extend(files_by_ext[ext])
        results.extend(dirs)
        return results

    def search_by_size(self, search_files: bool, search_dirs: bool) -> List[Tuple[str, str, str]]:
        results = []
        files_with_size = []
        dirs = []
        queue = deque([self.folder_path])
        while queue and not self.is_cancelled():
            current_path = queue.popleft()
            try:
                for entry in os.scandir(current_path):
                    if self.is_cancelled():
                        break
                    if entry.is_file():
                        ext = os.path.splitext(entry.name)[1] or '<无后缀>'
                        if search_files and self.match_name(entry.name) and self._should_include_file(ext):
                            try:
                                size = entry.stat().st_size
                                files_with_size.append((size, entry.name, entry.path, ext))
                            except OSError:
                                pass
                    elif entry.is_dir():
                        if not self._should_skip_dir(entry.name):
                            queue.append(entry.path)
                        if search_dirs and self.match_name(entry.name):
                            dirs.append((entry.name, entry.path, '<DIR>'))
            except OSError:
                continue
        files_with_size.sort(key=lambda x: x[0])
        for _, name, path, ext in files_with_size:
            results.append((name, path, ext))
        results.extend(dirs)
        return results

    def search_by_date(self, search_files: bool, search_dirs: bool) -> List[Tuple[str, str, str]]:
        results = []
        files_with_date = []
        dirs = []
        queue = deque([self.folder_path])
        while queue and not self.is_cancelled():
            current_path = queue.popleft()
            try:
                for entry in os.scandir(current_path):
                    if self.is_cancelled():
                        break
                    if entry.is_file():
                        ext = os.path.splitext(entry.name)[1] or '<无后缀>'
                        if search_files and self.match_name(entry.name) and self._should_include_file(ext):
                            try:
                                mtime = entry.stat().st_mtime
                                files_with_date.append((mtime, entry.name, entry.path, ext))
                            except OSError:
                                pass
                    elif entry.is_dir():
                        if not self._should_skip_dir(entry.name):
                            queue.append(entry.path)
                        if search_dirs and self.match_name(entry.name):
                            dirs.append((entry.name, entry.path, '<DIR>'))
            except OSError:
                continue
        files_with_date.sort(key=lambda x: x[0], reverse=True)
        for _, name, path, ext in files_with_date:
            results.append((name, path, ext))
        results.extend(dirs)
        return results

    def run(self):
        algorithm_map = {
            '广度优先': self.search_bfs,
            '深度优先': self.search_dfs,
            '文件优先': self.search_file_priority,
            '文件夹优先': self.search_dir_priority,
            '按扩展名分组': self.search_by_extension,
            '按大小排序': self.search_by_size,
            '按修改时间排序': self.search_by_date,
        }
        search_func = algorithm_map.get(self.algorithm, self.search_bfs)
        search_files = self.search_type in ('all', 'files')
        search_dirs = self.search_type in ('all', 'dirs')
        results = search_func(search_files, search_dirs)
        if not self.is_cancelled():
            self.finished_search.emit(self.epoch, results)


class ContentSearchWorker(CancellableWorker):
    def __init__(self, file_list: List[Tuple[str, str, str]], pattern: str,
                 case_sensitive: bool, exact_match: bool, use_regex: bool,
                 multiline: bool, epoch: int,
                 concurrent: bool = False, max_workers: int = 4):
        super().__init__(epoch)
        self.file_list = file_list
        self.pattern = pattern
        self.case_sensitive = case_sensitive
        self.exact_match = exact_match
        self.use_regex = use_regex
        self.multiline = multiline
        self.concurrent = concurrent
        self.max_workers = max_workers

    def match_content(self, content: str) -> bool:
        if self.exact_match:
            pattern = self.pattern if self.case_sensitive else self.pattern.lower()
            for line in content.splitlines():
                check = line.strip() if self.case_sensitive else line.strip().lower()
                if check == pattern:
                    return True
            return False
        elif self.use_regex:
            if not is_regex_safe(self.pattern):
                return False
            try:
                flags = 0 if self.case_sensitive else re.IGNORECASE
                if self.multiline:
                    flags |= re.DOTALL
                return bool(re.search(self.pattern, content, flags))
            except re.error:
                return False
        else:
            if self.case_sensitive:
                return self.pattern in content
            else:
                return self.pattern.lower() in content.lower()

    def _search_single_file(self, name: str, path: str, ext: str) -> Optional[Tuple[str, str, str]]:
        if self.is_cancelled():
            return None
        if ext == '<DIR>':
            return None
        if ext.lower() not in TEXT_EXTENSIONS:
            return None
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                if self.use_regex or self.multiline:
                    content = f.read()
                    if self.match_content(content):
                        return (name, path, ext)
                else:
                    for line in f:
                        if self.is_cancelled():
                            return None
                        if self.match_content(line):
                            return (name, path, ext)
            return None
        except (IOError, OSError):
            return None

    def run_serial(self):
        results = []
        total = len(self.file_list)
        for idx, (name, path, ext) in enumerate(self.file_list):
            if self.is_cancelled():
                return
            self.progress.emit(f"正在搜索: {idx+1}/{total}")
            res = self._search_single_file(name, path, ext)
            if res:
                results.append(res)
        if not self.is_cancelled():
            self.finished_search.emit(self.epoch, results)

    def run_concurrent(self):
        results_dict = {}
        total = len(self.file_list)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {
                executor.submit(self._search_single_file, name, path, ext): idx
                for idx, (name, path, ext) in enumerate(self.file_list)
            }
            completed = 0
            for future in as_completed(future_to_idx):
                if self.is_cancelled():
                    for f in future_to_idx:
                        f.cancel()
                    break
                idx = future_to_idx[future]
                completed += 1
                self.progress.emit(f"正在搜索: {completed}/{total}")
                try:
                    res = future.result()
                    if res:
                        results_dict[idx] = res
                except Exception:
                    pass
        results = [results_dict[i] for i in sorted(results_dict)]
        if not self.is_cancelled():
            self.finished_search.emit(self.epoch, results)

    def run(self):
        if self.concurrent and len(self.file_list) > 1:
            self.run_concurrent()
        else:
            self.run_serial()


class _SummaryBridge(QObject):
    finished = pyqtSignal(list)


class FilterWorker(CancellableWorker):
    filtered = pyqtSignal(list)

    def __init__(self, items: List[Tuple[str, str, str]], filter_text: str, use_regex: bool, scope: int):
        super().__init__(0)
        self.items = items
        self.filter_text = filter_text
        self.use_regex = use_regex
        self.scope = scope

    def run(self):
        if not self.filter_text:
            if not self.is_cancelled():
                self.filtered.emit(self.items)
            return
        filtered = []
        for item in self.items:
            if self.is_cancelled():
                break
            name, path, ext = item
            if self.scope == 0:
                text = f"{name}\n{path}\n{ext}"
            elif self.scope == 1:
                text = name
            elif self.scope == 2:
                text = path
            else:
                text = ext
            if self.use_regex:
                try:
                    if re.search(self.filter_text, text, re.IGNORECASE):
                        filtered.append(item)
                except re.error:
                    pass
            else:
                if self.filter_text.lower() in text.lower():
                    filtered.append(item)
        if not self.is_cancelled():
            self.filtered.emit(filtered)


class CustomTitleBar(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setObjectName("titleBar")
        self.setFixedHeight(32)
        self.setAttribute(Qt.WA_StyledBackground, True)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(0)

        left_strip = QWidget()
        left_strip.setFixedWidth(4)
        left_strip.setStyleSheet("background-color: #0078d4; border: none;")
        layout.addWidget(left_strip)

        self.icon_label = QLabel("📁")
        self.icon_label.setStyleSheet("font-size: 14px; padding-left: 8px; padding-right: 4px;")
        layout.addWidget(self.icon_label)

        self.title_label = QLabel("文件搜索工具")
        self.title_label.setStyleSheet("font-weight: bold; padding-left: 2px;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        self.min_btn = AnimatedTitleBarButton("—")
        self.min_btn.setObjectName("minButton")
        self.min_btn.setFixedSize(40, 28)
        self.min_btn.clicked.connect(self.main_window.showMinimized)
        layout.addWidget(self.min_btn)

        self.max_btn = AnimatedTitleBarButton("□")
        self.max_btn.setObjectName("maxButton")
        self.max_btn.setFixedSize(40, 28)
        self.max_btn.clicked.connect(self.toggle_maximize)
        layout.addWidget(self.max_btn)

        self.close_btn = AnimatedTitleBarButton("×")
        self.close_btn.setObjectName("closeButton")
        self.close_btn.setFixedSize(40, 28)
        self.close_btn.set_close_button(True)
        self.close_btn.clicked.connect(self.main_window.close)
        layout.addWidget(self.close_btn)

        self.setLayout(layout)
        self.drag_pos = None

    def toggle_maximize(self):
        if self.main_window.isMaximized():
            self.main_window.showNormal()
            self.max_btn.setText("□")
        else:
            self.main_window.showMaximized()
            self.max_btn.setText("❐")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()
        elif event.button() == Qt.RightButton:
            self.show_system_menu(event.globalPos())

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            if self.main_window.isMaximized():
                self.main_window.showNormal()
                self.max_btn.setText("□")
                self.main_window.move(event.globalPos() - QPoint(self.width() // 2, 16))
                self.drag_pos = event.globalPos()
            else:
                delta = event.globalPos() - self.drag_pos
                self.main_window.move(self.main_window.pos() + delta)
                self.drag_pos = event.globalPos()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.toggle_maximize()
        super().mouseDoubleClickEvent(event)

    def show_system_menu(self, global_pos):
        menu = QMenu(self)

        restore_action = QAction("还原(&R)", self)
        restore_action.setEnabled(self.main_window.isMaximized())
        restore_action.triggered.connect(self.main_window.showNormal)
        menu.addAction(restore_action)

        min_action = QAction("最小化(&N)", self)
        min_action.triggered.connect(self.main_window.showMinimized)
        menu.addAction(min_action)

        if self.main_window.isMaximized():
            max_action = QAction("还原(&X)", self)
        else:
            max_action = QAction("最大化(&X)", self)
        max_action.triggered.connect(self.toggle_maximize)
        menu.addAction(max_action)

        menu.addSeparator()

        close_action = QAction("关闭(&C)\tAlt+F4", self)
        close_action.triggered.connect(self.main_window.close)
        menu.addAction(close_action)

        menu.exec_(global_pos)


class FileSearchTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.file_results = []
        self.content_results = []
        self._display_items = []
        self._search_epoch = 0
        self._active_name_worker = None
        self._active_content_worker = None
        self._active_filter_worker = None
        self._results_mutex = QMutex()
        self.current_view = 'file'
        self.is_dark = is_system_dark_mode()
        self.settings = QSettings('FileSearchTool', 'FileSearchTool')
        self._preview_full = False
        self._preview_page = 0
        self._cached_file_lines = None
        self._cached_file_path = None
        self._cached_file_total_lines = 0
        self._filter_timer = QTimer()
        self._filter_timer.setSingleShot(True)
        self._filter_timer.timeout.connect(self._do_filter)
        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self.update_preview)
        self.init_ui()
        self._theme_transition = ThemeTransitionWidget(self)
        self._theme_transition.setGeometry(self.rect())
        self._theme_transition.hide()
        self.apply_theme()
        self.update_admin_button()
        self.restore_settings()

    def init_ui(self):
        self.setWindowTitle('文件搜索工具')
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(4)
        content_layout.setContentsMargins(4, 4, 4, 4)

        left_panel = QWidget()
        left_panel.setMinimumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(2, 2, 2, 2)
        left_layout.setSpacing(4)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(left_panel)
        scroll.setMinimumWidth(320)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        folder_group = QGroupBox('搜索目录')
        folder_layout = QVBoxLayout(folder_group)
        folder_row = QHBoxLayout()
        self.folder_edit = DropLineEdit()
        self.folder_edit.setPlaceholderText('拖拽文件夹到此处或点击选择...')
        folder_row.addWidget(self.folder_edit)
        self.folder_btn = QPushButton('选择')
        self.folder_btn.clicked.connect(self.select_folder)
        folder_row.addWidget(self.folder_btn)
        folder_layout.addLayout(folder_row)
        left_layout.addWidget(folder_group)

        name_group = QGroupBox('文件名搜索')
        name_layout = QVBoxLayout(name_group)
        name_layout.setSpacing(4)
        row1 = QHBoxLayout()
        row1.addWidget(QLabel('匹配:'))
        self.name_edit = ChineseLineEdit()
        self.name_edit.setPlaceholderText('*.txt 或正则')
        row1.addWidget(self.name_edit)
        name_layout.addLayout(row1)
        row2 = QHBoxLayout()
        self.case_sensitive_cb = QCheckBox('区分大小写')
        self.exact_match_cb = QCheckBox('绝对匹配')
        self.use_regex_cb = QCheckBox('正则')
        row2.addWidget(self.case_sensitive_cb)
        row2.addWidget(self.exact_match_cb)
        row2.addWidget(self.use_regex_cb)
        name_layout.addLayout(row2)
        row3 = QHBoxLayout()
        row3.addWidget(QLabel('算法:'))
        self.algorithm_combo = CustomComboBox()
        self.algorithm_combo.addItems([
            '广度优先', '深度优先', '文件优先', '文件夹优先',
            '按扩展名分组', '按大小排序', '按修改时间排序'
        ])
        row3.addWidget(self.algorithm_combo)
        name_layout.addLayout(row3)
        btn_row = QHBoxLayout()
        self.name_search_btn = AnimatedPushButton('搜文件')
        self.name_search_btn.clicked.connect(lambda: self.search_by_name('files'))
        btn_row.addWidget(self.name_search_btn)
        self.dir_search_btn = AnimatedPushButton('搜文件夹')
        self.dir_search_btn.clicked.connect(lambda: self.search_by_name('dirs'))
        btn_row.addWidget(self.dir_search_btn)
        self.all_search_btn = AnimatedPushButton('全部')
        self.all_search_btn.clicked.connect(lambda: self.search_by_name('all'))
        btn_row.addWidget(self.all_search_btn)
        name_layout.addLayout(btn_row)
        left_layout.addWidget(name_group)

        content_group = QGroupBox('内容搜索')
        content_group_layout = QVBoxLayout(content_group)
        content_group_layout.setSpacing(4)
        c_row1 = QHBoxLayout()
        c_row1.addWidget(QLabel('匹配:'))
        self.content_edit = ChineseLineEdit()
        self.content_edit.setPlaceholderText('搜索内容（支持正则）')
        c_row1.addWidget(self.content_edit)
        content_group_layout.addLayout(c_row1)
        c_row2 = QHBoxLayout()
        self.content_case_sensitive_cb = QCheckBox('区分大小写')
        self.content_exact_match_cb = QCheckBox('绝对匹配')
        self.content_use_regex_cb = QCheckBox('正则')
        self.content_multiline_cb = QCheckBox('多行')
        c_row2.addWidget(self.content_case_sensitive_cb)
        c_row2.addWidget(self.content_exact_match_cb)
        c_row2.addWidget(self.content_use_regex_cb)
        c_row2.addWidget(self.content_multiline_cb)
        content_group_layout.addLayout(c_row2)
        c_row3 = QHBoxLayout()
        c_row3.addWidget(QLabel('预览上下文:'))
        self.context_lines_spin = ChineseSpinBox()
        self.context_lines_spin.setRange(1, 50)
        self.context_lines_spin.setValue(5)
        c_row3.addWidget(self.context_lines_spin)
        c_row3.addStretch()
        content_group_layout.addLayout(c_row3)
        c_row4 = QHBoxLayout()
        self.concurrent_check = QCheckBox('启用并发搜索')
        self.concurrent_check.setToolTip('多线程加速内容搜索，适用于大量文件')
        c_row4.addWidget(self.concurrent_check)
        c_row4.addWidget(QLabel('线程数:'))
        self.workers_spin = ChineseSpinBox()
        self.workers_spin.setRange(1, 16)
        self.workers_spin.setValue(4)
        self.workers_spin.setEnabled(False)
        c_row4.addWidget(self.workers_spin)
        c_row4.addStretch()
        self.content_search_btn = AnimatedPushButton('搜索内容')
        self.content_search_btn.clicked.connect(self.search_by_content)
        c_row4.addWidget(self.content_search_btn)
        content_group_layout.addLayout(c_row4)
        self.concurrent_check.toggled.connect(self.workers_spin.setEnabled)
        left_layout.addWidget(content_group)

        other_group = QGroupBox('其他选项')
        other_layout = QVBoxLayout(other_group)
        other_layout.setSpacing(4)
        wl_row = QHBoxLayout()
        wl_row.addWidget(QLabel('白名单:'))
        self.whitelist_edit = ChineseLineEdit()
        self.whitelist_edit.setPlaceholderText('.txt,.py')
        wl_row.addWidget(self.whitelist_edit)
        self.enable_whitelist_cb = QCheckBox('启用')
        wl_row.addWidget(self.enable_whitelist_cb)
        other_layout.addLayout(wl_row)
        bl_row = QHBoxLayout()
        bl_row.addWidget(QLabel('黑名单:'))
        self.blacklist_edit = ChineseLineEdit()
        self.blacklist_edit.setPlaceholderText('.exe,.dll')
        bl_row.addWidget(self.blacklist_edit)
        self.enable_blacklist_cb = QCheckBox('启用')
        bl_row.addWidget(self.enable_blacklist_cb)
        other_layout.addLayout(bl_row)
        self.ignore_dirs_cb = QCheckBox('排除常见垃圾目录 (.git, node_modules 等)')
        self.ignore_dirs_cb.setChecked(True)
        other_layout.addWidget(self.ignore_dirs_cb)
        self.theme_btn = AnimatedPushButton('切换亮色/暗色主题')
        self.theme_btn.clicked.connect(self.toggle_theme)
        other_layout.addWidget(self.theme_btn)
        admin_row = QHBoxLayout()
        admin_row.addStretch()
        self.admin_restart_btn = AnimatedPushButton('以管理员身份重启')
        self.admin_restart_btn.clicked.connect(self.restart_as_admin)
        admin_row.addWidget(self.admin_restart_btn)
        other_layout.addLayout(admin_row)
        left_layout.addWidget(other_group)
        left_layout.addStretch()

        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(2, 2, 2, 2)
        center_layout.setSpacing(4)
        view_row = QHBoxLayout()
        self.file_view_btn = QRadioButton('文件名结果')
        self.file_view_btn.setChecked(True)
        self.file_view_btn.clicked.connect(lambda: self.switch_view('file'))
        view_row.addWidget(self.file_view_btn)
        self.content_view_btn = QRadioButton('内容结果')
        self.content_view_btn.clicked.connect(lambda: self.switch_view('content'))
        view_row.addWidget(self.content_view_btn)
        view_row.addStretch()
        view_row.addWidget(QLabel('过滤:'))
        self.filter_scope_combo = CustomComboBox()
        self.filter_scope_combo.addItems(['全部', '文件名', '路径', '后缀'])
        self.filter_scope_combo.setCurrentIndex(0)
        self.filter_scope_combo.currentIndexChanged.connect(self.apply_filter)
        view_row.addWidget(self.filter_scope_combo)
        self.filter_edit = ChineseLineEdit()
        self.filter_edit.setPlaceholderText('输入关键词实时过滤...')
        self.filter_edit.setFixedWidth(200)
        self.filter_edit.textChanged.connect(self.apply_filter)
        view_row.addWidget(self.filter_edit)
        self.filter_regex_cb = QCheckBox('正则')
        self.filter_regex_cb.stateChanged.connect(self.apply_filter)
        view_row.addWidget(self.filter_regex_cb)
        self.result_count_label = QLabel('')
        view_row.addWidget(self.result_count_label)
        center_layout.addLayout(view_row)
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setVisible(False)
        center_layout.addWidget(self.progress_bar)
        self.result_table = FadeTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(['文件名称', '文件路径', '文件类型'])
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.result_table.customContextMenuRequested.connect(self.show_context_menu)
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_table.setSortingEnabled(True)
        self.result_table.doubleClicked.connect(self.on_table_double_click)
        self.result_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        center_layout.addWidget(self.result_table)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(2, 2, 2, 2)
        right_layout.setSpacing(4)
        preview_header = QHBoxLayout()
        preview_header.setSpacing(6)
        preview_header.addWidget(QLabel('内容预览'))
        self.word_count_label = QLabel('0 字符')
        preview_header.addWidget(self.word_count_label)
        preview_header.addStretch()
        self.preview_full_btn = QPushButton('完整内容')
        self.preview_full_btn.setCheckable(True)
        self.preview_full_btn.clicked.connect(self._toggle_preview_full)
        preview_header.addWidget(self.preview_full_btn)
        self.preview_prev_btn = QPushButton('< 上一页')
        self.preview_prev_btn.clicked.connect(self._preview_prev_page)
        self.preview_prev_btn.setEnabled(False)
        preview_header.addWidget(self.preview_prev_btn)
        self.preview_page_label = QLabel('1/1')
        preview_header.addWidget(self.preview_page_label)
        self.preview_next_btn = QPushButton('下一页 >')
        self.preview_next_btn.clicked.connect(self._preview_next_page)
        self.preview_next_btn.setEnabled(False)
        preview_header.addWidget(self.preview_next_btn)
        self.preview_toggle_btn = QPushButton('隐藏预览')
        self.preview_toggle_btn.clicked.connect(self.toggle_preview)
        preview_header.addWidget(self.preview_toggle_btn)
        right_layout.addLayout(preview_header)
        self.preview_browser = PreviewTextBrowser()
        self.preview_browser.setOpenExternalLinks(False)
        self.preview_browser.setFont(QFont('Consolas', 10))
        self.preview_browser.setMinimumWidth(200)
        self.preview_browser.doubleClicked.connect(self.on_preview_double_click)
        right_layout.addWidget(self.preview_browser)

        scroll.setMinimumWidth(250)
        center_panel.setMinimumWidth(400)
        right_panel.setMinimumWidth(200)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(scroll)
        main_splitter.addWidget(center_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([320, 600, 480])
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)
        main_splitter.setStretchFactor(2, 1)
        main_splitter.setChildrenCollapsible(False)
        content_layout.addWidget(main_splitter)

        main_layout.addWidget(content_widget)
        self.status_bar = AnimatedStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪')

    def apply_theme(self):
        if self.is_dark:
            QApplication.instance().setStyleSheet(DARK_STYLE)
        else:
            QApplication.instance().setStyleSheet(LIGHT_STYLE)
        self.update_preview()

    def toggle_theme(self):
        self._theme_transition.setGeometry(self.rect())
        self._theme_transition.start_transition(self.is_dark, self._finish_theme_transition)

    def _finish_theme_transition(self):
        self.is_dark = not self.is_dark
        self.apply_theme()
        self._theme_transition.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_theme_transition'):
            self._theme_transition.setGeometry(self.rect())

    def toggle_preview(self):
        visible = self.preview_browser.isVisible()
        self.preview_browser.setVisible(not visible)
        self.preview_toggle_btn.setText('显示预览' if visible else '隐藏预览')

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if folder:
            self.folder_edit.setText(folder)

    def switch_view(self, view: str):
        self.current_view = view
        self.populate_table()

    def populate_table(self):
        self._results_mutex.lock()
        try:
            results = self.file_results if self.current_view == 'file' else self.content_results
            results_copy = list(results)
        finally:
            self._results_mutex.unlock()
        self._display_items = results_copy
        self._fill_table(results_copy)
        self._update_result_count(len(results_copy), len(results_copy))
        self.update_preview()

    def _fill_table(self, items: List[Tuple[str, str, str]]):
        was_sorting = self.result_table.isSortingEnabled()
        self.result_table.setUpdatesEnabled(False)
        self.result_table.setSortingEnabled(False)
        self.result_table.blockSignals(True)
        self.result_table.setRowCount(0)
        self.result_table.setRowCount(len(items))
        for row, (name, path, ext) in enumerate(items):
            self.result_table.setItem(row, 0, QTableWidgetItem(name))
            self.result_table.setItem(row, 1, QTableWidgetItem(path))
            self.result_table.setItem(row, 2, QTableWidgetItem(ext))
        self.result_table.blockSignals(False)
        self.result_table.setUpdatesEnabled(True)
        if was_sorting:
            self.result_table.setSortingEnabled(True)

    def apply_filter(self):
        self._filter_timer.start(200)

    def _do_filter(self):
        self._results_mutex.lock()
        try:
            results = self.file_results if self.current_view == 'file' else self.content_results
            results_copy = list(results)
        finally:
            self._results_mutex.unlock()

        filter_text = self.filter_edit.text()
        use_regex = self.filter_regex_cb.isChecked()
        scope = self.filter_scope_combo.currentIndex()

        if self._active_filter_worker and self._active_filter_worker.isRunning():
            self._active_filter_worker.cancel()
            try:
                self._active_filter_worker.filtered.disconnect()
            except TypeError:
                pass
            self._active_filter_worker.quit()
            self._active_filter_worker.wait(2000)
            self._active_filter_worker = None

        self._active_filter_worker = FilterWorker(results_copy, filter_text, use_regex, scope)
        self._active_filter_worker.filtered.connect(self._on_filter_finished)
        self._active_filter_worker.start()

    def _on_filter_finished(self, filtered_items):
        self._display_items = filtered_items
        self._fill_table(filtered_items)
        self._results_mutex.lock()
        try:
            total = len(self.file_results if self.current_view == 'file' else self.content_results)
        finally:
            self._results_mutex.unlock()
        self._update_result_count(len(filtered_items), total)

    def _update_result_count(self, shown: int, total: int):
        if shown == total:
            self.result_count_label.setText(f'{total} 项')
        else:
            self.result_count_label.setText(f'{shown}/{total} 项')

    def _cleanup_worker(self, worker):
        if worker is None:
            return
        try:
            worker.finished_search.disconnect()
        except TypeError:
            pass
        try:
            worker.progress.disconnect()
        except TypeError:
            pass
        if worker.isRunning():
            worker.cancel()
            worker.wait(2000)

    def search_by_name(self, search_type: str):
        folder = self.folder_edit.text()
        if not folder:
            QMessageBox.warning(self, '警告', '请先选择要搜索的文件夹！')
            return
        if not os.path.exists(folder):
            QMessageBox.warning(self, '警告', '选择的文件夹不存在！')
            return

        self.result_table.setSortingEnabled(False)
        self.result_table.setRowCount(0)
        self.result_count_label.setText('')
        QApplication.processEvents()

        self._search_epoch += 1
        current_epoch = self._search_epoch

        self._cleanup_worker(self._active_name_worker)
        self._cleanup_worker(self._active_content_worker)
        self._active_name_worker = None
        self._active_content_worker = None

        self._results_mutex.lock()
        try:
            self.file_results = []
            self.content_results = []
        finally:
            self._results_mutex.unlock()

        self.current_view = 'file'
        self.file_view_btn.setChecked(True)

        pattern = self.name_edit.text()
        case_sensitive = self.case_sensitive_cb.isChecked()
        exact_match = self.exact_match_cb.isChecked()
        use_regex = self.use_regex_cb.isChecked()
        algorithm = self.algorithm_combo.currentText()
        enable_whitelist = self.enable_whitelist_cb.isChecked()
        whitelist = parse_extension_list(self.whitelist_edit.text()) if enable_whitelist else []
        enable_blacklist = self.enable_blacklist_cb.isChecked()
        blacklist = parse_extension_list(self.blacklist_edit.text()) if enable_blacklist else []
        ignore_common = self.ignore_dirs_cb.isChecked()

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self._set_search_buttons_enabled(False)

        self._active_name_worker = SearchWorker(
            folder, pattern, case_sensitive, exact_match, use_regex,
            algorithm, search_type, enable_whitelist, whitelist,
            enable_blacklist, blacklist, ignore_common,
            epoch=current_epoch
        )
        self._active_name_worker.finished_search.connect(self.on_name_search_finished)
        self._active_name_worker.start()
        self.status_bar.showMessage('正在搜索文件...')

    def on_name_search_finished(self, epoch: int, results: list):
        if epoch != self._search_epoch:
            return
        self._results_mutex.lock()
        try:
            self.file_results = results
        finally:
            self._results_mutex.unlock()
        self.progress_bar.setVisible(False)
        self._set_search_buttons_enabled(True)
        self.populate_table()
        self.status_bar.showMessage(f'文件名搜索完成，共找到 {len(results)} 个结果')
        self.status_bar.flash_success()
        self.save_settings()

    def search_by_content(self):
        self._results_mutex.lock()
        try:
            if not self.file_results:
                has_results = False
                file_list_copy = []
            else:
                has_results = True
                file_list_copy = list(self.file_results)
        finally:
            self._results_mutex.unlock()
        if not has_results:
            QMessageBox.warning(self, '警告', '请先进行文件名搜索！')
            return

        pattern = self.content_edit.text()
        if not pattern:
            QMessageBox.warning(self, '警告', '请输入要搜索的内容！')
            return

        self.result_table.setSortingEnabled(False)
        self.result_table.setRowCount(0)
        self.result_count_label.setText('')
        QApplication.processEvents()

        self._search_epoch += 1
        current_epoch = self._search_epoch

        self._cleanup_worker(self._active_content_worker)
        self._active_content_worker = None

        self._results_mutex.lock()
        try:
            self.content_results = []
        finally:
            self._results_mutex.unlock()
        self.current_view = 'content'
        self.content_view_btn.setChecked(True)

        case_sensitive = self.content_case_sensitive_cb.isChecked()
        exact_match = self.content_exact_match_cb.isChecked()
        use_regex = self.content_use_regex_cb.isChecked()
        multiline = self.content_multiline_cb.isChecked()
        concurrent = self.concurrent_check.isChecked()
        max_workers = self.workers_spin.value() if concurrent else 1

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self._set_search_buttons_enabled(False)
        self.content_search_btn.setEnabled(False)

        self._active_content_worker = ContentSearchWorker(
            file_list_copy, pattern, case_sensitive, exact_match,
            use_regex, multiline,
            epoch=current_epoch,
            concurrent=concurrent,
            max_workers=max_workers
        )
        self._active_content_worker.progress.connect(lambda msg: self.status_bar.showMessage(msg))
        self._active_content_worker.finished_search.connect(self.on_content_search_finished)
        self._active_content_worker.start()
        self.status_bar.showMessage('正在搜索内容...')

    def on_content_search_finished(self, epoch: int, results: list):
        if epoch != self._search_epoch:
            return
        self._results_mutex.lock()
        try:
            self.content_results = results
        finally:
            self._results_mutex.unlock()
        self.progress_bar.setVisible(False)
        self._set_search_buttons_enabled(True)
        self.content_search_btn.setEnabled(True)
        self.populate_table()
        self.status_bar.showMessage(f'内容搜索完成，共找到 {len(results)} 个结果')
        self.status_bar.flash_success()
        self.save_settings()

    def _set_search_buttons_enabled(self, enabled: bool):
        self.name_search_btn.setEnabled(enabled)
        self.dir_search_btn.setEnabled(enabled)
        self.all_search_btn.setEnabled(enabled)

    def get_selected_items(self) -> List[Tuple[str, str, str]]:
        selected = []
        for row in self.result_table.selectionModel().selectedRows():
            name = self.result_table.item(row.row(), 0).text()
            path = self.result_table.item(row.row(), 1).text()
            ext = self.result_table.item(row.row(), 2).text()
            selected.append((name, path, ext))
        return selected

    def on_table_double_click(self):
        items = self.get_selected_items()
        if items:
            self.open_file(items)

    def on_selection_changed(self):
        self._preview_timer.start(150)

    def on_preview_double_click(self):
        cursor = self.preview_browser.textCursor()
        selected_text = cursor.selectedText().strip()
        if selected_text:
            self.content_edit.setText(selected_text)

    def show_context_menu(self, pos):
        selected_items = self.get_selected_items()
        if not selected_items:
            return
        menu = QMenu(self)
        open_action = menu.addAction('打开')
        open_folder_action = menu.addAction('用资源管理器打开所在文件夹')
        menu.addSeparator()
        copy_action = menu.addAction('复制文件')
        copy_path_action = menu.addAction('复制完整路径')
        copy_summary_action = menu.addAction('复制匹配摘要')
        menu.addSeparator()
        rename_action = menu.addAction('重命名')
        delete_action = menu.addAction('删除到回收站')
        shift_delete_action = menu.addAction('彻底删除 (Shift+Delete)')
        menu.addSeparator()
        properties_action = menu.addAction('打开属性')
        menu.addSeparator()
        sort_az_action = menu.addAction('排序: 名称 A-Z')
        sort_za_action = menu.addAction('排序: 名称 Z-A')
        menu.addSeparator()
        refresh_action = menu.addAction('刷新')
        action = menu.exec_(self.result_table.mapToGlobal(pos))
        if action == open_action:
            self.open_file(selected_items)
        elif action == open_folder_action:
            self.open_in_explorer(selected_items)
        elif action == copy_action:
            self.copy_files(selected_items)
        elif action == copy_path_action:
            self.copy_path_to_clipboard(selected_items)
        elif action == copy_summary_action:
            self.copy_match_summary(selected_items)
        elif action == rename_action:
            self.rename_files(selected_items)
        elif action == delete_action:
            self.delete_files(selected_items, False)
        elif action == shift_delete_action:
            self.delete_files(selected_items, True)
        elif action == properties_action:
            self.show_properties(selected_items)
        elif action == sort_az_action:
            self.sort_table(reverse=False)
        elif action == sort_za_action:
            self.sort_table(reverse=True)
        elif action == refresh_action:
            self.refresh_table()

    def open_file(self, items: List[Tuple[str, str, str]]):
        for name, path, ext in items:
            try:
                os.startfile(path)
            except Exception as e:
                QMessageBox.warning(self, '错误', f'无法打开: {e}')

    def open_in_explorer(self, items: List[Tuple[str, str, str]]):
        for name, path, ext in items:
            try:
                abs_path = os.path.abspath(path)
                if not os.path.exists(abs_path):
                    QMessageBox.warning(self, '错误', f'路径不存在: {abs_path}')
                    continue
                if ext == '<DIR>':
                    subprocess.run(['explorer', abs_path])
                else:
                    subprocess.run(['explorer', '/select,', abs_path])
            except Exception as e:
                QMessageBox.warning(self, '错误', f'无法打开资源管理器: {e}')

    def copy_files(self, items: List[Tuple[str, str, str]]):
        if len(items) > 1:
            QMessageBox.information(self, '提示', '一次只能复制一个文件/文件夹')
            return
        name, path, ext = items[0]
        dest = QFileDialog.getExistingDirectory(self, '选择目标文件夹')
        if dest:
            try:
                if ext == '<DIR>':
                    shutil.copytree(path, os.path.join(dest, name))
                else:
                    shutil.copy2(path, dest)
                QMessageBox.information(self, '成功', '复制成功！')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'复制失败: {e}')

    def copy_path_to_clipboard(self, items: List[Tuple[str, str, str]]):
        paths = [path for _, path, _ in items]
        QApplication.clipboard().setText('\n'.join(paths))
        self.status_bar.showMessage(f'已复制 {len(paths)} 个路径到剪贴板')

    def copy_match_summary(self, items: List[Tuple[str, str, str]]):
        search_pattern = self.content_edit.text()
        if not search_pattern:
            self.copy_path_to_clipboard(items)
            return
        case_sensitive = self.content_case_sensitive_cb.isChecked()
        use_regex = self.content_use_regex_cb.isChecked()
        exact_match = self.content_exact_match_cb.isChecked()
        self.status_bar.showMessage('正在生成匹配摘要...')

        def _worker():
            lines = []
            for name, path, ext in items:
                if ext == '<DIR>':
                    continue
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f):
                            if self._line_matches(line, search_pattern, case_sensitive, exact_match, use_regex):
                                lines.append(f'{path}:{i + 1}: {line.rstrip()}')
                except (IOError, OSError):
                    pass
            return lines

        bridge = _SummaryBridge()
        bridge.finished.connect(self._apply_summary_result)

        def _run(bridge=bridge):
            result = _worker()
            bridge.finished.emit(result)

        import threading
        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def _apply_summary_result(self, result):
        if result:
            QApplication.clipboard().setText('\n'.join(result))
            self.status_bar.showMessage(f'已复制 {len(result)} 条匹配摘要到剪贴板')
        else:
            self.status_bar.showMessage('未找到匹配内容')

    def rename_files(self, items: List[Tuple[str, str, str]]):
        if len(items) > 1:
            QMessageBox.information(self, '提示', '一次只能重命名一个文件/文件夹')
            return
        name, path, ext = items[0]
        parent = os.path.dirname(path)
        new_name, ok = QInputDialog.getText(self, '重命名', '请输入新名称:', text=name)
        if ok and new_name:
            new_path = os.path.join(parent, new_name)
            try:
                os.rename(path, new_path)
                self._results_mutex.lock()
                try:
                    results = self.file_results if self.current_view == 'file' else self.content_results
                    for i, (n, p, e) in enumerate(results):
                        if p == path:
                            results[i] = (new_name, new_path, e)
                            break
                finally:
                    self._results_mutex.unlock()
                for row in range(self.result_table.rowCount()):
                    if self.result_table.item(row, 1).text() == path:
                        self.result_table.item(row, 0).setText(new_name)
                        self.result_table.item(row, 1).setText(new_path)
                        break
                for i, (n, p, e) in enumerate(self._display_items):
                    if p == path:
                        self._display_items[i] = (new_name, new_path, e)
                        break
                QMessageBox.information(self, '成功', '重命名成功！')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'重命名失败: {e}')

    def delete_files(self, items: List[Tuple[str, str, str]], permanent: bool):
        if not items:
            return
        msg = '确定要彻底删除选中的项目吗？此操作不可恢复！' if permanent else '确定要将选中的项目移动到回收站吗？'
        reply = QMessageBox.question(self, '确认删除', msg,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            deleted_paths = []
            for name, path, ext in items:
                try:
                    if permanent:
                        if ext == '<DIR>':
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                    else:
                        self.move_to_recycle_bin(path)
                    deleted_paths.append(path)
                except Exception as e:
                    QMessageBox.warning(self, '错误', f'删除 {name} 失败: {e}')
            if deleted_paths:
                self._results_mutex.lock()
                try:
                    results = self.file_results if self.current_view == 'file' else self.content_results
                    updated = [(n, p, e) for n, p, e in results if p not in deleted_paths]
                    if self.current_view == 'file':
                        self.file_results = updated
                    else:
                        self.content_results = updated
                finally:
                    self._results_mutex.unlock()
                self.populate_table()
                QMessageBox.information(self, '成功', f'成功删除 {len(deleted_paths)} 个项目。')

    def move_to_recycle_bin(self, path: str):
        if SEND2TRASH_AVAILABLE:
            send2trash.send2trash(path)
        else:
            raise OSError('send2trash 库未安装，无法移动到回收站。请运行 pip install send2trash 安装后重试。')

    def show_properties(self, items: List[Tuple[str, str, str]]):
        for name, path, ext in items:
            dialog = FilePropertiesDialog(name, path, ext, self)
            dialog.exec_()

    def sort_table(self, reverse: bool):
        if not self._display_items:
            return
        sorted_items = sorted(self._display_items, key=lambda x: x[0].lower(), reverse=reverse)
        self._display_items = sorted_items
        self._fill_table(sorted_items)

    def refresh_table(self):
        self._results_mutex.lock()
        try:
            results = self.file_results if self.current_view == 'file' else self.content_results
            valid_results = [(n, p, e) for n, p, e in results if os.path.exists(p)]
            if self.current_view == 'file':
                self.file_results = valid_results
            else:
                self.content_results = valid_results
        finally:
            self._results_mutex.unlock()
        self.populate_table()
        self.status_bar.showMessage(f'已刷新，当前有效项目: {len(valid_results)} 个')

    def _toggle_preview_full(self):
        self._preview_full = self.preview_full_btn.isChecked()
        self._preview_page = 0
        self.update_preview()

    def _preview_prev_page(self):
        if self._preview_page > 0:
            self._preview_page -= 1
            self._render_preview_page()

    def _preview_next_page(self):
        self._preview_page += 1
        self._render_preview_page()

    def _render_preview_page(self):
        if self._cached_file_lines is None:
            return
        lines = self._cached_file_lines
        total = len(lines)
        lines_per_page = PREVIEW_LINES_PER_PAGE
        total_pages = (total + lines_per_page - 1) // lines_per_page
        self._preview_page = min(self._preview_page, total_pages - 1)
        start = self._preview_page * lines_per_page
        end = min(start + lines_per_page, total)
        bg = '#1e1e1e' if self.is_dark else '#ffffff'
        fg = '#d4d4d4' if self.is_dark else '#1e1e1e'
        num_fg = '#858585' if self.is_dark else '#999'
        info_fg = '#569cd6' if self.is_dark else '#0066cc'
        info2_fg = '#608b4e' if self.is_dark else '#666'
        name = os.path.basename(self._cached_file_path) if self._cached_file_path else ''
        html_parts = []
        html_parts.append(
            f'<div style="font-family:Consolas,monospace; font-size:10pt; '
            f'background:{bg}; color:{fg}; padding:8px;">'
        )
        page_info = f'{total} 行' if total_pages == 1 else f'{total} 行，第 {start+1}-{end} 行'
        html_parts.append(
            f'<div style="color:{info_fg}; margin-bottom:8px;">{name} '
            f'<span style="color:{info2_fg};">({page_info})</span></div>'
        )
        for i in range(start, end):
            line_num = i + 1
            line_content = lines[i].rstrip('\n\r')
            escaped = (line_content
                       .replace('&', '&amp;')
                       .replace('<', '&lt;')
                       .replace('>', '&gt;'))
            html_parts.append(
                f'<div style="background:{bg}; padding:1px 4px; white-space:pre;">'
                f'<span style="color:{num_fg}; display:inline-block; width:50px; '
                f'text-align:right; margin-right:16px; user-select:none;">{line_num}</span>'
                f'<span>{escaped}</span></div>'
            )
        html_parts.append('</div>')
        html_content = ''.join(html_parts)
        self.preview_browser.setHtml(html_content)
        self.preview_prev_btn.setEnabled(self._preview_page > 0)
        self.preview_next_btn.setEnabled(self._preview_page < total_pages - 1)
        self.preview_page_label.setText(f'{self._preview_page + 1}/{total_pages}')
        total_chars = sum(len(line) for line in lines)
        self.word_count_label.setText(f'{total_chars} 字符')

    def _count_file_lines(self, path: str) -> int:
        try:
            count = 0
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for _ in f:
                    count += 1
            return count
        except Exception:
            return 0

    def _load_large_file_chunk(self, start_line: int, num_lines: int) -> list:
        if not self._cached_file_path:
            return []
        try:
            lines = []
            for i in range(start_line, start_line + num_lines):
                line = linecache.getline(self._cached_file_path, i + 1)
                if not line:
                    break
                lines.append(line)
            return lines
        except Exception:
            return []

    def update_preview(self):
        selected_items = self.get_selected_items()
        if not selected_items:
            self._cached_file_lines = None
            self._cached_file_path = None
            self._cached_file_total_lines = 0
            self._set_preview_placeholder('请选中一个文件以查看内容详情')
            self._update_preview_nav_buttons(False)
            return
        name, path, ext = selected_items[0]
        if ext == '<DIR>':
            self._cached_file_lines = None
            self._cached_file_path = None
            self._cached_file_total_lines = 0
            self._set_preview_placeholder(f'"{name}" 是文件夹，无法预览内容')
            self._update_preview_nav_buttons(False)
            return
        try:
            file_size = os.path.getsize(path)
            if file_size > MAX_PREVIEW_SIZE:
                self._cached_file_lines = None
                self._cached_file_path = path
                self._cached_file_total_lines = self._count_file_lines(path)
                self._set_preview_placeholder(
                    f'文件过大 ({file_size // 1024 // 1024} MB)，共 {self._cached_file_total_lines} 行\n'
                    f'点击"加载更多"或"加载完整文件"按钮进行预览'
                )
                self._update_preview_nav_buttons(False)
                return
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except (IOError, OSError) as e:
            self._cached_file_lines = None
            self._cached_file_path = None
            self._cached_file_total_lines = 0
            self._set_preview_placeholder(f'无法读取文件: {e}')
            self._update_preview_nav_buttons(False)
            return
        if not lines:
            self._cached_file_lines = None
            self._cached_file_path = None
            self._cached_file_total_lines = 0
            self._set_preview_placeholder('空文件')
            self._update_preview_nav_buttons(False)
            return
        self._cached_file_lines = lines
        self._cached_file_path = path
        self._cached_file_total_lines = len(lines)
        search_pattern = self.content_edit.text() if self.current_view == 'content' else self.name_edit.text()
        if self._preview_full:
            total_pages = (len(lines) + PREVIEW_LINES_PER_PAGE - 1) // PREVIEW_LINES_PER_PAGE
            self._update_preview_nav_buttons(total_pages > 1)
            self._render_preview_page()
            return
        self._update_preview_nav_buttons(False)
        match_line_indices = set()
        if search_pattern:
            case_sensitive = (self.content_case_sensitive_cb.isChecked()
                              if self.current_view == 'content'
                              else self.case_sensitive_cb.isChecked())
            use_regex = (self.content_use_regex_cb.isChecked()
                         if self.current_view == 'content'
                         else self.use_regex_cb.isChecked())
            exact_match = (self.content_exact_match_cb.isChecked()
                           if self.current_view == 'content'
                           else self.exact_match_cb.isChecked())
            for i, line in enumerate(lines):
                if self._line_matches(line, search_pattern, case_sensitive, exact_match, use_regex):
                    match_line_indices.add(i)
        context_range = self.context_lines_spin.value()
        if match_line_indices:
            display_indices = set()
            for idx in match_line_indices:
                for offset in range(-context_range, context_range + 1):
                    line_idx = idx + offset
                    if 0 <= line_idx < len(lines):
                        display_indices.add(line_idx)
            display_indices = sorted(display_indices)
        else:
            display_indices = list(range(min(50, len(lines))))
        bg = '#1e1e1e' if self.is_dark else '#ffffff'
        fg = '#d4d4d4' if self.is_dark else '#1e1e1e'
        num_fg = '#858585' if self.is_dark else '#999'
        match_bg = '#2d2d0f' if self.is_dark else '#fffacd'
        match_num = '#dcdcaa' if self.is_dark else '#b8860b'
        sep_fg = '#608b4e' if self.is_dark else '#999'
        info_fg = '#569cd6' if self.is_dark else '#0066cc'
        info2_fg = '#608b4e' if self.is_dark else '#666'
        html_parts = []
        html_parts.append(
            f'<div style="font-family:Consolas,monospace; font-size:10pt; '
            f'background:{bg}; color:{fg}; padding:8px;">'
        )
        html_parts.append(
            f'<div style="color:{info_fg}; margin-bottom:8px;">{name} '
            f'<span style="color:{info2_fg};">({len(lines)} 行'
            f'{f"，匹配 {len(match_line_indices)} 处" if match_line_indices else ""})</span></div>'
        )
        prev_idx = -1
        for idx in display_indices:
            if prev_idx >= 0 and idx > prev_idx + 1:
                html_parts.append(
                    f'<div style="color:{sep_fg}; padding:2px 0; text-align:center;">···</div>'
                )
            prev_idx = idx
            line_num = idx + 1
            line_content = lines[idx].rstrip('\n\r')
            if search_pattern and idx in match_line_indices:
                case_sensitive = (self.content_case_sensitive_cb.isChecked()
                                  if self.current_view == 'content'
                                  else self.case_sensitive_cb.isChecked())
                use_regex = (self.content_use_regex_cb.isChecked()
                             if self.current_view == 'content'
                             else self.use_regex_cb.isChecked())
                exact_match = (self.content_exact_match_cb.isChecked()
                               if self.current_view == 'content'
                               else self.exact_match_cb.isChecked())
                highlighted = self._highlight_and_escape(line_content, search_pattern, case_sensitive, use_regex, exact_match)
                line_bg = match_bg
                num_color = match_num
            else:
                highlighted = (line_content
                               .replace('&', '&amp;')
                               .replace('<', '&lt;')
                               .replace('>', '&gt;'))
                line_bg = bg
                num_color = num_fg
            html_parts.append(
                f'<div style="background:{line_bg}; padding:1px 4px; white-space:pre;">'
                f'<span style="color:{num_color}; display:inline-block; width:50px; '
                f'text-align:right; margin-right:16px; user-select:none;">{line_num}</span>'
                f'<span>{highlighted}</span></div>'
            )
        html_parts.append('</div>')
        html_content = ''.join(html_parts)
        self.preview_browser.setHtml(html_content)
        total_chars = sum(len(lines[idx]) for idx in display_indices)
        self.word_count_label.setText(f'{total_chars} 字符')

    def _update_preview_nav_buttons(self, has_multiple_pages: bool):
        if has_multiple_pages:
            self.preview_prev_btn.setEnabled(self._preview_page > 0)
            self.preview_next_btn.setEnabled(True)
            self.preview_page_label.setText(f'{self._preview_page + 1}/?')
        else:
            self.preview_prev_btn.setEnabled(False)
            self.preview_next_btn.setEnabled(False)
            self.preview_page_label.setText('1/1')

    def _set_preview_placeholder(self, text: str):
        bg = '#1e1e1e' if self.is_dark else '#ffffff'
        fg = '#888' if self.is_dark else '#999'
        self.preview_browser.setHtml(
            f'<div style="font-family:Consolas,monospace; background:{bg}; color:{fg}; '
            f'padding:20px; text-align:center;">{text}</div>'
        )
        self.word_count_label.setText('0 字符')

    def _line_matches(self, line: str, pattern: str, case_sensitive: bool,
                      exact_match: bool, use_regex: bool) -> bool:
        if exact_match:
            if case_sensitive:
                return line.strip() == pattern
            else:
                return line.strip().lower() == pattern.lower()
        elif use_regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                return bool(re.search(pattern, line, flags))
            except re.error:
                return False
        else:
            if case_sensitive:
                return pattern in line
            else:
                return pattern.lower() in line.lower()

    def _highlight_and_escape(self, raw_text: str, pattern: str, case_sensitive: bool,
                              use_regex: bool, exact_match: bool) -> str:
        hl_open = '<span style="background:#f0e68c; color:#000; font-weight:bold;">'
        hl_close = '</span>'

        def html_escape(s):
            return (s.replace('&', '&amp;')
                     .replace('<', '&lt;')
                     .replace('>', '&gt;'))

        matches = []
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            if exact_match:
                search_pat = re.escape(pattern)
            elif use_regex:
                if not is_regex_safe(pattern):
                    return html_escape(raw_text)
                search_pat = pattern
            else:
                search_pat = re.escape(pattern)
            for m in re.finditer(search_pat, raw_text, flags):
                matches.append((m.start(), m.end()))
        except re.error:
            matches = []

        if not matches:
            return html_escape(raw_text)

        result = []
        last_end = 0
        for start, end in matches:
            result.append(html_escape(raw_text[last_end:start]))
            result.append(hl_open)
            result.append(html_escape(raw_text[start:end]))
            result.append(hl_close)
            last_end = end
        result.append(html_escape(raw_text[last_end:]))
        return ''.join(result)

    def is_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except AttributeError:
            return False

    def update_admin_button(self):
        if self.is_admin():
            self.admin_restart_btn.setText('当前已是管理员')
            self.admin_restart_btn.setEnabled(False)
        else:
            self.admin_restart_btn.setText('以管理员身份重启')
            self.admin_restart_btn.setEnabled(True)

    def restart_as_admin(self):
        if self.is_admin():
            QMessageBox.information(self, '提示', '当前已经是管理员权限运行。')
            return
        try:
            script = os.path.abspath(sys.argv[0])
            params = subprocess.list2cmdline([script] + sys.argv[1:])
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, None, 1
            )
            QApplication.quit()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'提权失败: {e}')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            had_running = ((self._active_name_worker and self._active_name_worker.isRunning()) or
                           (self._active_content_worker and self._active_content_worker.isRunning()))
            self._cleanup_worker(self._active_name_worker)
            self._cleanup_worker(self._active_content_worker)
            self._active_name_worker = None
            self._active_content_worker = None
            if had_running:
                self.progress_bar.setVisible(False)
                self._set_search_buttons_enabled(True)
                self.content_search_btn.setEnabled(True)
                self.status_bar.showMessage('搜索已中止')
        super().keyPressEvent(event)

    def save_settings(self):
        s = self.settings
        s.setValue('folder', self.folder_edit.text())
        s.setValue('name_pattern', self.name_edit.text())
        s.setValue('case_sensitive', self.case_sensitive_cb.isChecked())
        s.setValue('exact_match', self.exact_match_cb.isChecked())
        s.setValue('use_regex', self.use_regex_cb.isChecked())
        s.setValue('algorithm', self.algorithm_combo.currentText())
        s.setValue('content_pattern', self.content_edit.text())
        s.setValue('content_case_sensitive', self.content_case_sensitive_cb.isChecked())
        s.setValue('content_exact_match', self.content_exact_match_cb.isChecked())
        s.setValue('content_use_regex', self.content_use_regex_cb.isChecked())
        s.setValue('content_multiline', self.content_multiline_cb.isChecked())
        s.setValue('context_lines', self.context_lines_spin.value())
        s.setValue('whitelist', self.whitelist_edit.text())
        s.setValue('enable_whitelist', self.enable_whitelist_cb.isChecked())
        s.setValue('blacklist', self.blacklist_edit.text())
        s.setValue('enable_blacklist', self.enable_blacklist_cb.isChecked())
        s.setValue('ignore_dirs', self.ignore_dirs_cb.isChecked())
        s.setValue('is_dark', self.is_dark)
        s.setValue('concurrent_content', self.concurrent_check.isChecked())
        s.setValue('max_workers', self.workers_spin.value())
        s.setValue('filter_scope', self.filter_scope_combo.currentIndex())

    def restore_settings(self):
        s = self.settings
        folder = s.value('folder', '')
        if folder and os.path.exists(folder):
            self.folder_edit.setText(folder)
        self.name_edit.setText(s.value('name_pattern', ''))
        self.case_sensitive_cb.setChecked(s.value('case_sensitive', False, type=bool))
        self.exact_match_cb.setChecked(s.value('exact_match', False, type=bool))
        self.use_regex_cb.setChecked(s.value('use_regex', False, type=bool))
        idx = self.algorithm_combo.findText(s.value('algorithm', '广度优先'))
        if idx >= 0:
            self.algorithm_combo.setCurrentIndex(idx)
        self.content_edit.setText(s.value('content_pattern', ''))
        self.content_case_sensitive_cb.setChecked(s.value('content_case_sensitive', False, type=bool))
        self.content_exact_match_cb.setChecked(s.value('content_exact_match', False, type=bool))
        self.content_use_regex_cb.setChecked(s.value('content_use_regex', False, type=bool))
        self.content_multiline_cb.setChecked(s.value('content_multiline', False, type=bool))
        self.context_lines_spin.setValue(s.value('context_lines', 5, type=int))
        self.whitelist_edit.setText(s.value('whitelist', ''))
        self.enable_whitelist_cb.setChecked(s.value('enable_whitelist', False, type=bool))
        self.blacklist_edit.setText(s.value('blacklist', ''))
        self.enable_blacklist_cb.setChecked(s.value('enable_blacklist', False, type=bool))
        self.ignore_dirs_cb.setChecked(s.value('ignore_dirs', True, type=bool))
        saved_dark = s.value('is_dark', is_system_dark_mode(), type=bool)
        if saved_dark != self.is_dark:
            self.is_dark = saved_dark
            self.apply_theme()
        self.concurrent_check.setChecked(s.value('concurrent_content', False, type=bool))
        self.workers_spin.setValue(s.value('max_workers', 4, type=int))
        self.workers_spin.setEnabled(self.concurrent_check.isChecked())
        filter_scope = s.value('filter_scope', 0, type=int)
        self.filter_scope_combo.setCurrentIndex(filter_scope)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.title_bar.max_btn.setText("□")
        else:
            self.showMaximized()
            self.title_bar.max_btn.setText("❐")

    def nativeEvent(self, eventType, message):
        if sys.platform != 'win32':
            return super().nativeEvent(eventType, message)
        
        msg = ctypes.wintypes.MSG.from_address(message.__int__())
        
        if msg.message == 0x00A3:
            if msg.wParam == 2:
                self.toggle_maximize()
                return True, 0
        
        if msg.message == 0x00A5:
            if msg.wParam == 2:
                x = ctypes.c_short(msg.lParam & 0xFFFF).value
                y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
                self.title_bar.show_system_menu(QPoint(x, y))
                return True, 0
        
        if msg.message == 0x0084:
            if self.isMaximized():
                return False, 0
            
            x = ctypes.c_short(msg.lParam & 0xFFFF).value
            y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
            pt = QPoint(x, y)
            pos = self.mapFromGlobal(pt)
            width = self.width()
            height = self.height()
            
            border = 8
            left = pos.x() < border
            right = pos.x() > width - border
            top = pos.y() < border
            bottom = pos.y() > height - border
            
            if top and left:
                return True, 13
            elif top and right:
                return True, 14
            elif bottom and left:
                return True, 16
            elif bottom and right:
                return True, 17
            elif left:
                return True, 10
            elif right:
                return True, 11
            elif top:
                return True, 12
            elif bottom:
                return True, 15
            
            title_bar_height = self.title_bar.height()
            if pos.y() < title_bar_height:
                child = self.childAt(pos)
                if child is None or not isinstance(child, QPushButton):
                    return True, 2
        
        return super().nativeEvent(eventType, message)

    def closeEvent(self, event):
        self.save_settings()
        self._cleanup_worker(self._active_name_worker)
        self._cleanup_worker(self._active_content_worker)
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = FileSearchTool()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()