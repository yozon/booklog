#!/usr/bin/env python
import pickle

from PyQt5.QtCore import QFile, QIODevice, Qt, QTextStream
from PyQt5.QtWidgets import (QDialog, QFileDialog, QGridLayout, QHBoxLayout,
        QLabel, QLineEdit, QMessageBox, QMenu, QPushButton, QTextEdit, QVBoxLayout,
        QWidget, QSizePolicy, QMainWindow)


class SortedDict(dict):
    class Iterator(object):
        def __init__(self, sorted_dict):
            self._dict = sorted_dict
            self._keys = sorted(self._dict.keys())
            self._nr_items = len(self._keys)
            self._idx = 0

        def __iter__(self):
            return self

        def next(self):
            if self._idx >= self._nr_items:
                raise StopIteration

            key = self._keys[self._idx]
            value = self._dict[key]
            self._idx += 1

            return key, value

        __next__ = next

    def __iter__(self):
        return SortedDict.Iterator(self)

    iterkeys = __iter__


class BookLog(QWidget):
    NavigationMode, AddingMode, EditingMode = range(3)

    def __init__(self, parent=None):
        super(BookLog, self).__init__(parent)

        self.contacts = SortedDict()
        self.oldTitle = ''
        self.oldMemo = ''
        self.currentMode = self.NavigationMode

        titleLabel = QLabel("書名:")
        self.titleLine = QLineEdit()
        self.titleLine.setReadOnly(True)

        memoLabel = QLabel("メモ:")
        self.memoText = QTextEdit()
        self.memoText.setReadOnly(True)

        self.addButton = QPushButton("&追加")
        self.addButton.show()
        self.editButton = QPushButton("&編集")
        self.editButton.setEnabled(False)
        self.removeButton = QPushButton("&削除")
        self.removeButton.setEnabled(False)
        self.findButton = QPushButton("&検索")
        self.findButton.setEnabled(False)
        self.submitButton = QPushButton("&挿入")
        self.submitButton.hide()
        self.cancelButton = QPushButton("&キャンセル")
        self.cancelButton.hide()

        self.nextButton = QPushButton("&次")
        self.nextButton.setEnabled(False)
        self.previousButton = QPushButton("&前")
        self.previousButton.setEnabled(False)

        self.loadButton = QPushButton("&Load...")
        self.loadButton.setToolTip("Load contacts from a file")
        self.saveButton = QPushButton("Sa&ve...")
        self.saveButton.setToolTip("Save contacts to a file")
        self.saveButton.setEnabled(False)

        self.exportButton = QPushButton("Ex&port")
        self.exportButton.setToolTip("Export as vCard")
        self.exportButton.setEnabled(False)

        self.dialog = FindDialog()

        self.addButton.clicked.connect(self.addContact)
        self.submitButton.clicked.connect(self.submitContact)
        self.editButton.clicked.connect(self.editContact)
        self.removeButton.clicked.connect(self.removeContact)
        self.findButton.clicked.connect(self.findContact)
        self.cancelButton.clicked.connect(self.cancel)
        self.nextButton.clicked.connect(self.next)
        self.previousButton.clicked.connect(self.previous)
        self.loadButton.clicked.connect(self.loadFromFile)
        self.saveButton.clicked.connect(self.saveToFile)
        self.exportButton.clicked.connect(self.exportAsVCard)

        #self.createMenus()
        #topFiller = QWidget()
        #topFiller.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        buttonLayout1 = QVBoxLayout()
        buttonLayout1.addWidget(self.addButton)
        buttonLayout1.addWidget(self.editButton)
        buttonLayout1.addWidget(self.removeButton)
        buttonLayout1.addWidget(self.findButton)
        buttonLayout1.addWidget(self.submitButton)
        buttonLayout1.addWidget(self.cancelButton)
        buttonLayout1.addWidget(self.loadButton)
        buttonLayout1.addWidget(self.saveButton)
        buttonLayout1.addWidget(self.exportButton)
        buttonLayout1.addStretch()

        buttonLayout2 = QHBoxLayout()
        buttonLayout2.addWidget(self.previousButton)
        buttonLayout2.addWidget(self.nextButton)

        mainLayout = QGridLayout()
        mainLayout.addWidget(titleLabel, 0, 0)
        mainLayout.addWidget(self.titleLine, 0, 1)
        mainLayout.addWidget(memoLabel, 1, 0, Qt.AlignTop)
        mainLayout.addWidget(self.memoText, 1, 1)
        mainLayout.addLayout(buttonLayout1, 1, 2)
        mainLayout.addLayout(buttonLayout2, 2, 1)
        #mainLayout.addWidget(topFiller)

        self.setLayout(mainLayout)
        self.setWindowTitle("Simple Book Log")


    def createUI(self):
        self.setWindowTitle('Equipment Manager 0.3')
        #Menu Bar
        fileMenuBar = QMenuBar(self)
        menuFile = QMenu(fileMenuBar)
        actionChangePath = QAction(tr("Change Path"), self)
        fileMenuBar.addMenu(menuFile)
        menuFile.addAction(actionChangePath)

    def addContact(self):
        self.oldTitle = self.titleLine.text()
        self.oldMemo = self.memoText.toPlainText()

        self.titleLine.clear()
        self.memoText.clear()

        self.updateInterface(self.AddingMode)

    def editContact(self):
        self.oldTitle = self.titleLine.text()
        self.oldMemo = self.memoText.toPlainText()

        self.updateInterface(self.EditingMode)

    def submitContact(self):
        title = self.titleLine.text()
        memo = self.memoText.toPlainText()

        if title == "" or memo == "":
            QMessageBox.information(self, "Empty Field",
                    "Please enter a title and memo.")
            return

        if self.currentMode == self.AddingMode:
            if title not in self.contacts:
                self.contacts[title] = memo
                QMessageBox.information(self, "追加しました",
                        "\"%s\" は追加されました。" % title)
            else:
                QMessageBox.information(self, "追加できませんでした",
                        "\"%s\" はすでに存在しています。" % title)
                return

        elif self.currentMode == self.EditingMode:
            if self.oldTitle != title:
                if title not in self.contacts:
                    QMessageBox.information(self, "編集しました",
                            "\"%s\" は編集されました。" % self.oldTitle)
                    del self.contacts[self.oldTitle]
                    self.contacts[title] = memo
                else:
                    QMessageBox.information(self, "編集できませんでした。",
                            "\"%s\"はすでに存在しています。" % title)
                    return
            elif self.oldMemo != memo:
                QMessageBox.information(self, "編集しました",
                        "\"%s\"は編集されました。" % title)
                self.contacts[title] = memo

        self.updateInterface(self.NavigationMode)
    # ボタンの処理
    def cancel(self):
        self.titleLine.setText(self.oldTitle)
        self.memoText.setText(self.oldMemo)
        self.updateInterface(self.NavigationMode)

    def removeContact(self):
        title = self.titleLine.text()
        memo = self.memoText.toPlainText()

        if title in self.contacts:
            button = QMessageBox.question(self, "Confirm Remove",
                    "Are you sure you want to remove \"%s\"?" % title,
                    QMessageBox.Yes | QMessageBox.No)

            if button == QMessageBox.Yes:
                self.previous()
                del self.contacts[title]

                QMessageBox.information(self, "Remove Successful",
                        "\"%s\" has been removed from your memo book." % title)

        self.updateInterface(self.NavigationMode)

    def next(self):
        title = self.titleLine.text()
        it = iter(self.contacts)

        try:
            while True:
                this_title, _ = it.next()

                if this_title == title:
                    next_title, next_memo = it.next()
                    break
        except StopIteration:
            next_title, next_memo = iter(self.contacts).next()

        self.titleLine.setText(next_title)
        self.memoText.setText(next_memo)

    def previous(self):
        title = self.titleLine.text()

        prev_title = prev_memo = None
        for this_title, this_memo in self.contacts:
            if this_title == title:
                break

            prev_title = this_title
            prev_memo = this_memo
        else:
            self.titleLine.clear()
            self.memoText.clear()
            return

        if prev_title is None:
            for prev_title, prev_memo in self.contacts:
                pass

        self.titleLine.setText(prev_title)
        self.memoText.setText(prev_memo)

    def findContact(self):
        self.dialog.show()

        if self.dialog.exec_() == QDialog.Accepted:
            contactTitle = self.dialog.getFindText()

            if contactTitle in self.contacts:
                self.titleLine.setText(contactTitle)
                self.memoText.setText(self.contacts[contacttitle])
            else:
                QMessageBox.information(self, "Contact Not Found",
                        "Sorry, \"%s\" is not in your address book." % contactTitle)
                return

        self.updateInterface(self.NavigationMode)
 # ボタンを押せるか押せないかの処理
    def updateInterface(self, mode):
        self.currentMode = mode

        if self.currentMode in (self.AddingMode, self.EditingMode):
            self.titleLine.setReadOnly(False)
            self.titleLine.setFocus(Qt.OtherFocusReason)
            self.memoText.setReadOnly(False)

            self.addButton.setEnabled(False)
            self.editButton.setEnabled(False)
            self.removeButton.setEnabled(False)

            self.nextButton.setEnabled(False)
            self.previousButton.setEnabled(False)

            self.submitButton.show()
            self.cancelButton.show()

            self.loadButton.setEnabled(False)
            self.saveButton.setEnabled(False)
            self.exportButton.setEnabled(False)

        elif self.currentMode == self.NavigationMode:
            if not self.contacts:
                self.titleLine.clear()
                self.memoText.clear()

            self.titleLine.setReadOnly(True)
            self.memoText.setReadOnly(True)
            self.addButton.setEnabled(True)

            number = len(self.contacts)
            self.editButton.setEnabled(number >= 1)
            self.removeButton.setEnabled(number >= 1)
            self.findButton.setEnabled(number > 2)
            self.nextButton.setEnabled(number > 1)
            self.previousButton.setEnabled(number >1 )

            self.submitButton.hide()
            self.cancelButton.hide()

            self.exportButton.setEnabled(number >= 1)

            self.loadButton.setEnabled(True)
            self.saveButton.setEnabled(number >= 1)

    def saveToFile(self):
        fileTitle, _ = QFileDialog.getSaveFileName(self, "Save book log",
                '', "Book Log (*.bl);;All Files (*)")

        if not fileTitle:
            return

        try:
            out_file = open(str(fileTitle), 'wb')
        except IOError:
            QMessageBox.information(self, "Unable to open file",
                    "There was an error opening \"%s\"" % fileTitle)
            return

        pickle.dump(self.contacts, out_file)
        out_file.close()

    def loadFromFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Address Book",
                '', "Address Book (*.abk);;All Files (*)")

        if not fileName:
            return

        try:
            in_file = open(str(fileName), 'rb')
        except IOError:
            QMessageBox.information(self, "Unable to open file",
                    "There was an error opening \"%s\"" % fileName)
            return

        self.contacts = pickle.load(in_file)
        in_file.close()

        if len(self.contacts) == 0:
            QMessageBox.information(self, "No contacts in file",
                    "The file you are attempting to open contains no "
                    "contacts.")
        else:
            for title, memo in self.contacts:
                self.titleLine.setText(title)
                self.memoText.setText(memo)

        self.updateInterface(self.NavigationMode)

    def exportAsVCard(self):
        title = str(self.titleLine.text())
        memo = self.memoText.toPlainText()

        titleList = title.split()

        if len(titleList) > 1:
            firstName = nameList[0]
            lastName = nameList[-1]
        else:
            firstName = name
            lastName = ''

        fileName, _ = QFileDialog.getSaveFileName(self, "Export Contact", '',
                "vCard Files (*.vcf);;All Files (*)")

        if not fileName:
            return

        out_file = QFile(fileName)

        if not out_file.open(QIODevice.WriteOnly):
            QMessageBox.information(self, "Unable to open file",
                    out_file.errorString())
            return

        out_s = QTextStream(out_file)

        out_s << 'BEGIN:VCARD' << '\n'
        out_s << 'VERSION:2.1' << '\n'
        out_s << 'N:' << lastName << ';' << firstName << '\n'
        out_s << 'FN:' << ' '.join(nameList) << '\n'

        address.replace(';', '\\;')
        address.replace('\n', ';')
        address.replace(',', ' ')

        out_s << 'ADR;HOME:;' << address << '\n'
        out_s << 'END:VCARD' << '\n'

        QMessageBox.information(self, "Export Successful",
                "\"%s\" has been exported as a vCard." % name)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        #self.fileMenu.addAction(self.newAct)
        #self.fileMenu.addAction(self.openAct)
        #self.fileMenu.addAction(self.saveAct)
        #self.fileMenu.addAction(self.printAct)
        #self.fileMenu.addSeparator()
        #self.fileMenu.addAction(self.exitAct)

        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.undoAct)
        self.editMenu.addAction(self.redoAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.cutAct)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.pasteAct)
        self.editMenu.addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.formatMenu = self.editMenu.addMenu("&Format")
        self.formatMenu.addAction(self.boldAct)
        self.formatMenu.addAction(self.italicAct)
        self.formatMenu.addSeparator().setText("Alignment")
        self.formatMenu.addAction(self.leftAlignAct)
        self.formatMenu.addAction(self.rightAlignAct)
        self.formatMenu.addAction(self.justifyAct)
        self.formatMenu.addAction(self.centerAct)
        self.formatMenu.addSeparator()
        self.formatMenu.addAction(self.setLineSpacingAct)
        self.formatMenu.addAction(self.setParagraphSpacingAct)


class FindDialog(QDialog):
    def __init__(self, parent=None):
        super(FindDialog, self).__init__(parent)

        findLabel = QLabel("Enter the name of a contact:")
        self.lineEdit = QLineEdit()

        self.findButton = QPushButton("&Find")
        self.findText = ''

        layout = QHBoxLayout()
        layout.addWidget(findLabel)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.findButton)

        self.setLayout(layout)
        self.setWindowTitle("Find a Contact")

        self.findButton.clicked.connect(self.findClicked)
        self.findButton.clicked.connect(self.accept)

    def findClicked(self):
        text = self.lineEdit.text()

        if not text:
            QMessageBox.information(self, "Empty Field",
                    "Please enter a name.")
            return

        self.findText = text
        self.lineEdit.clear()
        self.hide()

    def getFindText(self):
        return self.findText


if __name__ == '__main__':
    import sys

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    bookLog = BookLog()
    bookLog.show()

    sys.exit(app.exec_())