import copy
from enum import Enum
from itertools import combinations
from typing import Any

import customtkinter as ctk
import random

from Solver_v2.Utils import Difficulty, SolveType, Algorithm, get_difficulty_range, ValueLabel
from Solver_v3.SudokuV3 import CellChange
from Themes.colors import color_dict as cd

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def ctk_sleep(main_gui, t, alg_speed_multiplier):
    """emulating time.sleep(seconds)"""
    ctk_instance = main_gui.root
    ms = int(t * 1000 / alg_speed_multiplier)
    var = ctk.BooleanVar(ctk_instance, value=False)
    ctk_instance.after(ms, var.set, True)
    ctk_instance.wait_variable(var)


def alg_progress_bar_handler(main_gui, progress):
    main_gui.alg_progress_bar.set(progress)


def alg_label_handler(main_gui, alg_type):
    if alg_type is None:
        main_gui.current_alg_label.configure(text=f"current algorithm: None", font=("Arial", 20))
    else:
        main_gui.current_alg_label.configure(text=f"Current algorithm: {alg_type.value} . . . ", font=("Arial", 20))


class BoardType(Enum):
    NINE_X_NINE = 9
    SIX_X_SIX = 6


class Board(ctk.CTkFrame):

    def __init__(self, main_gui: 'MainGUI', master: Any, **kwargs):
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

    def __init__(self, main_gui: 'MainGUI', master: Any, **kwargs):
        super().__init__(main_gui, master, **kwargs)
        self.board_type = BoardType.NINE_X_NINE
        # all cells
        self.cells = []  # Never needs to be updated
        self.cell_rows = []  # Never needs to be updated
        self.cell_cols = [[] for _ in range(9)]  # Never needs to be updated
        self.cell_boxes = [[] for _ in range(9)]  # Never needs to be updated
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
    def isUniquelySolvable(self):
        return self.main_gui.background_solver.isBoardUniquelySolvable

    def construct_board(self):
        # Create 9 frames.
        self.board_box_frames = [[ctk.CTkFrame(
            master=self,
            border_width=1) for _ in range(3)] for _ in range(3)]

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
            cell_row = []
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

    def clear_board(self):
        self.main_gui.current_alg_type = Algorithm.CLEARING.CLEARING
        self.main_gui.recursions_checked_label.value = 0
        self.main_gui.recursions_made_label.value = 0
        self.main_gui.reductions_checked_label.value = 0
        self.main_gui.reductions_by_constellation_label.value = 0
        self.main_gui.reductions_by_sudoku_label.value = 0
        self.main_gui.constellations_checked_label.value = 0
        for index, cell in enumerate(self.cells):
            cell.clear_value()  # We clear every cell to also reset every possible values that might still be linguering
            # set progress bar
            progress = index / 80
            alg_progress_bar_handler(main_gui=self.main_gui, progress=progress)
        self.main_gui.current_alg_type = None

    def reset_board(self):
        print("reset board")
        self.main_gui.current_alg_type = Algorithm.CLEARING.RESETTING
        self.main_gui.recursions_checked_label.value = 0
        self.main_gui.reductions_by_constellation_label.value = 0
        self.main_gui.reductions_by_sudoku_label.value = 0
        self.main_gui.constellations_checked_label.value = 0
        self.selected_cell = None
        self.update_all_board_references()
        resolved_cell_count = len(self.resolved_cells)  # For progress
        for i, c in enumerate(self.resolved_cells):
            c.clear_value()
            progress = i / resolved_cell_count - 1
            alg_progress_bar_handler(main_gui=self.main_gui, progress=progress)
        self.main_gui.current_alg_type = None

    def update_all_board_references(self):
        """
        should only be called when these lists are needed,
        calling them whenever something updates costs way too much processing power
        """
        self.unresolved_cells.clear()
        self.cell_rows_unresolved.clear()
        self.cell_cols_unresolved = [[] for _ in range(9)]
        self.cell_boxes_unresolved = [[] for _ in range(9)]

        self.resolved_cells.clear()
        self.cell_rows_resolved.clear()
        self.cell_cols_resolved = [[] for _ in range(9)]
        self.cell_boxes_resolved = [[] for _ in range(9)]

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
        if self.isUniquelySolvable:
            self.main_gui.board_unique_solution_label.configure(text="Has a unique solution ",
                                                                text_color=cd["pale-green"])
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

    def board_stats_handler(self, change_state):
        """
        should be called before any changes to the cell are actually made
        """
        match change_state:
            case CellChange.UNRESOLVED_TO_RESOLVED:
                self.board.main_gui.numbers_unresolved_label.value -= 1
                self.board.main_gui.numbers_resolved_label.value += 1
            case CellChange.UNRESOLVED_TO_GIVEN:
                self.board.main_gui.numbers_unresolved_label.value -= 1
                self.board.main_gui.numbers_given_label.value += 1
            case CellChange.RESOLVED_TO_UNRESOLVED:
                self.board.main_gui.numbers_resolved_label.value -= 1
                self.board.main_gui.numbers_unresolved_label.value += 1
            case CellChange.RESOLVED_TO_GIVEN:
                self.board.main_gui.numbers_resolved_label.value -= 1
                self.board.main_gui.numbers_given_label.value += 1
            case CellChange.GIVEN_TO_UNRESOLVED:
                self.board.main_gui.numbers_given_label.value -= 1
                self.board.main_gui.numbers_unresolved_label.value += 1
            case CellChange.GIVEN_TO_RESOLVED:
                self.board.main_gui.numbers_given_label.value -= 1
                self.board.main_gui.numbers_resolved_label.value += 1

    def set_given_value(self, value):
        if not self.isGiven:
            self.board_stats_handler(change_state=CellChange.UNRESOLVED_TO_GIVEN)
        self.value = value
        self.possible_values = {value}
        self.isGiven = True
        self.isUnresolved = False
        self.isResolved = False
        if self.board.main_gui.show_alg and self is not self.board.selected_cell:
            ctk_sleep(main_gui=self.board.main_gui, t=0.1,
                      alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
            self.configure(fg_color=cd["pale-green"])
        self.configure(text=str(value), text_color=cd["black"])
        if self.board.main_gui.show_alg and self is not self.board.selected_cell:
            ctk_sleep(main_gui=self.board.main_gui, t=0.1,
                      alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
            self.configure(fg_color=cd["dark-grey"])
        self.update_cell_UI_stats()

    def set_resolved_value(self, value):
        if not self.isResolved:
            self.board_stats_handler(change_state=CellChange.UNRESOLVED_TO_RESOLVED)
        self.value = value
        self.possible_values = {value}
        self.isGiven = False
        self.isUnresolved = False
        self.isResolved = True
        if self.board.main_gui.show_alg and self is not self.board.selected_cell:
            ctk_sleep(main_gui=self.board.main_gui, t=0.1,
                      alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
            self.configure(fg_color=cd["pale-green"])
        self.configure(text=str(value), text_color=cd["banana"])
        if self.board.main_gui.show_alg and self is not self.board.selected_cell:
            ctk_sleep(main_gui=self.board.main_gui, t=0.1,
                      alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
            self.configure(fg_color=cd["dark-grey"])
        self.update_cell_UI_stats()

    def clear_value(self):
        if self.isGiven:
            self.board_stats_handler(CellChange.GIVEN_TO_UNRESOLVED)
        elif self.isResolved:
            self.board_stats_handler(CellChange.RESOLVED_TO_UNRESOLVED)
        self.value = None
        self.possible_values = {pV for pV in range(1, 10)}
        self.isGiven = False
        self.isUnresolved = True
        self.isResolved = False
        if self.board.main_gui.show_alg and self is not self.board.selected_cell:
            ctk_sleep(main_gui=self.board.main_gui, t=0.1,
                      alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
            self.configure(fg_color=cd["red"])
        self.configure(text="")
        if self.board.main_gui.show_alg and self is not self.board.selected_cell:
            ctk_sleep(main_gui=self.board.main_gui, t=0.1,
                      alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
            self.configure(fg_color=cd["dark-grey"])
        self.update_cell_UI_stats()

    def reduce_possible_values(self, values):
        pV_b4 = len(self.possible_values)
        self.possible_values -= values
        pV_aftr = len(self.possible_values)
        if len(self.possible_values) == 1:  # Cell gets resolved branch
            self.set_resolved_value(list(self.possible_values)[0])
        if pV_aftr < pV_b4:  # Cell gets reduced branch
            if self is not self.board.selected_cell:
                self.configure(fg_color=cd["banana"])
                ctk_sleep(main_gui=self.board.main_gui, t=0.1,
                          alg_speed_multiplier=self.board.main_gui.alg_speed_multiplier)
                self.configure(fg_color=cd["dark-grey"])

    def is_valid(self, value):
        """returns whether the value would be valid for this cell or not"""
        return not any(
            value in lst for lst in [[cell.value for cell in self.containing_row],
                                     [cell.value for cell in self.containing_col],
                                     [cell.value for cell in self.containing_box]]
        )


class BackgroundBoardNbN:

    def __init__(self, board: Board9x9):
        self.og_board = board
        self.cells = []
        self.cell_rows = []
        self.cell_cols = [[] for _ in range(9)]
        self.cell_boxes = [[] for _ in range(9)]
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

    @property
    def isUniquelySolvable(self):
        snap_shot = [c.value for c in self.cells]
        isSolvable = BackgroundSolver(main_gui=self.og_board.main_gui).check_if_bg_board_is_uniquely_solvable(bg_board=self)
        for i, val in enumerate(snap_shot):
            if val:
                self.cells[i].set_value(val)
            else:
                self.cells[i].clear_value()
        return isSolvable

    def clear_bg_board(self):
        for c in self.cells:
            c.clear_value()

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
                if unresolved_cell.is_valid(num):
                    unresolved_cell.set_value(num)
                    if self.solve_alg_backtracking():
                        return True
                    unresolved_cell.clear_value()
            return False
        return True

    def reduce_all_possible_values(self):
        """reduction by soduko"""
        unresolved_cells = self.get_unresolved_cells()
        for unresolved_cell in unresolved_cells:
            pVs_for_unresolved_cell = {}
            for pV in range(1, 10):
                if unresolved_cell.is_valid(pV):
                    pVs_for_unresolved_cell |= {pV}
            unresolved_cell.possible_values = pVs_for_unresolved_cell

    def print_back_to_og_board(self):
        for row_index, og_row in enumerate(self.og_board.cell_rows):
            for col_index, og_cell in enumerate(og_row):
                if self.cell_rows[row_index][col_index].isResolved and not self.og_board.cell_rows[row_index][
                    col_index].isGiven:
                    og_cell.set_resolved_value(value=self.cell_rows[row_index][col_index].value)

    def print_back_to_og_board_as_given(self):
        for row_index, og_row in enumerate(self.og_board.cell_rows):
            for col_index, og_cell in enumerate(og_row):
                if self.cell_rows[row_index][col_index].isResolved:
                    og_cell.set_given_value(value=self.cell_rows[row_index][col_index].value)


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

    def is_valid(self, value):
        """returns True if the digit is valid"""
        return not any(
            value in lst for lst in [[cell.value for cell in self.c_row],
                                     [cell.value for cell in self.c_col],
                                     [cell.value for cell in self.c_box]]
        )


class BackgroundSolver:

    def __init__(self, main_gui):
        self.main_gui = main_gui
        self.bg_board = BackgroundBoardNbN(main_gui.board)
        self.reductions_by_sudoku = 0
        self.reductions_by_constellations = 0
        self.constellations_checked = 0
        self.recursions_checked = 0

    def update_board(self):
        """
        fetches a new copy of the current main board
        """
        self.bg_board = BackgroundBoardNbN(self.main_gui.board)

    def check_if_bg_board_is_uniquely_solvable(self, bg_board):
        iterations_without_change = 0
        while iterations_without_change < 4:
            board_before = [c.value for c in bg_board.cells]
            for bg_cell in bg_board.cells:
                if bg_cell.isResolved:
                    continue
                else:
                    self.reduction_by_constellation_set(bg_cell.c_row)
                    self.reduction_by_constellation_set(bg_cell.c_col)
                    self.reduction_by_constellation_set(bg_cell.c_box)
            board_after = [c.value for c in bg_board.cells]
            if board_before == board_after:
                iterations_without_change += 1
            else:
                iterations_without_change = 0
        return bg_board.isSolved


    @property
    def isBoardUniquelySolvable(self):
        self.update_board()
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

    def solve(self):
        self.update_board()
        self.main_gui.board.selected_cell = None  # Just to handle the decoloration in case a cell is selected
        self.reductions_by_sudoku = 0
        self.reductions_by_constellations = 0
        self.constellations_checked = 0
        self.recursions_checked = 0
        match self.main_gui.selected_solving_algorithm:
            case Algorithm.SOLVING.ELIMINATION_BY_CONSTELLATION:
                if self.isBoardUniquelySolvable:
                    self.reduction_by_constellation()
                    self.bg_board.print_back_to_og_board()
            case Algorithm.SOLVING.ELIMINATION_OPTIMIZED:
                if self.isBoardUniquelySolvable:
                    self.reduction_by_constellation_optimized()
                    self.bg_board.print_back_to_og_board()
            case Algorithm.SOLVING.BACKTRACKING:
                self.backtracking()
                self.bg_board.print_back_to_og_board()
            case Algorithm.SOLVING.BACKTRACKING_OPTIMIZED:
                self.reduction_by_sudoku()
                self.backtracking()
                self.bg_board.print_back_to_og_board()
        self.main_gui.recursions_checked_label.value = self.recursions_checked
        self.main_gui.reductions_by_sudoku_label.value = self.reductions_by_sudoku
        self.main_gui.reductions_by_constellation_label.value = self.reductions_by_constellations
        self.main_gui.constellations_checked_label.value = self.constellations_checked

    def backtracking(self):
        unresolved_cells = [bgc for bgc in self.bg_board.cells if not bgc.isResolved]
        for bgc in unresolved_cells:
            for value in bgc.possible_values:
                if bgc.is_valid(value=value):
                    bgc.set_value(value=value)
                    self.recursions_checked += 1
                    unresolved_cells.remove(bgc)
                    if self.backtracking():
                        return True
                    bgc.clear_value()
                    unresolved_cells.append(bgc)
            return False
        return True

    def reduction_by_constellation(self):
        while not self.bg_board.isSolved:
            for bgC in self.bg_board.cells:
                # print(f"bg_cell: {bg_cell.value}, c_row: {[c.value for c in bg_cell.c_row]}")
                if bgC.isResolved:
                    continue
                else:
                    self.reduction_by_constellation_set(bgCs=bgC.c_row)
                    self.reduction_by_constellation_set(bgCs=bgC.c_col)
                    self.reduction_by_constellation_set(bgCs=bgC.c_box)

    def reduction_by_constellation_optimized(self):
        while not self.bg_board.isSolved:
            self.reduction_by_sudoku()
            for row in [[c for c in self.bg_board.cell_rows[j] if not c.isResolved] for j in range(9)]:
                self.reduction_by_constellation_optimized_set(cell_set=row)
            for col in [[c for c in self.bg_board.cell_cols[j] if not c.isResolved] for j in range(9)]:
                self.reduction_by_constellation_optimized_set(cell_set=col)
            for box in [[c for c in self.bg_board.cell_boxes[j] if not c.isResolved] for j in range(9)]:
                self.reduction_by_constellation_optimized_set(cell_set=box)

    def reduction_by_sudoku(self):
        rbgCs = [bgc for bgc in self.bg_board.cells if bgc.isResolved]  # get all resolved cells
        for rbgC in rbgCs:
            ubgCs = self.get_unresolved_cells_in_rcb(
                rbgC)  # get a set of unresolved cells in the same row, col and box of the resolved or given cells
            for ubgC in ubgCs:  # Reduce the unresolved cell's pVs by the value of the resolved or given cell
                b4 = len(ubgC.possible_values)
                ubgC.reduce_possible_values({rbgC.value})
                aftr = len(ubgC.possible_values)
                self.reductions_by_sudoku += b4 - aftr
                if ubgC.isResolved:
                    rbgCs.append(ubgC)
        if self.bg_board.isSolved:  # This check gets done in case we solve the board with only this method
            return

    def get_unresolved_cells_in_rcb(self, cell):
        """
        cell passed in here should be resolved or given.
        Returns a set of all cells in the same row, col and box as the passed in cell
        """
        return {cell for lst in [cell.c_row,
                                 cell.c_col,
                                 cell.c_box] for cell in lst if not cell.isResolved}

    def reduction_by_constellation_set(self, bgCs):  # This function is currently used to determine a boards solvability
        """bg_cells is a set of nine BackgroundCells"""
        if bgCs:
            possible_constellations = list()
            # get all possible combinations
            for size in range(1, 9):
                possible_constellations += combinations(bgCs, size)
            for constellation in possible_constellations:
                self.constellations_checked += 1
                shared_pVs = set()
                for bgc in constellation:
                    shared_pVs |= bgc.possible_values
                if len(shared_pVs) == len(constellation):
                    for bgcR in bgCs:
                        if bgcR not in constellation and not bgcR.isResolved:
                            # b4 = len(bgcR.possible_values)
                            bgcR.reduce_possible_values(shared_pVs)
                            # aftr = len(bgcR.possible_values)
                            # self.main_gui.reductions_by_constellation.value += b4 - aftr

    def reduction_by_constellation_optimized_set(self, cell_set):
        cell_set = [bgc for bgc in cell_set if not bgc.isResolved]
        if cell_set:
            min_con_size = min(
                [len(bgc.possible_values) for bgc in cell_set])
            max_con_size = len(cell_set)
            possible_constellations = list()
            for size in range(min_con_size, max_con_size):
                possible_constellations += combinations(cell_set, size)
            for constellation in possible_constellations:
                self.constellations_checked += 1
                shared_pVs = set()
                for bgc in constellation:
                    shared_pVs |= bgc.possible_values
                if len(shared_pVs) == len(constellation):
                    for bgcR in cell_set:
                        if bgcR not in constellation and bgcR.isUnresolved:
                            b4 = len(bgcR.possible_values)
                            bgcR.reduce_possible_values(shared_pVs)
                            aftr = len(bgcR.possible_values)
                            self.reductions_by_constellations += b4 - aftr


class Solver:

    def __init__(self, main_gui, board):
        self.main_gui = main_gui
        self.board = board

    def solve(self):
        self.board.selected_cell = None
        match self.main_gui.selected_solving_algorithm:
            case Algorithm.SOLVING.ELIMINATION_BY_CONSTELLATION:
                if self.board.isUniquelySolvable:
                    self.reduction_by_constellation()
            case Algorithm.SOLVING.ELIMINATION_OPTIMIZED:
                if self.board.isUniquelySolvable:
                    self.reduction_by_constellation_optimized()
            case Algorithm.SOLVING.BACKTRACKING:
                self.board.update_all_board_references()
                self.main_gui.current_alg_type = Algorithm.SOLVING.BACKTRACKING
                self.backtracking(unresolved_cells=self.board.unresolved_cells)
            case Algorithm.SOLVING.BACKTRACKING_OPTIMIZED:
                self.main_gui.current_alg_type = Algorithm.SOLVING.ELIMINATION_BY_SUDOKU
                self.reduction_by_sudoku()
                self.board.update_all_board_references()
                self.backtracking(unresolved_cells=self.board.unresolved_cells)

    def backtracking(self, unresolved_cells):
        for c in unresolved_cells:
            for value in c.possible_values:
                if c.is_valid(value=value):
                    c.set_resolved_value(value=value)
                    self.main_gui.recursions_checked_label.value += 1
                    unresolved_cells.remove(c)
                    if self.backtracking(unresolved_cells=unresolved_cells):
                        return True
                    c.clear_value()
                    unresolved_cells.append(c)
            return False
        self.main_gui.current_alg_type = None
        return True

    def reduction_by_constellation(self):
        self.main_gui.current_alg_type = Algorithm.SOLVING.ELIMINATION_BY_CONSTELLATION
        while not self.board.isSolved:
            for cell in self.board.cells:
                if cell.isResolved or cell.isGiven:
                    continue
                else:
                    self.reduction_by_constellation_set(cell_set=cell.containing_row)
                    self.reduction_by_constellation_set(cell_set=cell.containing_col)
                    self.reduction_by_constellation_set(cell_set=cell.containing_box)
        self.main_gui.current_alg_type = None

    def reduction_by_constellation_optimized(self):
        while not self.board.isSolved:
            self.main_gui.current_alg_type = Algorithm.SOLVING.ELIMINATION_BY_SUDOKU
            self.reduction_by_sudoku()
            self.main_gui.current_alg_type = Algorithm.SOLVING.ELIMINATION_BY_CONSTELLATION
            self.board.update_all_board_references()
            for row in self.board.cell_rows_unresolved:
                self.reduction_by_constellation_optimized_set(cell_set=row)
            self.board.update_all_board_references()
            for col in self.board.cell_cols_unresolved:
                self.reduction_by_constellation_optimized_set(cell_set=col)
            self.board.update_all_board_references()
            for box in self.board.cell_boxes_unresolved:
                self.reduction_by_constellation_optimized_set(cell_set=box)
        self.main_gui.current_alg_type = None

    def reduction_by_sudoku(self):
        self.board.update_all_board_references()
        rgCs = [c for c in self.board.cells if c.isResolved or c.isGiven]  # get all resolved or given cells
        for rgC in rgCs:
            if rgC is not self.board.selected_cell:
                rgC.configure(fg_color=cd["light-grey"])
            uCs = self.get_unresolved_cells_in_rcb(
                rgC)  # get a set of unresolved cells in the same row, col and box of the resolved or given cells
            for uC in uCs:  # Reduce the unresolved cell's pVs by the value of the resolved or given cell
                b4 = len(uC.possible_values)
                uC.reduce_possible_values({rgC.value})
                aftr = len(uC.possible_values)
                self.main_gui.reductions_by_sudoku_label.value += b4 - aftr
                if uC.isResolved:
                    rgCs.append(uC)
            if rgC is not self.board.selected_cell:
                rgC.configure(fg_color=cd["dark-grey"])
        if self.board.isSolved:  # This check gets done in case we solve the board with only this method
            return

    def get_unresolved_cells_in_rcb(self, cell):
        """
        cell passed in here should be resolved or given.
        Returns a set of all cells in the same row, col and box as the passed in cell
        """
        return {cell for lst in [cell.containing_row,
                                 cell.containing_col,
                                 cell.containing_box] for cell in lst if cell.isUnresolved}

    def reduction_by_constellation_optimized_set(self, cell_set):
        cell_set = [c for c in cell_set if c.isUnresolved]
        if cell_set:
            min_con_size = min(
                [len(c.possible_values) for c in cell_set])
            max_con_size = len(cell_set)
            possible_constellations = list()
            for size in range(min_con_size, max_con_size):
                possible_constellations += combinations(cell_set, size)
            for constellation in possible_constellations:
                shared_pVs = set()
                for c in constellation:
                    self.main_gui.constellations_checked_label.value += 1
                    if c is not self.board.selected_cell:
                        c.configure(fg_color=cd["grey"])
                        ctk_sleep(main_gui=self.main_gui, t=0.1,
                                  alg_speed_multiplier=self.main_gui.alg_speed_multiplier)
                    shared_pVs |= c.possible_values
                if len(shared_pVs) == len(constellation):
                    for c in constellation:
                        if c is not self.board.selected_cell:
                            c.configure(fg_color=cd["light-grey"])
                            ctk_sleep(main_gui=self.main_gui, t=0.1,
                                      alg_speed_multiplier=self.main_gui.alg_speed_multiplier)
                    for c in constellation:
                        if c is not self.board.selected_cell:
                            c.configure(fg_color=cd["dark-grey"])
                            ctk_sleep(main_gui=self.main_gui, t=0.1,
                                      alg_speed_multiplier=self.main_gui.alg_speed_multiplier)
                    for cR in cell_set:
                        if cR not in constellation and cR.isUnresolved:
                            b4 = len(cR.possible_values)
                            cR.reduce_possible_values(shared_pVs)
                            aftr = len(cR.possible_values)
                            self.main_gui.reductions_by_constellation_label.value += b4 - aftr
                else:
                    for c in constellation:
                        if c is not self.board.selected_cell:
                            c.configure(fg_color=cd["dark-grey"])
                            ctk_sleep(main_gui=self.main_gui, t=0.1,
                                      alg_speed_multiplier=self.main_gui.alg_speed_multiplier)

    def reduction_by_constellation_set(self, cell_set):
        """bg_cells is a set of nine BackgroundCells"""
        if cell_set:
            possible_constellations = list()
            # get all possible combinations
            for size in range(1, 9):
                possible_constellations += combinations(cell_set, size)
            for constellation in possible_constellations:
                shared_pVs = set()
                for c in constellation:
                    self.main_gui.constellations_checked_label.value += 1
                    if c is not self.board.selected_cell:
                        c.configure(fg_color=cd["grey"])
                        ctk_sleep(main_gui=self.main_gui, t=0.1,
                                  alg_speed_multiplier=self.main_gui.alg_speed_multiplier)
                    shared_pVs |= c.possible_values
                if len(shared_pVs) == len(constellation):
                    for c in constellation:
                        if c is not self.board.selected_cell:
                            c.configure(fg_color=cd["light-grey"])
                            ctk_sleep(main_gui=self.main_gui, t=0.1,
                                      alg_speed_multiplier=self.main_gui.alg_speed_multiplier)
                    for c in constellation:
                        if c is not self.board.selected_cell:
                            c.configure(fg_color=cd["dark-grey"])
                            ctk_sleep(main_gui=self.main_gui, t=0.1,
                                      alg_speed_multiplier=self.main_gui.alg_speed_multiplier)
                    for cR in cell_set:
                        if cR not in constellation and cR.isUnresolved:
                            b4 = len(cR.possible_values)
                            cR.reduce_possible_values(shared_pVs)
                            aftr = len(cR.possible_values)
                            self.main_gui.reductions_by_constellation_label.value += b4 - aftr
                else:
                    for c in constellation:
                        if c is not self.board.selected_cell:
                            c.configure(fg_color=cd["dark-grey"])
                            ctk_sleep(main_gui=self.main_gui, t=0.1,
                                      alg_speed_multiplier=self.main_gui.alg_speed_multiplier)


class Generator:

    def __init__(self, main_gui, board):
        self.main_gui = main_gui
        self.board = board

    def generate(self):
        self.board.selected_cell = None
        self.board.clear_board()
        self.board.update_all_board_references()
        #  Later on there will also be different generating algorithms
        self.main_gui.current_alg_type = Algorithm.GENERATING.FILLING
        self.fill_board_by_backtracking()
        self.standard_reduction()

    def fill_board_by_backtracking(self):
        self.main_gui.recursions_made_label.value += 1
        for c in self.board.cells:
            if c.isUnresolved:
                rVs = list(range(1, 10))
                random.shuffle(rVs)
                for rV in rVs:
                    if c.is_valid(rV):
                        c.set_given_value(rV)
                        if self.fill_board_by_backtracking():
                            return True
                        c.clear_value()
                return False
        return True

    def standard_reduction(self):
        self.main_gui.current_alg_type = Algorithm.GENERATING.REDUCING
        goal_digit_count = self.get_difficulty_range()
        given_digits = 81
        while given_digits != goal_digit_count:
            gCs = [gc for gc in self.board.cells if gc.isGiven]
            random.shuffle(gCs)
            board_b4 = [c.value for c in self.board.cells]
            for gC in gCs:  # Remove cell values one by one
                self.main_gui.reductions_checked_label.value += 1
                if given_digits == goal_digit_count:  # until digit count is met
                    self.main_gui.current_alg_type = None
                    return
                rmvd_val = gC.value
                gC.clear_value()
                given_digits -= 1
                if not self.board.isUniquelySolvable:  # Check if the board is still solvable
                    gC.set_given_value(rmvd_val)
                    given_digits += 1
            board_aftr = [c.value for c in self.board.cells]
            if board_b4 == board_aftr:  # Break when the board hasn't changed
                break
        self.main_gui.current_alg_type = None

    def get_difficulty_range(self):
        match self.main_gui.difficulty:
            case Difficulty.EASY:
                return random.randrange(39, 43)
            case Difficulty.MEDIUM:
                return random.randrange(34, 38)
            case Difficulty.HARD:
                return random.randrange(29, 33)
            case Difficulty.EXTREME:
                return random.randrange(19, 23)


class BackgroundGenerator:

    def __init__(self, main_gui):
        self.main_gui = main_gui
        self.bg_board = BackgroundBoardNbN(main_gui.board)

    def update_board(self):
        """
        fetches a new copy of the current main board
        """
        self.bg_board = BackgroundBoardNbN(self.main_gui.board)

    def generate(self):
        self.bg_board.og_board.clear_board()
        self.update_board()
        self.fill_board_by_backtracking()
        self.standard_reduction()
        self.bg_board.print_back_to_og_board_as_given()

    def fill_board_by_backtracking(self):
        self.main_gui.recursions_made_label.value += 1
        for c in self.bg_board.cells:
            if not c.isResolved:
                rVs = list(range(1, 10))
                random.shuffle(rVs)
                for rV in rVs:
                    if c.is_valid(rV):
                        c.set_value(rV)
                        if self.fill_board_by_backtracking():
                            return True
                        c.clear_value()
                return False
        return True

    def standard_reduction(self):
        self.main_gui.current_alg_type = Algorithm.GENERATING.REDUCING
        goal_digit_count = self.get_difficulty_range()
        given_digits = 81
        while given_digits != goal_digit_count:
            rbgCs = [bgC for bgC in self.bg_board.cells if bgC.isResolved]
            random.shuffle(rbgCs)
            board_b4 = [c.value for c in self.bg_board.cells]
            for rbgC in rbgCs:  # Remove cell values one by one
                self.main_gui.reductions_checked_label.value += 1
                if given_digits == goal_digit_count:  # until digit count is met
                    self.main_gui.current_alg_type = None
                    return
                rmvd_val = rbgC.value
                rbgC.clear_value()
                given_digits -= 1
                if not self.bg_board.isUniquelySolvable:  # Check if the board is still solvable
                    rbgC.set_value(rmvd_val)
                    given_digits += 1
            board_aftr = [bgC.value for bgC in self.bg_board.cells]
            if board_b4 == board_aftr:  # Break when the board hasn't changed
                break

    def get_difficulty_range(self):
        match self.main_gui.difficulty:
            case Difficulty.EASY:
                return random.randrange(39, 43)
            case Difficulty.MEDIUM:
                return random.randrange(34, 38)
            case Difficulty.HARD:
                return random.randrange(29, 33)
            case Difficulty.EXTREME:
                return random.randrange(19, 23)


class MainGUI:

    def __init__(self):
        self.root = ctk.CTk()
        self.root.geometry("2304x1296")
        self.root.title("sdk solver")
        # values

        self._current_alg_type = None
        self.alg_speed_multiplier = 50
        self.show_alg = False
        self.difficulty = Difficulty.HARD
        self.solve_until = SolveType.COMPLETE

        self.main_frame = ctk.CTkFrame(master=self.root)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=3)
        self.main_frame.columnconfigure(2, weight=3)
        self.main_frame.rowconfigure(0, weight=2)
        self.main_frame.rowconfigure(1, weight=7)
        self.main_frame.pack(fill="both", expand=True)

        # Board
        self.board = Board9x9(master=self.main_frame, main_gui=self, width=500)
        self.generator = Generator(main_gui=self, board=self.board)
        self.background_generator = BackgroundGenerator(main_gui=self)
        self.solver = Solver(main_gui=self, board=self.board)
        self.background_solver = BackgroundSolver(main_gui=self)
        self.board.grid(row=1, rowspan=1, column=0, padx=(25, 25), pady=(50, 50), sticky="n")

        # Buttons
        self.button_frame = ctk.CTkFrame(master=self.main_frame)
        self.button_frame.grid(row=1, column=2, columnspan=1, rowspan=1, sticky="news", padx=50, pady=(25, 50))

        self.solve_button_frame = ctk.CTkFrame(master=self.main_frame)
        self.solve_button_frame.grid(row=0, column=2, columnspan=1, rowspan=1, sticky="news", padx=50, pady=(50, 25))

        self.solve_button = ctk.CTkButton(
            master=self.solve_button_frame,
            text="Solve", font=("Arial", 20),
            text_color=cd["black"],
            height=50,
            corner_radius=30,
            border_width=3,
            border_color=cd["dark-grey"],
            hover_color=cd["pale-yellow"],
            fg_color=cd["banana"],
            command=self.solve
        )
        self.solve_button.grid(row=0, column=0, padx=50, pady=50)

        self.choose_solving_alg_combo_box = ctk.CTkComboBox(
            master=self.solve_button_frame,
            values=[
                Algorithm.SOLVING.ELIMINATION_BY_CONSTELLATION.value,
                Algorithm.SOLVING.ELIMINATION_OPTIMIZED.value,
                Algorithm.SOLVING.BACKTRACKING.value,
                Algorithm.SOLVING.BACKTRACKING_OPTIMIZED.value
            ],
            state="readonly",
            border_color=cd["black"],
            fg_color=cd["grey"],
            button_color=cd["black"],
            text_color=cd["black"],
            dropdown_text_color=cd["black"],
            dropdown_fg_color=cd["grey"],
            command=self.on_alg_change
        )
        self.selected_solving_algorithm = Algorithm.SOLVING.ELIMINATION_OPTIMIZED
        self.choose_solving_alg_combo_box.set(self.selected_solving_algorithm.value)
        self.choose_solving_alg_combo_box.grid(row=0, column=1, padx=50, pady=50)

        self.solve_until_combo_box = ctk.CTkComboBox(
            master=self.solve_button_frame,
            values=[opt.value for opt in SolveType],
            state="readonly",
            command=self.on_solve_until_change
        )
        self.solve_until_combo_box.set(SolveType.COMPLETE.value)
        self.solve_until_combo_box.grid(row=0, column=2, padx=50, pady=50)

        # Other Buttons

        self.alg_speed_label = ctk.CTkLabel(
            master=self.button_frame,
            text="Algorithm Speed",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.alg_speed_label.grid(row=0, column=0, padx=50, pady=(50, 50))

        self.alg_speed_slider = ctk.CTkSlider(
            master=self.button_frame,
            button_color=cd["black"],
            progress_color=cd["banana"],
            button_hover_color=cd["pale-yellow"],
            from_=1,
            to=100,
            command=lambda value: self.on_slider_change(value=value))
        self.alg_speed_slider.grid(row=0, column=1, padx=(110, 50), pady=(35, 15))

        self.show_alg_label = ctk.CTkLabel(
            master=self.button_frame,
            text="Show Algorithm",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.show_alg_label.grid(row=1, column=0, padx=50, pady=25)

        self.check_box_helper_var = ctk.BooleanVar(value=False)
        self.show_alg_check_box = ctk.CTkCheckBox(
            master=self.button_frame,
            text="",
            checkmark_color=cd["black"],
            fg_color=cd["banana"],
            border_color=cd["black"],
            hover_color=cd["grey"],
            variable=self.check_box_helper_var,
            command=self.on_checked_change
        )
        self.show_alg_check_box.grid(row=1, column=1, padx=(187, 50), pady=25)

        self.generate_new_board_button = ctk.CTkButton(
            master=self.button_frame,
            text="Generate",
            font=("Arial", 20),
            text_color=cd["black"],
            height=50,
            corner_radius=30,
            border_width=3,
            border_color=cd["dark-grey"],
            hover_color=cd["pale-yellow"],
            fg_color=cd["banana"],
            command=self.generate
        )
        self.generate_new_board_button.grid(row=2, column=0, padx=50, pady=25)

        self.choose_difficulty_combo_box = ctk.CTkComboBox(
            master=self.button_frame,
            values=[diff.name for diff in Difficulty],
            state="readonly",
            border_color=cd["black"],
            fg_color=cd["grey"],
            button_color=cd["black"],
            text_color=cd["black"],
            dropdown_text_color=cd["black"],
            dropdown_fg_color=cd["grey"],
            command=self.on_diff_change
        )
        self.choose_difficulty_combo_box.set(Difficulty.HARD.name)
        self.choose_difficulty_combo_box.grid(row=2, column=1, padx=(110, 50), pady=25)

        self.clear_board_button = ctk.CTkButton(
            master=self.button_frame,
            text="Clear Board",
            font=("Arial", 20),
            text_color=cd["black"],
            height=50,
            corner_radius=30,
            border_width=3,
            border_color=cd["dark-grey"],
            hover_color=cd["pale-yellow"],
            fg_color=cd["banana"],
            command=self.board.clear_board
        )
        self.clear_board_button.grid(row=3, column=0, padx=50, pady=25)

        self.reset_board_button = ctk.CTkButton(
            master=self.button_frame,
            text="Reset Board",
            font=("Arial", 20),
            text_color=cd["black"],
            height=50,
            corner_radius=30,
            border_width=3,
            border_color=cd["dark-grey"],
            fg_color=cd["banana"],
            hover_color=cd["pale-yellow"],
            command=self.board.reset_board
        )
        self.reset_board_button.grid(row=3, column=1, padx=(110, 50), pady=25)

        ######### Statistics 4 Nerds ######################################################################
        ###################################################################################################

        self.statistics_4_nerds_frame = ctk.CTkFrame(master=self.main_frame)
        self.statistics_4_nerds_frame.grid(row=0, column=1, columnspan=1, rowspan=2, sticky="news", padx=(0, 10),
                                           pady=(50, 50))

        self.current_alg_label = ctk.CTkLabel(
            master=self.statistics_4_nerds_frame,
            text="Current algorithm:",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.current_alg_label.grid(row=0, padx=(25, 0), pady=(35, 25), sticky="w")

        self.alg_progress_bar = ctk.CTkProgressBar(
            self.statistics_4_nerds_frame,
            progress_color=cd["banana"]
        )
        self.alg_progress_bar.set(0)
        self.alg_progress_bar.grid(row=1, padx=(25, 0), pady=(10, 0), sticky="we")

        self.solving_alg_label = ctk.CTkLabel(
            master=self.statistics_4_nerds_frame,
            text="Solving algorithm stats:",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.solving_alg_label.grid(row=2, padx=(25, 0), pady=(35, 25), sticky="w")

        self.reductions_by_constellation_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Reductions made constellation",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.reductions_by_constellation_label.value = 0
        self.reductions_by_constellation_label.grid(row=3, padx=(25, 0), pady=(10, 0), sticky="w")

        self.reductions_by_sudoku_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Reductions made by sudoku",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.reductions_by_sudoku_label.value = 0
        self.reductions_by_sudoku_label.grid(row=4, padx=(25, 0), pady=(10, 0), sticky="w")

        self.constellations_checked_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Constellations checked",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.constellations_checked_label.value = 0
        self.constellations_checked_label.grid(row=5, padx=(25, 0), pady=(10, 0), sticky="w")

        self.recursions_checked_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Recursions checked",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.recursions_checked_label.value = 0
        self.recursions_checked_label.grid(row=6, padx=(25, 0), pady=(10, 0), sticky="w")

        self.generating_alg_label = ctk.CTkLabel(
            master=self.statistics_4_nerds_frame,
            text="Generating Algorithm stats:",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.generating_alg_label.grid(row=7, padx=(25, 0), pady=(35, 25), sticky="w")

        self.recursions_made_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Recursions made",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.recursions_made_label.value = 0
        self.recursions_made_label.grid(row=8, padx=(25, 0), pady=(10, 0), sticky="w")

        self.reductions_checked_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Reductions checked",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.reductions_checked_label.value = 0
        self.reductions_checked_label.grid(row=9, padx=(25, 0), pady=(10, 0), sticky="w")

        self.board_label = ctk.CTkLabel(
            master=self.statistics_4_nerds_frame,
            text="Board:",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.board_label.grid(row=10, padx=(25, 0), pady=(35, 25), sticky="w")

        self.board_unique_solution_label = ctk.CTkLabel(
            master=self.statistics_4_nerds_frame,
            text="Has no unique solution",
            text_color=cd["red"],
            font=("Arial", 20)
        )
        self.board_unique_solution_label.grid(row=11, padx=(25, 0), pady=(10, 0), sticky="w")

        self.board_solved_status_label = ctk.CTkLabel(
            master=self.statistics_4_nerds_frame,
            text="Not solved",
            text_color=cd["red"],
            font=("Arial", 20)
        )
        self.board_solved_status_label.grid(row=12, padx=(25, 0), pady=(10, 0), sticky="w")

        self.numbers_given_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Numbers given",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.numbers_given_label.value = 0
        self.numbers_given_label.grid(row=13, padx=(25, 0), pady=(10, 0), sticky="w")

        self.numbers_resolved_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Numbers resolved",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.numbers_resolved_label.value = 0
        self.numbers_resolved_label.grid(row=14, padx=(25, 0), pady=(10, 0), sticky="w")

        self.numbers_unresolved_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Numbers unresolved",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.numbers_unresolved_label.value = 81
        self.numbers_unresolved_label.grid(row=15, padx=(25, 0), pady=(10, 0), sticky="w")

        self.possible_values_remaining_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="possible values remaining",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        # self.possible_values_remaining_label.value = self.board.get_possible_value_count()
        self.possible_values_remaining_label.grid(row=16, padx=(25, 0), pady=(10, 0), sticky="w")

        self.cell_label = ctk.CTkLabel(
            master=self.statistics_4_nerds_frame,
            text="Cell:",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.cell_label.grid(row=17, padx=(25, 0), pady=(35, 25), sticky="w")

        self.cell_row_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Row",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.cell_row_label.grid(row=18, padx=(25, 0), pady=(10, 0), sticky="w")

        self.cell_col_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Col",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.cell_col_label.grid(row=19, padx=(25, 0), pady=(10, 0), sticky="w")

        self.cell_value_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Value",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.cell_value_label.grid(row=20, padx=(25, 0), pady=(10, 0), sticky="w")

        self.cell_pV_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="possible Values",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.cell_pV_label.grid(row=21, padx=(25, 0), pady=(10, 0), sticky="w")

        self.spacer_label = ctk.CTkLabel(
            master=self.statistics_4_nerds_frame,
            width=500,
            text=""
        )
        self.spacer_label.grid(row=22)

        self.root.bind("<Key>", self.on_key_press)

        self.root.mainloop()

    @property
    def current_alg_type(self):
        return self._current_alg_type

    @current_alg_type.setter
    def current_alg_type(self, alg_type):
        self._current_alg_type = alg_type
        print(self.current_alg_type)
        alg_label_handler(main_gui=self, alg_type=alg_type)

    def solve(self):
        if self.show_alg:
            self.solver.solve()
        else:
            self.background_solver.solve()

    def generate(self):
        print("generate")
        if self.show_alg:
            print("with generate")
            self.generator.generate()
        else:
            print("with bg generator")
            self.background_generator.generate()

    def on_key_press(self, event):
        if self.board.selected_cell:
            containing_row = self.board.selected_cell.containing_row
            containing_col = self.board.selected_cell.containing_col
            if event.keysym == "Up":
                for index, cell in enumerate(containing_col):
                    if cell == self.board.selected_cell:
                        if index == 0:
                            containing_col[8].invoke()
                        else:
                            containing_col[index - 1].invoke()
                        break
            elif event.keysym == "Down":
                for index, cell in enumerate(containing_col):
                    if cell == self.board.selected_cell:
                        if index == 8:
                            containing_col[0].invoke()
                        else:
                            containing_col[index + 1].invoke()
                        break
            elif event.keysym == "Left":
                for index, cell in enumerate(containing_row):
                    if cell == self.board.selected_cell:
                        if index == 0:
                            containing_row[8].invoke()
                        else:
                            containing_row[index - 1].invoke()
                        break
            elif event.keysym == "Right":
                for index, cell in enumerate(containing_row):
                    if cell == self.board.selected_cell:
                        if index == 8:
                            containing_row[0].invoke()
                        else:
                            containing_row[index + 1].invoke()
                        break
            elif event.char.isdigit() and event.char != '0':
                if int(event.char) == self.board.selected_cell.value:
                    self.board.selected_cell.clear_value()
                else:
                    self.board.selected_cell.set_given_value(value=int(event.char))
            elif event.keysym == "BackSpace":
                self.board.selected_cell.clear_value()

    def on_alg_change(self, choice):
        self.selected_solving_algorithm = next((alg for alg in Algorithm.SOLVING if alg.value == choice), None)

    def on_slider_change(self, value: float):
        self.alg_speed_multiplier = value
        print(self.alg_speed_multiplier)

    def on_checked_change(self):
        self.show_alg = self.check_box_helper_var.get()

    def on_diff_change(self, choice):
        self.difficulty = next((diff for diff in Difficulty if diff.name == choice), None)

    def on_solve_until_change(self, choice):
        self.solve_until = next((solve_type for solve_type in SolveType if solve_type.value == choice), None)
        print(self.solve_until.value)


if __name__ == "__main__":
    MainGUI()
