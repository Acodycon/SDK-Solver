import copy
import random
from enum import Enum
from itertools import combinations
from typing import Any, List

from Solver_v2.Utils import Algorithm
from main import MainGUI, ctk_sleep, alg_progress_bar_handler
from Themes.colors import color_dict as cd

import customtkinter as ctk


class Board(ctk.CTkFrame):

    def __init__(self, main_gui: MainGUI, master: Any, **kwargs):
        super().__init__(master, **kwargs)
        self.board_type = None
        self.main_gui = main_gui
        self.board_box_frames = []
        self._selected_cell = None

    @property
    def selected_cell(self):
        return self._selected_cell

    @selected_cell.setter
    def selected_cell(self, cell):
        if self._selected_cell:
            self._selected_cell.deselect()
            self.main_gui.cell_col_label.value = ""
            self.main_gui.cell_row_label.value = ""
            self.main_gui.cell_value_label.value = ""
            self.main_gui.cell_pV_label.value = ""
        if cell:
            cell.isSelected = True
        self._selected_cell = cell

    def construct_board(self):
        pass

    def on_cell_clicked(self, cell, c_row, c_col):
        self.main_gui.cell_row_label.value = c_row
        self.main_gui.cell_col_label.value = c_col
        self.main_gui.cell_value_label.value = cell.value
        self.main_gui.cell_pV_label.value = cell.possible_values
        self.selected_cell = cell
        print(f"Button in row: {c_row}, col: {c_col}, pV: {cell.possible_values}")


