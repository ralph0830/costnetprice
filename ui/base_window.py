"""
UI 기본 클래스 모듈

모든 윈도우에서 공통으로 사용하는 기능을 제공합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseWindow:
    """기본 윈도우 클래스"""

    def __init__(
        self,
        root: Optional[tk.Tk] = None,
        title: str = "Window",
        width: int = 800,
        height: int = 600
    ):
        """
        초기화

        Args:
            root: Tk 루트 (None이면 새로 생성)
            title: 윈도우 제목
            width: 윈도우 너비
            height: 윈도우 높이
        """
        if root is None:
            self.root = tk.Tk()
            self.is_main_window = True
        else:
            self.root = root
            self.is_main_window = False

        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.logger = logger

    def show_error(self, title: str, message: str):
        """에러 메시지 표시"""
        self.logger.error(f"{title}: {message}")
        messagebox.showerror(title, message)

    def show_warning(self, title: str, message: str):
        """경고 메시지 표시"""
        self.logger.warning(f"{title}: {message}")
        messagebox.showwarning(title, message)

    def show_info(self, title: str, message: str):
        """정보 메시지 표시"""
        self.logger.info(f"{title}: {message}")
        messagebox.showinfo(title, message)

    def ask_yes_no(self, title: str, message: str) -> bool:
        """Yes/No 질문"""
        return messagebox.askyesno(title, message)

    def run(self):
        """메인 루프 실행 (메인 윈도우만)"""
        if self.is_main_window:
            self.root.mainloop()


class BaseDialog(tk.Toplevel):
    """기본 다이얼로그 클래스"""

    def __init__(
        self,
        parent: tk.Tk,
        title: str = "Dialog",
        width: int = 600,
        height: int = 400,
        modal: bool = True
    ):
        """
        초기화

        Args:
            parent: 부모 윈도우
            title: 다이얼로그 제목
            width: 너비
            height: 높이
            modal: 모달 여부
        """
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")

        if modal:
            self.transient(parent)
            self.grab_set()

        self.logger = logger

    def show_error(self, title: str, message: str):
        """에러 메시지 표시"""
        self.logger.error(f"{title}: {message}")
        messagebox.showerror(title, message)

    def show_warning(self, title: str, message: str):
        """경고 메시지 표시"""
        self.logger.warning(f"{title}: {message}")
        messagebox.showwarning(title, message)

    def show_info(self, title: str, message: str):
        """정보 메시지 표시"""
        self.logger.info(f"{title}: {message}")
        messagebox.showinfo(title, message)

    def close(self):
        """다이얼로그 닫기"""
        self.destroy()
