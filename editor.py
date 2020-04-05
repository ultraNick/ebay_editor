import os
import uuid
import sys
import re


from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QVBoxLayout,
    QAction,
    QDialog,
    QFileDialog,
    QColorDialog,
    QWidget,
    QStatusBar,
    QToolBar,
    QMessageBox,
    QFontComboBox,
    QComboBox,
    QActionGroup,
    QPushButton,
)
from PyQt5.QtGui import QImage, QTextDocument, QFont, QIcon, QKeySequence
from PyQt5.QtCore import Qt, QSize

FONT_SIZES = [7, 8, 9, 10, 11, 12, 13, 14, 18, 24, 36, 48, 64, 72, 96, 144, 288]
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp"]
HTML_EXTENSIONS = [".htm", ".html"]


def hexuuid():
    return uuid.uuid4().hex


def splitext(p):
    return os.path.splitext(p)[1].lower()


class TextEdit(QTextEdit):
    def canInsertFromMimeData(self, source):
        """
        source가 이미지인지 확인하고 이미지이면 True를 리턴. source가 이미지이면 window manager가 drop&down으로 이미지를 받을 수 있도록 설정.

        :param source: QMimeData object
        :return:
        """

        if source.hasImage():
            return True
        else:
            return False

    def insertFromMimeData(self, source):
        """
        위의 canInsertFromMimeData 메서드에서 이미지를 받아드리도록 설정되면, 실제 이미지를 문서 상으로 삽입하는 메서드.

        두 가지 경우를 처리
        1. 이미지를 직접 추가
        2. 파일에서 추가

        :param source: QMimeData object
        :return:
        """

        cursor = self.textCursor()  # 현재 커서 위치를 리턴
        document = self.document()  # 현재 문서를 리턴

        if source.hasUrls():  # PyQt5는 파일 위치를 URL로 표
            for u in source.urls():
                file_ext = splitext(str(u.toLocalFile()))
                if u.isLocalFile() and file_ext in IMAGE_EXTENSIONS:
                    image = QImage(u.toLocalFile())
                    document.addResource(QTextDocument.ImageResource, u, image)
                    cursor.insertImage(u.toLocalFile())
                else:
                    # If we hit a non-image or non-local URL break the loop and fall out
                    # to the super call & let Qt handle it
                    break
            else:
                # If all were valid images, finish here.
                return
        elif source.hasImage():
            image = source.imageData()
            uuid = hexuuid()
            document.addResource(QTextDocument.ImageResource, uuid, image)
            cursor.insertImage(uuid)

            return

        super(TextEdit, self).insertFromMimeData(source)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # self.path holds the path of the currently open file
        # If none, we haven't got a file open yet (or creating new)
        self.path = None
        self.origin_text_length = 0
        self.modified_text_length = 0

        self.setup()
        self.menu_and_toolbar()

        self.slot()

        # Initialize
        self.update_format()
        self.update_title()

        self.show()

    def setup(self):
        layout = QVBoxLayout()

        # Editor 설정
        self.editor = TextEdit()
        self.editor.setAutoFormatting(QTextEdit.AutoAll)
        font = QFont("Times", 12)
        self.editor.setFont(font)
        self.editor.setFontPointSize(12)

        self.convert_button = QPushButton("Convert")

        layout.addWidget(self.editor)
        layout.addWidget(self.convert_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.menuBar().setNativeMenuBar(False)

    def slot(self):
        self.editor.selectionChanged.connect(self.update_format)
        self.bold_action.toggled.connect(
            lambda x: self.editor.setFontWeight(QFont.Bold if x else QFont.Normal)
        )
        self.italic_action.toggled.connect(self.editor.setFontItalic)
        self.underline_action.toggled.connect(self.editor.setFontUnderline)
        self.new_file_action.triggered.connect(self.new_file)
        self.open_file_action.triggered.connect(self.file_open)
        self.save_file_action.triggered.connect(self.file_save)
        self.saveas_file_action.triggered.connect(self.file_saveas)
        self.undo_action.triggered.connect(self.editor.undo)
        self.redo_action.triggered.connect(self.editor.redo)
        self.cut_action.triggered.connect(self.editor.cut)
        self.copy_action.triggered.connect(self.editor.copy)
        self.paste_action.triggered.connect(self.editor.paste)
        self.select_action.triggered.connect(self.editor.selectAll)
        self.wrap_action.triggered.connect(self.edit_toggle_wrap)
        self.fonts.currentIndexChanged.connect(self.editor.setCurrentFont)
        self.fontsize.currentIndexChanged[str].connect(
            lambda s: self.editor.setFontPointSize(float(s))
        )
        self.text_color_action.triggered.connect(self.change_text_color)
        self.text_background_color_action.triggered.connect(
            self.change_text_background_color
        )
        self.alignl_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignLeft)
        )
        self.alignc_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignCenter)
        )
        self.alignr_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignRight)
        )
        self.alignj_action.triggered.connect(
            lambda: self.editor.setAlignment(Qt.AlignJustify)
        )

        self.convert_button.clicked.connect(self.convert_to_html)

    def menu_and_toolbar(self):
        file_toolbar = QToolBar("File")
        file_toolbar.setIconSize(QSize(14, 14))
        self.addToolBar(file_toolbar)
        file_menu = self.menuBar().addMenu("&File")

        self.new_file_action = QAction(
            QIcon(os.path.join("images", "document-plus.png")), "New file", self
        )
        self.new_file_action.setStatusTip("Create new file")
        file_menu.addAction(self.new_file_action)
        file_toolbar.addAction(self.new_file_action)

        self.open_file_action = QAction(
            QIcon(os.path.join("images", "blue-folder-open-document.png")),
            "Open file...",
            self,
        )
        self.open_file_action.setStatusTip("Open file")
        file_menu.addAction(self.open_file_action)
        file_toolbar.addAction(self.open_file_action)

        self.save_file_action = QAction(
            QIcon(os.path.join("images", "disk.png")), "Save", self
        )
        self.save_file_action.setStatusTip("Save current page")
        file_menu.addAction(self.save_file_action)
        file_toolbar.addAction(self.save_file_action)

        self.saveas_file_action = QAction(
            QIcon(os.path.join("images", "disk--pencil.png")), "Save As...", self
        )
        self.saveas_file_action.setStatusTip("Save current page to specified file")
        file_menu.addAction(self.saveas_file_action)
        file_toolbar.addAction(self.saveas_file_action)

        edit_toolbar = QToolBar("Edit")
        edit_toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(edit_toolbar)
        edit_menu = self.menuBar().addMenu("&Edit")

        self.undo_action = QAction(
            QIcon(os.path.join("images", "arrow-curve-180-left.png")), "Undo", self
        )
        self.undo_action.setStatusTip("Undo last change")
        edit_menu.addAction(self.undo_action)
        edit_toolbar.addAction(self.undo_action)

        self.redo_action = QAction(
            QIcon(os.path.join("images", "arrow-curve.png")), "Redo", self
        )
        self.redo_action.setStatusTip("Redo last change")
        edit_menu.addAction(self.redo_action)
        edit_toolbar.addAction(self.redo_action)

        edit_menu.addSeparator()

        self.cut_action = QAction(
            QIcon(os.path.join("images", "scissors.png")), "Cut", self
        )
        self.cut_action.setStatusTip("Cut selected text")
        self.cut_action.setShortcut(QKeySequence.Cut)
        edit_toolbar.addAction(self.cut_action)
        edit_menu.addAction(self.cut_action)

        self.copy_action = QAction(
            QIcon(os.path.join("images", "document-copy.png")), "Copy", self
        )
        self.copy_action.setStatusTip("Copy selected text")
        self.copy_action.setShortcut(QKeySequence.Copy)
        edit_toolbar.addAction(self.copy_action)
        edit_menu.addAction(self.copy_action)

        self.paste_action = QAction(
            QIcon(os.path.join("images", "clipboard-paste-document-text.png")),
            "Paste",
            self,
        )
        self.paste_action.setStatusTip("Paste from clipboard")
        self.paste_action.setShortcut(QKeySequence.Paste)
        edit_toolbar.addAction(self.paste_action)
        edit_menu.addAction(self.paste_action)

        self.select_action = QAction(
            QIcon(os.path.join("images", "selection-input.png")), "Select all", self
        )
        self.select_action.setStatusTip("Select all text")
        self.select_action.setShortcut(QKeySequence.SelectAll)
        edit_menu.addAction(self.select_action)
        edit_toolbar.addAction(self.select_action)

        edit_menu.addSeparator()

        self.wrap_action = QAction(
            QIcon(os.path.join("images", "arrow-continue.png")),
            "Wrap text to window",
            self,
        )
        self.wrap_action.setStatusTip("Toggle wrap text to window")
        self.wrap_action.setCheckable(True)
        self.wrap_action.setChecked(True)
        edit_menu.addAction(self.wrap_action)
        edit_toolbar.addAction(self.wrap_action)

        format_toolbar = QToolBar("Format")
        format_toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(format_toolbar)
        format_menu = self.menuBar().addMenu("&Foramt")

        self.fonts = QFontComboBox()
        format_toolbar.addWidget(self.fonts)

        self.fontsize = QComboBox()
        self.fontsize.addItems([str(s) for s in FONT_SIZES])
        format_toolbar.addWidget(self.fontsize)

        self.bold_action = QAction(
            QIcon(os.path.join("images", "edit-bold.png")), "Bold", self
        )
        self.bold_action.setStatusTip("Bold")
        self.bold_action.setShortcut(QKeySequence.Bold)
        self.bold_action.setCheckable(True)
        format_toolbar.addAction(self.bold_action)
        format_menu.addAction(self.bold_action)

        self.italic_action = QAction(
            QIcon(os.path.join("images", "edit-italic.png")), "Italic", self
        )
        self.italic_action.setStatusTip("Italic")
        self.italic_action.setShortcut(QKeySequence.Italic)
        self.italic_action.setCheckable(True)
        format_toolbar.addAction(self.italic_action)
        format_menu.addAction(self.italic_action)

        self.underline_action = QAction(
            QIcon(os.path.join("images", "edit-underline.png")), "Underline", self
        )
        self.underline_action.setStatusTip("Underline")
        self.underline_action.setShortcut(QKeySequence.Underline)
        self.underline_action.setCheckable(True)
        format_toolbar.addAction(self.underline_action)
        format_menu.addAction(self.underline_action)

        self.text_color_action = QAction(
            QIcon(os.path.join("images", "color-pencil.png")), "Text Color", self
        )
        self.text_color_action.setStatusTip("Change text color")
        format_toolbar.addAction(self.text_color_action)
        format_menu.addAction(self.text_color_action)

        self.text_background_color_action = QAction(
            QIcon(os.path.join("images", "color.png")), "Background Color", self
        )
        self.text_background_color_action.setStatusTip("Change text background color")
        format_toolbar.addAction(self.text_background_color_action)
        format_menu.addAction(self.text_background_color_action)

        format_menu.addSeparator()
        format_toolbar.addSeparator()

        self.alignl_action = QAction(
            QIcon(os.path.join("images", "edit-alignment.png")), "Align left", self
        )
        self.alignl_action.setStatusTip("Align text left")
        self.alignl_action.setCheckable(True)
        format_toolbar.addAction(self.alignl_action)
        format_menu.addAction(self.alignl_action)

        self.alignc_action = QAction(
            QIcon(os.path.join("images", "edit-alignment-center.png")),
            "Align center",
            self,
        )
        self.alignc_action.setStatusTip("Align text center")
        self.alignc_action.setCheckable(True)
        format_toolbar.addAction(self.alignc_action)
        format_menu.addAction(self.alignc_action)

        self.alignr_action = QAction(
            QIcon(os.path.join("images", "edit-alignment-right.png")),
            "Align right",
            self,
        )
        self.alignr_action.setStatusTip("Align text right")
        self.alignr_action.setCheckable(True)
        format_toolbar.addAction(self.alignr_action)
        format_menu.addAction(self.alignr_action)

        self.alignj_action = QAction(
            QIcon(os.path.join("images", "edit-alignment-justify.png")), "Justify", self
        )
        self.alignj_action.setStatusTip("Justify text")
        self.alignj_action.setCheckable(True)
        format_toolbar.addAction(self.alignj_action)
        format_menu.addAction(self.alignj_action)

        format_group = QActionGroup(self)
        format_group.setExclusive(True)
        format_group.addAction(self.alignl_action)
        format_group.addAction(self.alignc_action)
        format_group.addAction(self.alignr_action)
        format_group.addAction(self.alignj_action)

        format_menu.addSeparator()

    def new_file(self):
        if self.path:
            if self.origin_text_length != self.modified_text_length:
                button_reply = QMessageBox.question(
                    self,
                    "PyQt5 Message",
                    "Do you want to save?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )
                if button_reply == QMessageBox.Yes:
                    self.file_save()
            self.path = None
        else:
            text = self.editor.toPlainText()
            if len(text) > 0:
                button_reply = QMessageBox.question(
                    self,
                    "PyQt5 message",
                    "Do you want to save?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )
                if button_reply == QMessageBox.Yes:
                    self.file_save()

        self.editor.selectAll()
        self.editor.clear()
        self.update_title()

    def block_signals(self, objects, b):
        for o in objects:
            o.blockSignals(b)

    def update_format(self):
        """
        Update the font format toolbar/action when a new text selection is made.
        This is neccessary to keep toolbars/etc.
        in sync with the current edit state

        :return:
        """

        # A list of all format-related widgets/actions, so we can disable/enable signals when updating.
        self._format_action = [
            self.fonts,
            self.fontsize,
            self.bold_action,
            self.italic_action,
            self.underline_action,
        ]

        # Disable signals for all format widgets, so changing values here does not trigger further formatting
        self.block_signals(self._format_action, True)

        self.fonts.setCurrentFont(self.editor.currentFont())
        self.fontsize.setCurrentText(str(int(self.editor.fontPointSize())))
        self.italic_action.setChecked(self.editor.fontItalic())
        self.underline_action.setChecked(self.editor.fontUnderline())
        self.bold_action.setChecked(self.editor.fontWeight() == QFont.Bold)

        self.alignl_action.setChecked(self.editor.alignment() == Qt.AlignLeft)
        self.alignc_action.setChecked(self.editor.alignment() == Qt.AlignCenter)
        self.alignr_action.setChecked(self.editor.alignment() == Qt.AlignRight)
        self.alignj_action.setChecked(self.editor.alignment() == Qt.AlignJustify)

        self.block_signals(self._format_action, False)

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "",
            "HTML documents (*.html);Text Documents (*.txt);All files (*.*)",
        )

        try:
            with open(path, "r") as f:
                text = f.read()
        except Exception as e:
            self.dialog_critical(str(e))
        else:
            self.path = path
            # Qt will automatically try and guess the format as txt/html
            self.editor.setText(text)
            self.update_title()

    def file_save(self):
        if self.path is None:
            # If we do not have a path, we need to use Save As.
            return self.file_saveas()

        text = (
            self.editor.toHtml()
            if splitext(self.path) in HTML_EXTENSIONS
            else self.editor.toPlainText()
        )

        try:
            with open(self.path, "w") as f:
                f.write(text)
        except Exception as e:
            self.dialog_critical(str(e))

    def file_saveas(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save file",
            "",
            "HTML documents (*.html);Text documents (*.txt);All files (*.*)",
        )

        if not path:
            # If dialog is cancelled, will return ''
            return

        text = (
            self.editor.toHtml()
            if splitext(path) in HTML_EXTENSIONS
            else self.editor.toPlainText()
        )

        try:
            with open(path, "w") as f:
                f.write(text)
        except Exception as e:
            self.dialog_critical(str(e))
        else:
            self.path = path
            self.update_title()

    def convert_to_html(self):
        dialog = QDialog()

        tool_bar = QToolBar("Edit")
        tool_bar.setIconSize(QSize(14, 14))

        self.copy_html_button = QPushButton("Copy")

        self.html_dialog_editor = QTextEdit()
        self.html_dialog_editor.setReadOnly(True)

        html = self.editor.toHtml()
        body = re.search("<body.*/body>", html, re.I | re.S)
        self.html_dialog_editor.setPlainText(body.group()[89:-7])

        layout = QVBoxLayout()
        layout.addWidget(self.copy_html_button)
        layout.addWidget(self.html_dialog_editor)

        dialog.setLayout(layout)

        self.copy_html_button.clicked.connect(self.copy_html)

        dialog.exec()

    def copy_html(self):
        self.html_dialog_editor.selectAll()
        self.html_dialog_editor.copy()

    def update_title(self):
        self.setWindowTitle(os.path.basename(self.path) if self.path else "Untitled")

    def edit_toggle_wrap(self):
        self.editor.setLineWrapMode(1 if self.editor.lineWrapMode() == 0 else 0)

    def _get_color(self):
        color = QColorDialog()
        selected_color = color.getColor()
        if selected_color.isValid():
            return selected_color

    def change_text_color(self):
        color = self._get_color()
        if color is not None:
            self.editor.setTextColor(color)

    def change_text_background_color(self):
        color = self._get_color()
        if color is not None:
            self.editor.setTextBackgroundColor(color)

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    sys.exit(app.exec())
