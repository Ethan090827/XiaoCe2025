from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys, sip, random, os
from data import nation_template
from problems import problem_set
from localization import localization
from calculator import dist, bearing
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.lang = 0
        self.setGeometry(300, 300, 1000, 500)
        self.setWindowTitle('PhotoHunt')
        self.widget = QWidget()
        self.frame = QLabel(self)
        self.frame.resize(626, 400)
        self.nationenter = QLineEdit(self)
        self.guessbutton = QPushButton(self)
        self.guessbutton.clicked.connect(self.handleguess)
        self.notelabel = QLabel(self)
        self.errorlabel = QLabel(self)
        self.errorlabel.setStyleSheet('color: red')
        self.historylabel = QLabel(self)
        self.historylabel.setAlignment(Qt.AlignLeft)
        self.langcombo = QComboBox()
        self.langcombo.addItem('English')
        self.langcombo.addItem('简体中文')
        self.langcombo.addItem('日本語')
        self.langcombo.currentIndexChanged.connect(self.lang_init)
        self.layout = QGridLayout(self)
        self.layout.addWidget(self.frame, 0, 0, 2, 1)
        self.layout.addWidget(self.nationenter, 0, 1)
        self.layout.addWidget(self.guessbutton, 0, 2)
        self.layout.addWidget(self.errorlabel, 2, 1)
        self.layout.addWidget(self.historylabel, 1, 1, 1, 2)
        self.layout.addWidget(self.notelabel, 3, 0)
        self.layout.addWidget(self.langcombo, 2, 2)
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)
        
        self.game_status = 0 # 1 for winning, 2 for losing
        self.guessed_problems = [0]
        self.guessed_nations = []
        self.curr_problem = 0
        self.guesses = 6
        self.curr_ans = problem_set[self.curr_problem][0]
        self.curr_photo = QPixmap('./images/' + problem_set[self.curr_problem][1])
        self.curr_coords = problem_set[self.curr_problem][2]
        self.frame.setPixmap(self.curr_photo)
        
        self.lang_init()
    def lang_init(self):
        self.lang = self.langcombo.currentIndex()
        if self.game_status == 0:    self.guessbutton.setText(localization[self.lang]['guess'])
        else:   self.guessbutton.setText(localization[self.lang]['next'])
        self.notelabel.setText(localization[self.lang]['note'])
        self.errorlabel.setText('')
        self.update_history()
    def update_history(self):
        if self.game_status == 1:
            self.historylabel.setStyleSheet('color: green')
            self.historylabel.setText(localization[self.lang]['correct'] % self.nationenter.text())
        elif self.game_status == 2:
            self.historylabel.setStyleSheet('color: red')
            self.historylabel.setText(localization[self.lang]['fail'])
        else:
            self.historylabel.setStyleSheet('color: black')
            txt = ''
            for nation in self.guessed_nations:
                txt += localization[self.lang]['info'] % (nation_template[nation][self.lang][0],
                                                   bearing(nation_template[nation][3], self.curr_coords),
                                                   dist(nation_template[nation][3], self.curr_coords))
                txt += '\n'
            self.historylabel.setText(txt)
    def handleguess(self):
        self.errorlabel.setText('')
        if self.game_status == 1 or self.game_status == 2:
            self.new_game()
            return
        nation_guess = -1
        for i in range(len(nation_template)):
            if self.nationenter.text().lower() in list(map(lambda x: x.lower(), nation_template[i][0] + nation_template[i][1] + nation_template[i][2])):
                nation_guess = i
                break
        if nation_guess == -1:
            self.errorlabel.setText(localization[self.lang]['notexist'] % self.nationenter.text())
            return
        self.guesses -= 1
        if nation_guess == self.curr_ans:
            self.game_status = 1
            self.guessbutton.setText(localization[self.lang]['next'])
        else:
            self.guessed_nations.append(nation_guess)
            if self.guesses == 0:
                self.game_status = 2
                self.guessbutton.setText(localization[self.lang]['next'])
        self.update_history()
    def new_game(self):
        self.guesses = 6
        self.game_status = 0
        self.guessed_nations = []
        self.guessbutton.setText(localization[self.lang]['guess'])
        while self.curr_problem in self.guessed_problems:
            self.curr_problem = random.randint(1, len(problem_set) - 1)
        self.curr_ans = problem_set[self.curr_problem][0]
        self.curr_photo = QPixmap('/images/' + problem_set[self.curr_problem][1])
        self.curr_coords = problem_set[self.curr_problem][2]
        self.frame.setPixmap(self.curr_photo)
        self.guessed_problems.append(self.curr_problem)
        self.update_history()
app = QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
sys.exit(app.exec_())
