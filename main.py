import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QTabWidget,
    QFileDialog, QAction, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QMenu
)
from PyQt5.QtGui import QColor, QPainter, QTextFormat
from PyQt5.QtCore import Qt, QRect, QSize, QPoint


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)


class NotepadPlusPlus(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Notepad++")
        self.resize(900, 600)

        self.tabWidget = QTabWidget()
        self.setCentralWidget(self.tabWidget)

        self.createMenus()
        self.newTab()

    def createMenus(self):
        menubar = self.menuBar()

        # Dosya
        fileMenu = menubar.addMenu("Dosya")
        fileMenu.addAction("Yeni Sekme", self.newTab)
        fileMenu.addAction("Aç", self.openFile)
        fileMenu.addAction("Kaydet", self.saveFile)
        fileMenu.addAction("Sekmeyi Kapat", self.closeCurrentTab)

        # Düzen
        editMenu = menubar.addMenu("Düzen")
        editMenu.addAction("Kes", lambda: self.currentEditor().cut())
        editMenu.addAction("Kopyala", lambda: self.currentEditor().copy())
        editMenu.addAction("Yapıştır", lambda: self.currentEditor().paste())
        editMenu.addAction("Tümünü Seç", lambda: self.currentEditor().selectAll())

        # Ara
        searchMenu = menubar.addMenu("Ara")
        searchMenu.addAction("Bul")  # Henüz işlev eklenmedi

        # Görünüm
        viewMenu = menubar.addMenu("Görünüm")
        viewMenu.addAction("Sekme Sayısını Göster", self.showTabCount)

        # Araçlar
        toolsMenu = menubar.addMenu("Araçlar")
        toolsMenu.addAction("Kod Temizleyici")  # Henüz işlev eklenmedi

        # Eklentiler
        pluginsMenu = menubar.addMenu("Eklentiler")
        pluginsMenu.addAction("Eklenti Yükle")  # Henüz işlev eklenmedi

        # Makrolar
        macrosMenu = menubar.addMenu("Makrolar")
        macrosMenu.addAction("Makro Kaydet")  # Henüz işlev eklenmedi

        # Pencereler
        windowsMenu = menubar.addMenu("Pencereler")
        windowsMenu.addAction("Tüm Sekmeleri Listele", self.listTabs)

    def newTab(self):
        editor = CodeEditor()
        index = self.tabWidget.addTab(editor, "Yeni Sekme")
        self.tabWidget.setCurrentIndex(index)

    def currentEditor(self):
        return self.tabWidget.currentWidget()

    def openFile(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Dosya Aç", "", "Metin Dosyaları (*.txt *.py *.cpp *.md)")
        if filePath:
            with open(filePath, 'r', encoding='utf-8') as file:
                content = file.read()
            editor = CodeEditor()
            editor.setPlainText(content)
            fileName = filePath.split("/")[-1]
            index = self.tabWidget.addTab(editor, fileName)
            self.tabWidget.setCurrentIndex(index)

    def saveFile(self):
        editor = self.currentEditor()
        if editor:
            filePath, _ = QFileDialog.getSaveFileName(self, "Dosyayı Kaydet", "", "Metin Dosyaları (*.txt *.py)")
            if filePath:
                with open(filePath, 'w', encoding='utf-8') as file:
                    file.write(editor.toPlainText())

    def closeCurrentTab(self):
        index = self.tabWidget.currentIndex()
        if index != -1:
            self.tabWidget.removeTab(index)

    def showTabCount(self):
        count = self.tabWidget.count()
        self.statusBar().showMessage(f"Açık sekme sayısı: {count}")

    def listTabs(self):
        names = [self.tabWidget.tabText(i) for i in range(self.tabWidget.count())]
        self.statusBar().showMessage("Açık sekmeler: " + ", ".join(names))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NotepadPlusPlus()
    window.show()
    sys.exit(app.exec_())
