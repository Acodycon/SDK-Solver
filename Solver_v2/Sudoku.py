from enum import Enum
from itertools import combinations
from typing import Any, List

from main import MainGUI, ctk_sleep, alg_progress_bar_handler, isSolvable
from Themes.colors import color_dict as cd

import customtkinter as ctk


class Board(ctk.CTkFrame):

    def __init__(self, main_gui: MainGUI, master: Any, **kwargs):
        super().__init__(master, **kwargs)
        self.board_type = None
        self.main_gui = main_gui
        self.board_box_frames = []
        self.selected_cell = None

    def construct_board(self):
        pass

    def on_cell_clicked(self, cell, c_row, c_col):
        self.main_gui.cell_row_label.value = c_row
        self.main_gui.cell_col_label.value = c_col
        self.main_gui.cell_value_label.value = cell.value
        self.main_gui.cell_pV_label.value = cell.possible_values
        if self.selected_cell:
            self.selected_cell.isSelected = False
        self.selected_cell = cell
        cell.isSelected = True
        print(f"Button in row: {c_row}, col: {c_col}, pV: {cell.possible_values}")


def check_filled_status(board):
    for row in board.cell_rows:
        for cell in row:
            if cell.value is None:
                return False
    return True


class Board9x9(Board):

    def __init__(self, main_gui: MainGUI, master: Any, **kwargs):
        super().__init__(main_gui, master, **kwargs)
        self.board_type = BoardType.NINE_X_NINE
        self.cell_rows: List[List[Cell]] = []
        self.cell_cols = [[] for i in range(9)]
        self.cell_boxes = [[] for i in range(9)]
        self.configure(fg_color=cd["black"])
        self.construct_board()

    def construct_board(self):
        # Create 9 frames.
        self.board_box_frames = [[ctk.CTkFrame(
            master=self,
            border_width=1) for j in range(3)] for i in range(3)]

        # Place the frames in the board_frame with padding to create seperations between the 9x9 boxes
        for i, frame_row in enumerate(self.board_box_frames):
            for j, frame in enumerate(frame_row):
                pad_left = 6 if j == 0 else 3
                pad_right = 6 if j == 2 else 3
                pad_top = 6 if i == 0 else 3
                pad_bottom = 6 if i == 2 else 3
                frame.grid(row=i, column=j, padx=(pad_left, pad_right),
                           pady=(pad_top, pad_bottom))  # Add some space between the frames

        # Create a 9x9 grid of buttons.
        for i in range(9):
            cell_row: List[Cell] = []
            for j in range(9):
                cell = Cell(
                    master=self.board_box_frames[i // 3][j // 3],
                    board=self,
                    containing_row=cell_row,
                    containing_col=self.cell_cols[j],
                    containing_box=self.cell_boxes[(i // 3) * 3 + j // 3],
                    text="",
                    font=("Arial", 50),
                    text_color=cd["tc_for_when_cell_is_empty"],
                    fg_color=cd["dark-grey"],
                    border_color=cd["black"],
                    hover_color=cd["pale-yellow"],
                    border_width=1,
                    corner_radius=0,
                    width=100,
                    height=100)
                cell.configure(
                    command=lambda btn=cell, c_row=i, c_col=j: self.on_cell_clicked(btn, c_row, c_col)
                )
                cell.grid(row=i % 3, column=j % 3, sticky="news")
                cell_row.append(cell)
                self.cell_cols[j].append(cell)
                self.cell_boxes[(i // 3) * 3 + j // 3].append(cell)
            self.cell_rows.append(cell_row)

    def get_unresolved_digit_count(self):
        return sum([sum([1 for cell in self.cell_rows[j] if not cell.isResolved]) for j in range(9)])

    def get_resolved_digit_count(self):
        return sum([sum([1 for cell in self.cell_rows[j] if cell.cget('text_color') == cd["banana"]]) for j in range(9)])

    def get_given_digit_count(self):
        print(self.cell_rows[0][0].cget('text_color'), cd["black"])
        print(sum([sum([1 for cell in self.cell_rows[j] if cell.cget('text_color') == "#000000"]) for j in range(9)]))
        return sum([sum([1 for cell in self.cell_rows[j] if cell.cget('text_color') == cd["black"]]) for j in range(9)])

    def get_possible_value_count(self):
        """gets the amount of possible values in all cells that aren't resolved.
        Helper function for the progress bar"""
        return sum([sum([len(cell.possible_values) for cell in self.cell_rows[j] if not cell.isResolved]) for j in range(9)])

    def get_fill_status(self):
        """returns a float value between 0 and 1 that represents the percentage to which the board is filled i.e. 0 = empty, 1 = full"""
        filled_cells = 0
        for row in self.cell_rows:
            for cell in row:
                if cell.isResolved:
                    filled_cells += 1
        return filled_cells / 81

    def is_solved(self):
        for row in self.cell_rows:
            if len(row) != len(set(row)):
                return False
        for col in self.cell_cols:
            if len(col) != len(set(col)):
                return False
        for box in self.cell_boxes:
            if len(box) != len(set(box)):
                return False
        return True if self.get_fill_status() == 1 else False






class Board6x6(Board):

    def __init__(self, main_gui: MainGUI, master: Any, **kwargs):
        super().__init__(main_gui, master, **kwargs)
        self.button_rows: List[List[Cell]] = []
        self.button_cols = [[] for i in range(6)]
        self.button_boxes = [[] for i in range(6)]


class BoardType(Enum):
    NINE_X_NINE = 9
    SIX_X_SIX = 6


class Cell(ctk.CTkButton):

    def __init__(self, board: Board9x9, containing_row, containing_col, containing_box, master: Any, **kwargs):
        super().__init__(master, **kwargs)
        self.value = None
        self._isSelected = False
        self.possible_values = None
        self.isResolved = False
        self.board = board
        self.board_type = board.board_type

        self.containing_row = containing_row
        self.containing_col = containing_col
        self.containing_box = containing_box

        match board.board_type:
            case BoardType.NINE_X_NINE:
                self.possible_values = {pV for pV in range(1, 10)}
            case BoardType.SIX_X_SIX:
                self.possible_values = {pV for pV in range(1, 7)}

    @property
    def isSelected(self):
        return self._isSelected

    @isSelected.setter
    def isSelected(self, value):
        self._isSelected = value
        if self._isSelected:
            self.select()
        else:
            self.deselect()

    def select(self):
        # if self.board.main_gui.current_alg_type is None:
        #     for cell in self.containing_row:
        #         cell.configure(fg_color=cd["very-dark-yellow"])
        #     for cell in self.containing_col:
        #         cell.configure(fg_color=cd["very-dark-yellow"])
        #     for cell in self.containing_box:
        #         cell.configure(fg_color=cd["very-dark-yellow"])
        if self.board.main_gui.current_alg_type is None:
            for row in self.board.cell_rows:
                for cell in row:
                    if cell.value == self.value and cell is not self and self.value is not None:
                        cell.configure(fg_color=cd["medium-dark-yellow"])
                    if cell in self.containing_row or cell in self.containing_col or cell in self.containing_box:
                        cell.configure(fg_color=cd["very-dark-yellow"])
        self.configure(fg_color=cd["dark-yellow"])

    def deselect(self):
        for row in self.board.cell_rows:
            for cell in row:
                cell.configure(fg_color=cd["dark-grey"])

    def update_cell_stats_labels(self):
        self.board.main_gui.cell_value_label.value = self.value
        self.board.main_gui.cell_pV_label.value = self.possible_values

    def update_board_stats_labels(self):
        self.board.main_gui.numbers_given_label.value = self.board.get_given_digit_count()
        self.board.main_gui.numbers_resolved_label.value = self.board.get_resolved_digit_count()
        self.board.main_gui.numbers_unresolved_label.value = self.board.get_unresolved_digit_count()
        self.board.main_gui.possible_values_remaining_label.value = self.board.get_possible_value_count()

    def clear_value(self):
        self.value = None
        self.isResolved = False
        match self.board_type:
            case BoardType.NINE_X_NINE:
                self.possible_values = {pV for pV in range(1, 10)}
            case BoardType.SIX_X_SIX:
                self.possible_values = {pV for pV in range(1, 7)}
        if self.board.main_gui.show_alg:
            self.configure(fg_color=cd["red"])
            ctk_sleep(main_gui=self.board.main_gui,
                      t=0.1,
                      alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
        self.configure(text="", text_color=cd["tc_for_when_cell_is_empty"])
        if self.isSelected:
            self.update_cell_stats_labels()
        self.update_board_stats_labels()
        if self.board.main_gui.show_alg:
            self.configure(fg_color=cd["dark-grey"])
            ctk_sleep(main_gui=self.board.main_gui,
                      t=0.1,
                      alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)

    def set_value_by_key_press(self, value):
        self.value = value
        self.isResolved = True
        self.possible_values = {value}
        # update stats label
        self.configure(text=str(value), text_color=cd["black"])
        if self.isSelected:
            self.update_cell_stats_labels()
        self.update_board_stats_labels()
        if isSolvable(self.board):
            self.board.main_gui.board_unique_solution_label.configure(text="Does have a unique solution", text_color=cd["pale-green"])
        else:
            self.board.main_gui.board_unique_solution_label.configure(text="Does not have a unique solution", text_color=cd["red"])

    def set_value_by_com_generating(self, value):
        self.value = value
        self.isResolved = True
        self.possible_values = {value}
        # update stats label
        self.configure(text=str(value), text_color=cd["black"])
        if self.isSelected:
            self.update_cell_stats_labels()
        self.update_board_stats_labels()

    def set_value_by_com_solving(self, value):
        self.value = value
        self.isResolved = True
        self.possible_values = {value}
        if self.board.main_gui.show_alg:
            self.configure(fg_color=cd["pale-green"])
            ctk_sleep(main_gui=self.board.main_gui,
                      t=0.5,
                      alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
        self.configure(text=str(value), text_color=cd["banana"])
        if self.isSelected:
            self.update_cell_stats_labels()
        self.update_board_stats_labels()
        if self.board.main_gui.show_alg:
            ctk_sleep(main_gui=self.board.main_gui,
                      t=0.5,
                      alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
            self.configure(fg_color=cd["dark-grey"])

    def is_valid(self, value):
        return not any(
            value in lst for lst in [[cell.value for cell in self.containing_row],
                                     [cell.value for cell in self.containing_col],
                                     [cell.value for cell in self.containing_box]]
        )

    def reduce_possible_values(self, values, n_of_pV_before_solve):
        n_of_pV_b4_redc = len(self.possible_values)
        self.possible_values -= values
        if self.isSelected:
            self.update_cell_stats_labels()
        n_of_pV_run_time = self.board.get_possible_value_count()
        progress = 1 - n_of_pV_run_time / n_of_pV_before_solve
        n_of_pV_aftr_redc = len(self.possible_values)
        if len(self.possible_values) == 1:  # cell gets resolved branch
            self.board.main_gui.reductions_made_label.value += 1
            self.set_value_by_com_solving(value=list(self.possible_values)[0])
            # allow the progress bar to track solving procedure
            alg_progress_bar_handler(main_gui=self.board.main_gui, progress=progress)
            return True
        else:
            if n_of_pV_b4_redc > n_of_pV_aftr_redc:  # cell gets reduced branch
                self.board.main_gui.reductions_made_label.value += 1
                self.board.main_gui.possible_values_remaining_label.value = n_of_pV_run_time
                print(self.board.main_gui.show_alg)
                if self.board.main_gui.show_alg:
                    self.configure(fg_color=cd["banana"])
                    ctk_sleep(main_gui=self.board.main_gui, t=0.1, alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
                    self.configure(fg_color=cd["dark-grey"])
            alg_progress_bar_handler(main_gui=self.board.main_gui, progress=progress)
            return False


class BackgroundBoardNbN:

    def __init__(self, board: Board9x9):
        self.cell_rows = [[BackgroundCell(cell) for cell in board.cell_rows[j]] for j in range(9)]
        self.cell_cols = [[BackgroundCell(cell) for cell in board.cell_cols[j]] for j in range(9)]
        self.cell_boxes = [[BackgroundCell(cell) for cell in board.cell_boxes[j]] for j in range(9)]

    def print_board(self):
        for row in self.cell_rows:
            print([cell.value for cell in row])


class BackgroundCell:

    def __init__(self, cell: Cell):
        self.value = cell.value
        self.isResolved = cell.isResolved
        self.possible_values = {pV for pV in range(1,10)}

    def reduce_possible_values(self, values):
        self.possible_values -= values
        if len(self.possible_values) == 1:
            self.value = list(self.possible_values)[0]
            self.isResolved = True
            return True
        else:
            return False
