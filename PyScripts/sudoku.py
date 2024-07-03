from typing import Tuple
from typing import List
from itertools import combinations


class SudokuBoard:

    isSolvable = False
    isSolved = False

    def __init__(self, initial_board):
        self.boxes = [[] for i in range(9)]
        self.cols = [[] for i in range(9)]
        self.rows = [[SudokuCell(initial_board[j][i], (j, i), self) for i in range(9)] for j in range(9)]

    def solve(self):
        board_hasnt_changed_in_x_iterations = 0
        iter_count = 0
        while board_hasnt_changed_in_x_iterations < 5:
            print(f"iteration: {iter_count + 1}")
            board_before = [[cell.value for cell in self.rows[j]] for j in range(9)]
            for full_set in self.boxes:
                self.reduction_by_constellation(full_set)
            for full_set in self.rows:
                self.reduction_by_constellation(full_set)
            for full_set in self.cols:
                self.reduction_by_constellation(full_set)
            iter_count += 1
            if board_before == [[cell.value for cell in self.rows[j]] for j in range(9)]:
                board_hasnt_changed_in_x_iterations += 1
            else:
                board_hasnt_changed_in_x_iterations = 0
            self.print_board()
            if self.check_solved_status():
                self.isSolved = True
                self.isSolvable = True
                print(f"The board has been solved after {iter_count} iterations")
                break
        if self.check_solved_status():
            self.isSolved = True
            self.isSolvable = True
            print(f"The board has been solved after {iter_count} iterations")
        else:
            self.isSolved = False
            self.isSolvable = False
            print("The board is not uniquely solvable")

    def check_solved_status(self):
        for row in self.rows:
            for cell in row:
                if cell.value is None:
                    return False
        return True

    def print_board(self):
        for row in self.rows:
            print([cell.value for cell in row])

    def print_box(self, index: int):
        print("\n")
        print([cell.value for cell in self.boxes[index]])

    def print_row(self, index):
        print("\n")
        print([cell.value for cell in self.rows[index]])

    def print_col(self, index):
        print("\n")
        print([cell.value for cell in self.cols[index]])

    def reduction_by_constellation(self, full_set: List['SudokuCell']):
        unresolved_cells = [cell for cell in full_set]
        if unresolved_cells:
            min_constellation_size = min([len(cell.possible_values) for cell in unresolved_cells])
            max_constellation_size = len(unresolved_cells) - 1
            possible_constellations = []
            for size in range(min_constellation_size, max_constellation_size + 1, 1):
                possible_constellations += combinations(unresolved_cells, size)
            for combo in possible_constellations:
                set_of_shared_possible_digits = set()
                for cell in combo:
                    set_of_shared_possible_digits |= cell.possible_values
                if len(set_of_shared_possible_digits) == len(combo):
                    for cell_to_be_reduced in unresolved_cells:
                        if cell_to_be_reduced not in combo:
                            cell_to_be_reduced.possible_values -= set_of_shared_possible_digits


class SudokuCell:
    isResolved = False

    def __init__(self, value, coords: Tuple[int, int], board: SudokuBoard):
        self.value = value
        self.coords = coords
        self.board = board
        self.row = coords[0]
        self.col = coords[1]
        self.board.cols[self.col].append(self)
        self._possible_values = {pV for pV in range(1, 10, 1)}
        if self.row < 3:
            if self.col < 3:
                self.box = 0
            elif self.col < 6:
                self.box = 1
            else:
                self.box = 2
        elif self.row < 6:
            if self.col < 3:
                self.box = 3
            elif self.col < 6:
                self.box = 4
            else:
                self.box = 5
        else:
            if self.col < 3:
                self.box = 6
            elif self.col < 6:
                self.box = 7
            else:
                self.box = 8
        self.board.boxes[self.box].append(self)
        if value is not None:
            self.possible_values: set = {value}
            self.isResolved = True

    @property
    def possible_values(self):
        return self._possible_values

    @possible_values.setter
    def possible_values(self, value: set):
        self._possible_values = value
        if len(value) == 1:
            self.value = list(value)[0]

    def __str__(self):
        return str(self.coords)

# ELIMINATION BY CONSTELLATION
# If a set of unresolved boxes in one 1-9 set (Box,Row,Col) have a constellation of 'n' cells that all share 'n' different digits that are possible, all other cells in that 1-9 set can now longer be these n digits
# Step 1: get a list of cells that are unresolved
# Step 2: iterate over every possible combination of these cells
#           Where:    n = number of unresolved cells
#                     c = size of the constellation
#                     1 < c < n  -> c is at least 2 and at most n - 1
#                     We can narrow down c even further:
#                         c has to be at least as big as the minimum number of possible digits of any cell in the set
#                         meaning that if there is a cell in the set that has 3 different options and every other cell also has at least three different options, than c has to be at least 3
#           Step 2.1: Find the lower bound for c
#               Iterate over the unresolved cells and look what the lowest number of possible digits is, which than dictates what c is going to be
#           Step 2.2: go over every possible constellation and check if the set of possible digits for all contained cells is equal to 'c'
#