class Board9x9(Board):

    def __init__(self, main_gui: MainGUI, master: Any, **kwargs):
        super().__init__(main_gui, master, **kwargs)
        self.board_type = BoardType.NINE_X_NINE
        # all cells
        self.cells = []  # Never needs to be updated
        self.cell_rows = []  # Never needs to be updated
        self.cell_cols = [[] for i in range(9)]  # Never needs to be updated
        self.cell_boxes = [[] for i in range(9)]  # Never needs to be updated
        # all resolved cells
        self.resolved_cells = []
        self.cell_rows_resolved = []
        self.cell_cols_resolved = []
        self.cell_boxes_resolved = []
        # all unresolved cells
        self.unresolved_cells = []
        self.cell_rows_unresolved = []
        self.cell_cols_unresolved = []
        self.cell_boxes_unresolved = []
        # all 'given' cells (cells that are set by generating or the user to set a board) generally BLACK
        # For now I don't see a reason why I would need the givens in rows, cols and boxes
        self.given_cells = []
        # fill status (count of cells that are resolved or given)

        self.configure(fg_color=cd["black"])
        self.construct_board()

    @property
    def fillPercentage(self):
        """returns a float between 0 and 1 representing the fill status of the board"""
        return (len(self.given_cells) + len(self.resolved_cells)) / 81

    @property
    def isSolved(self):
        self.update_all_board_references()
        # checks if the board has any unresolved values left
        if len(self.unresolved_cells) != 0:
            self.main_gui.board_solved_status_label.configure(text="Not solved", text_color=cd["red"])
            return False
        # checks if every cells value only appears once in every row, col and box containing the cell
        for cell in self.cells:
            if sum([
                [c.value for c in cell.containing_row].count(cell.value),
                [c.value for c in cell.containing_col].count(cell.value),
                [c.value for c in cell.containing_box].count(cell.value)
            ]) != 3:
                self.main_gui.board_solved_status_label.configure(text="Not solved", text_color=cd["red"])
                return False
        self.main_gui.board_solved_status_label.configure(text="Solved", text_color=cd["pale-green"])
        return True

    @property
    def isSolvable(self):
        return BackgroundSolver(BackgroundBoardNbN(self)).isBoardSolvable

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
                self.cells.append(cell)
                cell_row.append(cell)
                self.cell_cols[j].append(cell)
                self.cell_boxes[(i // 3) * 3 + j // 3].append(cell)
            self.cell_rows.append(cell_row)

    def update_all_board_references(self):
        """
        should only be called when these lists are needed,
        calling them whenever something updates costs way too much processing power
        """
        self.unresolved_cells.clear()
        self.cell_rows_unresolved.clear()
        self.cell_cols_unresolved = [[] for j in range(9)]
        self.cell_boxes_unresolved = [[] for j in range(9)]

        self.resolved_cells.clear()
        self.cell_rows_resolved.clear()
        self.cell_cols_resolved = [[] for j in range(9)]
        self.cell_boxes_resolved = [[] for j in range(9)]

        self.given_cells.clear()

        for index_row, row in enumerate(self.cell_rows):
            cell_row_unresolved = []
            cell_row_resolved = []
            for index_col, cell in enumerate(row):
                # resolved, unresolved and given should all be mutually exclusive
                if cell.isUnresolved:
                    self.unresolved_cells.append(cell)
                    cell_row_unresolved.append(cell)
                    self.cell_cols_unresolved[index_col].append(cell)
                    self.cell_boxes_unresolved[(index_row // 3) * 3 + index_col // 3].append(cell)
                elif cell.isResolved:
                    self.resolved_cells.append(cell)
                    cell_row_resolved.append(cell)
                    self.cell_cols_resolved[index_col].append(cell)
                    self.cell_boxes_resolved[(index_row // 3) * 3 + index_col // 3].append(cell)
                else:
                    self.given_cells.append(cell)
            self.cell_rows_unresolved.append(cell_row_unresolved)
            self.cell_rows_resolved.append(cell_row_resolved)
        self.update_UI_stats()

    def update_UI_stats(self):
        if self.selected_cell:
            self.selected_cell.update_UI_stats()
        if self.isSolvable:
            self.main_gui.board_unique_solution_label.configure(text="Has a unique solution ", text_color=cd["pale-green"])
        else:
            self.main_gui.board_unique_solution_label.configure(text="Has no unique solution", text_color=cd["red"])


class Cell(ctk.CTkButton):

    def __init__(self, board: Board9x9, containing_row, containing_col, containing_box, master: Any, **kwargs):
        super().__init__(master, **kwargs)
        self.value = None
        self._isSelected = False
        self.possible_values = None
        self.isUnresolved = True
        self.isResolved = False
        self.isGiven = False
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

    def update_cell_UI_stats(self):
        if self.isSelected:
            self.board.main_gui.cell_value_label.value = self.value
            self.board.main_gui.cell_pV_label.value = self.possible_values

    def select(self):
        if self.board.main_gui.current_alg_type is None:
            for row in self.board.cell_rows:
                for cell in row:
                    if cell.value == self.value and cell is not self and self.value is not None:  # Tint all digits that are the same
                        cell.configure(fg_color=cd["medium-dark-yellow"])
                    if cell in self.containing_row or cell in self.containing_col or cell in self.containing_box:  # Tint all places a digit that's here couldn't go
                        cell.configure(fg_color=cd["very-dark-yellow"])
        self.configure(fg_color=cd["dark-yellow"])  # Tint the selected cell itself

    def deselect(self):
        for row in self.board.cell_rows:
            for cell in row:
                cell.configure(fg_color=cd["dark-grey"])

    def update_UI_stats(self):
        self.board.main_gui.cell_value_label.value = self.value
        self.board.main_gui.cell_pV_label.value = self.possible_values


    def set_given_value(self, value):
        self.value = value
        self.possible_values = {value}
        self.isGiven = True
        self.isUnresolved = False
        self.isResolved = False
        if self.board.main_gui.show_alg and self is not self.board.selected_cell:
            ctk_sleep(main_gui=self.board.main_gui, t=0.1, alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
            self.configure(fg_color=cd["pale-green"])
        self.configure(text=str(value), text_color=cd["black"])
        if self.board.main_gui.show_alg and self is not self.board.selected_cell:
            ctk_sleep(main_gui=self.board.main_gui, t=0.1, alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
            self.configure(fg_color=cd["dark-grey"])
        self.update_cell_UI_stats()

    def set_resolved_value(self, value):
        self.value = value
        self.possible_values = {value}
        self.isGiven = False
        self.isUnresolved = False
        self.isResolved = True
        if self.board.main_gui.show_alg and self is not self.board.selected_cell:
            ctk_sleep(main_gui=self.board.main_gui, t=0.1, alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
            self.configure(fg_color=cd["pale-green"])
        self.configure(text=str(value), text_color=cd["banana"])
        if self.board.main_gui.show_alg and self is not self.board.selected_cell:
            ctk_sleep(main_gui=self.board.main_gui, t=0.1, alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
            self.configure(fg_color=cd["dark-grey"])
        self.update_cell_UI_stats()

    def clear_value(self):
        self.value = None
        self.possible_values = {pV for pV in range(1, 10)}
        self.isGiven = False
        self.isUnresolved = True
        self.isResolved = False
        if self.board.main_gui.show_alg and self is not self.board.selected_cell:
            ctk_sleep(main_gui=self.board.main_gui, t=0.1, alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
            self.configure(fg_color=cd["red"])
        self.configure(text="")
        if self.board.main_gui.show_alg and self is not self.board.selected_cell:
            ctk_sleep(main_gui=self.board.main_gui, t=0.1, alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
            self.configure(fg_color=cd["dark-grey"])
        self.update_cell_UI_stats()

    def reduce_possible_values(self, values):
        pV_b4 = len(self.possible_values)
        self.possible_values -= values
        pV_aftr = len(self.possible_values)
        if len(self.possible_values) == 1:  # Cell gets resolved branch
            self.set_resolved_value(list(self.possible_values)[0])
        if pV_aftr < pV_b4:  # Cell gets reduced branch
            if self.board.main_gui.show_alg and self is not self.board.selected_cell:
                self.configure(fg_color=cd["banana"])
                ctk_sleep(main_gui=self.board.main_gui, t=0.1, alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
                self.configure(fg_color=cd["dark-grey"])

    def is_valid(self, value):
        """returns whether or not the value would be valid for this cell"""
        return not any(
            value in lst for lst in [[cell.value for cell in self.containing_row],
                                     [cell.value for cell in self.containing_col],
                                     [cell.value for cell in self.containing_box]]
        )


class Generator:

    def __init__(self, main_gui, board):
        self.main_gui = main_gui
        self.board = board



class BackgroundSolver:

    def __init__(self, bg_board):
        self.bg_board = bg_board

    @property
    def isBoardSolvable(self):
        iterations_without_change = 0
        while iterations_without_change < 4:
            board_before = [c.value for c in self.bg_board.cells]
            for bg_cell in self.bg_board.cells:
                if bg_cell.isResolved:
                    continue
                else:
                    self.reduction_by_constellation_set(bg_cell.c_row)
                    self.reduction_by_constellation_set(bg_cell.c_col)
                    self.reduction_by_constellation_set(bg_cell.c_box)
            board_after = [c.value for c in self.bg_board.cells]
            if board_before == board_after:
                iterations_without_change += 1
            else:
                iterations_without_change = 0
        return self.bg_board.isSolved

    def solve(self, alg):
        match alg:
            case Algorithm.SOLVING.ELIMINATION_BY_CONSTELLATION:
                if self.isBoardSolvable:
                    self.reduction_by_constellation()

    def reduction_by_constellation_set(self, bg_cells):
        """bg_cells is a set of nine BackgroundCells"""
        if bg_cells:
            possible_constellations = list()
            # get all possible combinations
            for size in range(1, 9):
                possible_constellations += combinations(bg_cells, size)
            for constellation in possible_constellations:
                shared_pVs = set()
                for bgc in constellation:
                    shared_pVs |= bgc.possible_values
                if len(shared_pVs) == len(constellation):
                    for bgcR in bg_cells:
                        if bgcR not in constellation and not bgcR.isResolved:
                            bgcR.reduce_possible_values(shared_pVs)

    def reduction_by_constellation(self):
        while not self.bg_board.isSolved:
            for bg_cell in self.bg_board.cells:
                # print(f"bg_cell: {bg_cell.value}, c_row: {[c.value for c in bg_cell.c_row]}")
                if bg_cell.isResolved:
                    continue
                else:
                    self.reduction_by_constellation_set(bg_cell.c_row)
                    self.reduction_by_constellation_set(bg_cell.c_col)
                    self.reduction_by_constellation_set(bg_cell.c_box)


class BackgroundBoardNbN:

    def __init__(self, board: Board9x9):
        self.og_board = board
        self.cells = []
        self.cell_rows = []
        self.cell_cols = [[] for i in range(9)]
        self.cell_boxes = [[] for i in range(9)]
        for row_index, row in enumerate(board.cell_rows):
            cell_row = []
            for col_index, cell in enumerate(row):
                bg_cell = BackgroundCell(
                    c_row=cell_row,
                    c_col=self.cell_cols[col_index],
                    c_box=self.cell_boxes[(row_index // 3) * 3 + col_index // 3],
                    cell=cell)
                self.cells.append(bg_cell)
                cell_row.append(bg_cell)
                self.cell_cols[col_index].append(bg_cell)
                self.cell_boxes[(row_index // 3) * 3 + col_index // 3].append(bg_cell)
            self.cell_rows.append(cell_row)

    @property
    def isSolved(self):
        # checks if the board has any unresolved values left
        if len([c for c in self.cells if not c.isResolved]) != 0:
            return False
        # checks if every cells value only appears once in every row, col and box containing the cell
        for cell in self.cells:
            if sum([
                [c.value for c in cell.c_row].count(cell.value),
                [c.value for c in cell.c_col].count(cell.value),
                [c.value for c in cell.c_box].count(cell.value)
            ]) != 3:
                return False
        return True

    def solve(self, alg):
        BackgroundSolver(self).solve(alg)

    def print_board(self):
        for row in self.cell_rows:
            print([cell.value for cell in row])

    def get_unresolved_cells(self):
        unresolved_cells = []
        for row in self.cell_rows:
            for cell in row:
                if not cell.isResolved:
                    unresolved_cells.append(cell)
        return unresolved_cells

    def solve_alg_backtracking(self):
        """try all possible values"""
        unresolved_cells = self.get_unresolved_cells()
        for unresolved_cell in unresolved_cells:
            for num in unresolved_cell.possible_values:
                if unresolved_cell.isValid(num):
                    unresolved_cell.set_value(num)
                    if self.solve_alg_backtracking():
                        return True
                    unresolved_cell.clear_value()
            return False
        return True

    def solve_alg_constellation_reduction(self):
        pass

    def reduce_all_possible_values(self):
        """reduction by soduko"""
        unresolved_cells = self.get_unresolved_cells()
        for unresolved_cell in unresolved_cells:
            pVs_for_unresolved_cell = {}
            for pV in range(1, 10):
                if unresolved_cell.isValid(pV):
                    pVs_for_unresolved_cell |= {pV}
            unresolved_cell.possible_values = pVs_for_unresolved_cell

    def print_back_to_og_board(self):
        for row_index, og_row in enumerate(self.og_board.cell_rows):
            for col_index, og_cell in enumerate(og_row):
                if self.cell_rows[row_index][col_index].isResolved and not self.og_board.cell_rows[row_index][col_index].isGiven:
                    og_cell.set_resolved_value(value=self.cell_rows[row_index][col_index].value)


class BackgroundCell:

    def __init__(self, c_row, c_col, c_box, cell):
        self.c_row = c_row
        self.c_col = c_col
        self.c_box = c_box
        self.value = copy.deepcopy(cell.value)
        self.isResolved = False if cell.isUnresolved else True
        self.possible_values = copy.deepcopy(cell.possible_values)

    def reduce_possible_values(self, values):
        self.possible_values -= values
        if len(self.possible_values) == 1:
            self.value = list(self.possible_values)[0]
            self.isResolved = True

    def clear_value(self):
        self.value = None
        self.isResolved = False
        self.possible_values = {pV for pV in range(1, 10)}

    def set_value(self, value):
        self.value = value
        self.isResolved = True
        self.possible_values = {value}

    def isValid(self, value):
        """returns True if the digit is valid"""
        return not any(
            value in lst for lst in [[cell.value for cell in self.c_row],
                                     [cell.value for cell in self.c_col],
                                     [cell.value for cell in self.c_box]]
        )


class BoardType(Enum):
    NINE_X_NINE = 9
    SIX_X_SIX = 6
