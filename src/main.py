import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtGui import QIcon
from datetime import datetime
from matplotlib.backends.backend_qt5agg import FigureCanvas

from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtWidgets import QFileDialog

MEAN_PLOT = 'Mean hole scores'
ROUND_PLOT = 'Round scores'
BEST_PLOT = 'Theoretically best round'
plots = [MEAN_PLOT, ROUND_PLOT, BEST_PLOT]

epoch = datetime(2021, 1, 1, 0, 0, 0)


class UDiscAnalyzer(QtWidgets.QMainWindow):
    def __init__(self):
        super(UDiscAnalyzer, self).__init__()
        uic.loadUi('../res/ui/udisc-analyzer.ui', self)
        self.setWindowTitle('UDisc Analyzer')
        self.setWindowIcon(QIcon('../res/images/icon.png'))

        self.courses = None
        self.scores = None
        self.scorecard = None
        self.show_numbers=False
        self.player = None
        self.course = None
        self.course_layout = None

        self.widget_plots = [None, None, None]
        self.widgets = [self.widget_plot_a, self.widget_plot_b, self.widget_plot_c]

        self.combobox_plot_a.addItems(plots)
        self.combobox_plot_a.setCurrentIndex(0)

        self.combobox_plot_b.addItems(plots)
        self.combobox_plot_b.setCurrentIndex(1)

        self.combobox_plot_c.addItems(plots)
        self.combobox_plot_c.setCurrentIndex(2)

        self.btn_load_scorecard.clicked.connect(self.get_scorecard)
        self.btn_change_show_numbers.clicked.connect(self.change_show_numbers)
        self.list_players.itemClicked.connect(self.update_lists)
        self.list_courses.itemClicked.connect(self.update_lists)
        self.list_layouts.itemClicked.connect(self.update_lists)

        fig_a, ax_a = plt.subplots()
        fig_b, ax_b = plt.subplots()
        fig_c, ax_c = plt.subplots()
        self.figs = [fig_a, fig_b, fig_c]
        self.axes = [ax_a, ax_b, ax_c]

        self.show()

    def get_scorecard(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file',
                                            os.getcwd(), "Image files (*.csv)")

        if not fname[0]:
            return

        self.text_scorecard.setText(fname[0])

        self.scorecard = pd.read_csv(fname[0]).replace(0, np.nan)

        self.list_players_update()
        self.list_courses_update(True)
        self.list_layouts_update(True)

        self.update_plots()

    def change_show_numbers(self):
        self.show_numbers = not self.show_numbers
        self.update_plots()

    def update_lists(self):
        cur_player = self.player
        self.list_players_update()
        new_player = cur_player != self.player

        cur_course = self.course
        self.list_courses_update(new_player)
        new_course = cur_course != self.course

        self.list_layouts_update(new_course or new_player)

        self.update_plots()

    def update_plots(self):
        self.update_plot_a()
        self.update_plot_b()
        self.update_plot_c()

    def list_players_update(self):
        if len(self.list_players.selectedItems()) == 0:
            self.scores = self.scorecard.loc[self.scorecard['PlayerName'] != 'Par']
            players = sorted(self.scores['PlayerName'].unique(), reverse=True,
                             key=lambda p: (self.scores.PlayerName == p).sum())

            self.list_players.addItems(players)
            self.list_players.setCurrentRow(0)

        self.player = self.list_players.currentItem().text()

    def list_courses_update(self, clear):
        self.courses = self.scorecard.loc[self.scorecard['PlayerName'] == 'Par'].drop_duplicates(
            subset=['CourseName', 'LayoutName'], keep='first')

        courses_by_player = self.scorecard.loc[self.scorecard['PlayerName'] == self.list_players.currentItem().text()]

        courses_only = sorted(courses_by_player['CourseName'].unique(), reverse=True,
                              key=lambda c: courses_by_player['CourseName'].value_counts()[c])

        if clear:
            self.list_courses.clear()
            self.list_courses.addItems(courses_only)
            self.list_courses.setCurrentRow(0)

        self.course = self.list_courses.currentItem().text()

    def list_layouts_update(self, clear):
        # layouts = self.courses.loc[
        #    self.courses['CourseName'] == self.list_courses.currentItem().text(), 'LayoutName'].unique().tolist()

        layouts_by_player = self.scorecard.loc[
            (self.scorecard['CourseName'] == self.course) & (self.scorecard['PlayerName'] == self.player)]

        layouts_only = sorted(layouts_by_player['LayoutName'].unique(), reverse=True,
                              key=lambda l: layouts_by_player['LayoutName'].value_counts()[l])

        if clear:
            self.list_layouts.clear()
            self.list_layouts.addItems(layouts_only)
            self.list_layouts.setCurrentRow(0)

        self.course_layout = self.list_layouts.currentItem().text()

    def update_plot_a(self):
        if self.combobox_plot_a.currentText() == MEAN_PLOT:
            self.plot_mean(0)
        elif self.combobox_plot_a.currentText() == ROUND_PLOT:
            self.plot_rounds(0)
        elif self.combobox_plot_a.currentText() == BEST_PLOT:
            self.plot_best(0)

    def update_plot_b(self):
        if self.combobox_plot_b.currentText() == MEAN_PLOT:
            self.plot_mean(1)
        elif self.combobox_plot_b.currentText() == ROUND_PLOT:
            self.plot_rounds(1)
        elif self.combobox_plot_b.currentText() == BEST_PLOT:
            self.plot_best(1)

    def update_plot_c(self):
        if self.combobox_plot_c.currentText() == MEAN_PLOT:
            self.plot_mean(2)
        elif self.combobox_plot_c.currentText() == ROUND_PLOT:
            self.plot_rounds(2)
        elif self.combobox_plot_c.currentText() == BEST_PLOT:
            self.plot_best(2)

    def plot_mean(self, i):
        df = self.scores.loc[(self.scores['PlayerName'] == self.player) & (self.scores['CourseName'] == self.course) & (
                self.scores['LayoutName'] == self.course_layout)]

        result = df.groupby("PlayerName").mean().select_dtypes(include=[np.number]).iloc[0, 2:]
        par = self.courses.loc[
                  (self.courses['CourseName'] == self.course) & (
                          self.courses['LayoutName'] == self.course_layout)].select_dtypes(
            include=[np.number]).iloc[0, 2:]

        self.axes[i].cla()
        par.plot(kind='line', ax=self.axes[i], style='--', alpha=0.3, label='Par')
        result.plot(kind='line', ax=self.axes[i], label='Mean')

        if self.show_numbers:
            for j, txt in enumerate(list(par)):
                self.axes[i].annotate(str(int(txt)), (j, txt), color='tab:blue', horizontalalignment='center',
                                      verticalalignment='top',alpha=0.3)
            for j, txt in enumerate(list(result)):
                self.axes[i].annotate(str(int(txt)), (j, txt), color='tab:orange', horizontalalignment='center',
                                      verticalalignment='bottom')

        # self.axes[i].xticks(rotation=70)
        self.figs[i].suptitle('Mean score per hole', fontsize=10)
        self.axes[i].set_xlabel('Hole', fontsize=8)
        self.axes[i].set_ylabel('Mean throws', fontsize=8)
        self.axes[i].set_ylim([0, 10])
        self.axes[i].legend(loc="upper left")

        if not self.widget_plots[i]:
            self.widget_plots[i] = FigureCanvas(self.figs[i])

            lay = QtWidgets.QVBoxLayout(self.widgets[i])
            lay.setContentsMargins(0, 0, 0, 0)
            lay.addWidget(self.widget_plots[i])
        else:
            self.figs[i].canvas.draw_idle()

    def handicap(self, scores):
        scores.sort()
        n = len(scores)
        if n < 6:
            handicap = scores[0]
        elif n < 9:
            handicap = np.mean(scores[:2])
        elif n < 12:
            handicap = np.mean(scores[:3])
        elif n < 15:
            handicap = np.mean(scores[:4])
        elif n < 17:
            handicap = np.mean(scores[:5])
        elif n < 19:
            handicap = np.mean(scores[:6])
        elif n == 19:
            handicap = np.mean(scores[:7])
        else:
            handicap = np.mean(scores[:8])

        if n < 4:
            handicap -= 2
        elif n == 4:
            handicap -= 1
        elif n == 6:
            handicap -= 1

        return handicap

    def handicap_list(self, scores):
        handicap_list = []
        for i, _ in enumerate(scores):
            handicap_list.append(self.handicap(scores[:i + 1]))
        return handicap_list

    def plot_rounds(self, i):
        df = self.scores.loc[(self.scores['PlayerName'] == self.player) & (self.scores['CourseName'] == self.course) & (
                self.scores['LayoutName'] == self.course_layout)]

        self.axes[i].cla()
        df = df.iloc[::-1]
        df.reset_index(drop=True, inplace=True)
        df.index += 1
        # dates=list(df['Date'])
        # days=[int((datetime.strptime(date, '%Y-%m-%d %H:%M')-epoch).total_seconds()/3600/24) for date in dates]
        df['+/-'].plot(kind='line', ax=self.axes[i], label='Score')



        handicap_list = self.handicap_list(list(df['+/-']))
        self.axes[i].plot(list(range(1, len(handicap_list) + 1)), handicap_list, '-o', markersize=3,
                          label='Handicap after round')

        if self.show_numbers:
            for j, txt in enumerate(list(df['+/-'])):
                self.axes[i].annotate(str(int(txt)), (j + 1, txt), color='tab:blue', horizontalalignment='center',
                                      verticalalignment='bottom')
            for j, txt in enumerate(handicap_list):
                self.axes[i].annotate(str(int(txt)), (j + 1, txt), color='tab:orange', horizontalalignment='center',
                                      verticalalignment='top')

        # self.axes[i].plot(days, list(df['+/-']),'-o',markersize=3)

        self.figs[i].suptitle('All rounds', fontsize=10)
        self.axes[i].set_xlabel('Round', fontsize=8)
        self.axes[i].set_ylabel('Score (+/-)', fontsize=8)
        self.axes[i].set_ylim([-10, self.scores['+/-'].max()])
        # self.axes[i].set_xlim([0, 365])
        self.axes[i].legend(loc="upper left")

        if not self.widget_plots[i]:
            self.widget_plots[i] = FigureCanvas(self.figs[i])

            lay = QtWidgets.QVBoxLayout(self.widgets[i])
            lay.setContentsMargins(0, 0, 0, 0)
            lay.addWidget(self.widget_plots[i])
        else:
            self.figs[i].canvas.draw_idle()

    def plot_best(self, i):
        df = self.scores.loc[(self.scores['PlayerName'] == self.player) & (self.scores['CourseName'] == self.course) & (
                self.scores['LayoutName'] == self.course_layout)]

        best = df.groupby("PlayerName").min().select_dtypes(include=[np.number]).iloc[0, 2:]

        par = self.courses.loc[
                  (self.courses['CourseName'] == self.course) & (
                          self.courses['LayoutName'] == self.course_layout)].select_dtypes(
            include=[np.number]).iloc[0, 2:]

        self.axes[i].cla()
        par.plot(kind='line', ax=self.axes[i], style='--', alpha=0.3, label='Par')
        best.plot(kind='line', ax=self.axes[i], label='Best')

        if self.show_numbers:
            for j, txt in enumerate(list(par)):
                self.axes[i].annotate(str(int(txt)), (j, txt), color='tab:blue', horizontalalignment='center',
                                      verticalalignment='top',alpha=0.3)
            for j, txt in enumerate(list(best)):
                self.axes[i].annotate(str(int(txt)), (j, txt), color='tab:orange', horizontalalignment='center',
                                      verticalalignment='bottom')

        # self.axes[i].xticks(rotation=70)
        self.figs[i].suptitle('Theoretically best round', fontsize=10)
        self.axes[i].set_xlabel('Hole', fontsize=8)
        self.axes[i].set_ylabel('Throws', fontsize=8)
        self.axes[i].set_ylim([0, 10])
        self.axes[i].legend(loc="upper left")

        if not self.widget_plots[i]:
            self.widget_plots[i] = FigureCanvas(self.figs[i])

            lay = QtWidgets.QVBoxLayout(self.widgets[i])
            lay.setContentsMargins(0, 0, 0, 0)
            lay.addWidget(self.widget_plots[i])
        else:
            self.figs[i].canvas.draw_idle()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = UDiscAnalyzer()
    sys.exit(app.exec_())
