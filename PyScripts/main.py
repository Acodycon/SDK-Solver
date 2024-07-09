import random
from itertools import combinations
from Utils import SolveType, Difficulty, generate_board

from PyScripts import sudoku
import tkinter as tk
from typing import List, Tuple

UnsolvedBoard = [[None, None, 3, 1, None, None, None, None, 4],
                 [None, 1, None, None, 5, None, None, 9, None],
                 [2, None, None, None, None, 6, 5, None, None],
                 [3, None, 5, None, None, 8, 9, None, None],
                 [None, 7, None, None, 9, None, None, 3, None],
                 [None, None, 2, 3, None, None, None, None, 8],
                 [4, 6, None, None, 2, None, None, None, None],
                 [None, None, None, 6, None, 4, None, None, 3],
                 [None, 3, None, None, 8, None, None, None, None]]

empty_board = [[0, 0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0, 0]]


class SudokuCellButton(tk.Button):

    def __init__(self, sudoku_board: 'SudokuBoard', master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.isResolved = False
        self.sudoku_board = sudoku_board
        self._possible_values = {pV for pV in range(1, 10, 1)}
        self.value = None

    @property
    def possible_values(self):
        return self._possible_values

    @possible_values.setter
    def possible_values(self, value: set):
        self._possible_values = value
        if len(value) == 1:
            self.value = list(value)[0]

    def __str__(self):
        return f"value: {self.value}"

    def clear_value(self):
        self.config(text=" ")
        self.value = None
        self.isResolved = False
        self.possible_values = {pV for pV in range(1, 10, 1)}
        self.sudoku_board.check_solved_status()
        self.sudoku_board.isSolvable()

    def set_value_by_com(self, value):
        if self.sudoku_board.main_gui.show_alg:
            self.config(background="green")
            tksleep(.1 / self.sudoku_board.solve_speed_multiplier)
        self.config(text=str(value), fg="black")
        if self.sudoku_board.main_gui.show_alg:
            tksleep(.1 / self.sudoku_board.solve_speed_multiplier)
            self.config(background="#C1CDCD")
        self.value = value
        self.isResolved = True
        self.possible_values = {value}
        self.sudoku_board.check_solved_status()
        self.sudoku_board.isSolvable()

    def set_value_by_key_press(self, event):
        if event.char.isdigit() and event.char != '0':
            self.config(text=event.char, fg="black")
            self.value = int(event.char)
            self.isResolved = True
            self.possible_values = {int(event.char)}
        elif event.keysym == "BackSpace":
            self.config(text=" ", fg="black")
            self.value = None
            self.isResolved = False
            self.possible_values = {pV for pV in range(1, 10, 1)}
        self.sudoku_board.check_solved_status()
        self.sudoku_board.isSolvable()

    def reduce_possible_values(self, values: set):
        if self.sudoku_board.main_gui.show_alg:
            self.config(background="#00CD66")
            tksleep(0.01 / self.sudoku_board.solve_speed_multiplier)
        self.possible_values -= set(values)
        if len(list(self.possible_values)) == 1:
            if self.sudoku_board.main_gui.show_alg:
                self.config(background="#3D9140")
                tksleep(0.5 / self.sudoku_board.solve_speed_multiplier)
            self.value = list(self.possible_values)[0]
            self.config(text=str(self.value), fg="#0000CD")
            if self.sudoku_board.main_gui.show_alg:
                tksleep(0.5 / self.sudoku_board.solve_speed_multiplier)
                self.config(background="#C1CDCD")
            self.sudoku_board.isSolvable()
            self.isResolved = True
            if self.sudoku_board.solve_type == SolveType.NEXT_DIGIT:
                return True
            else:
                return self.sudoku_board.check_solved_status()
        else:
            if self.sudoku_board.main_gui.show_alg:
                self.config(background="#C1CDCD")
                tksleep(0.01 / self.sudoku_board.solve_speed_multiplier)
            if self.sudoku_board.solve_type == SolveType.NEXT_REDUCTION:
                return True
            else:
                return False


def tksleep(t):
    'emulating time.sleep(seconds)'
    ms = int(t * 1000)
    root = tk._get_default_root('sleep')
    var = tk.IntVar(root)
    root.after(ms, var.set, 1)
    root.wait_variable(var)


class SudokuBoard(tk.Frame):

    def __init__(self, main_gui: 'MainGUI', master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.main_gui = main_gui
        self.isSolved = False
        self.solve_type = SolveType.COMPLETE
        self.isGenerating = False

        self.solve_speed_multiplier = 1
        self.solve_is_running = False
        # Create a 9x9 grid of buttons and store them in a 2D list.
        self.selected_cell = None

        self.button_rows: List[List[SudokuCellButton]] = []
        self.button_cols = [[] for i in range(9)]
        self.button_boxes = [[] for i in range(9)]

        # Create 9 frames.
        self.frames = [[tk.Frame(master=self, borderwidth=1, relief="solid") for j in range(3)] for i in range(3)]
        for i, frame_row in enumerate(self.frames):
            for j, frame in enumerate(frame_row):
                frame.grid(row=i, column=j, padx=5, pady=5)  # Add some space between the frames

        # Create a 9x9 grid of buttons.
        for i in range(9):
            button_row: List[SudokuCellButton] = []
            for j in range(9):
                button = SudokuCellButton(master=self.frames[i // 3][j // 3], sudoku_board=self, text=" ",
                                          font=("Arial", 30), fg="#0000CD", width=3, height=1)
                button.config(background="#C1CDCD",
                              command=lambda btn=button, c_row=i, c_col=j: self.on_click(btn, c_row, c_col))
                button.grid(row=i % 3, column=j % 3)
                button_row.append(button)
                self.button_cols[j].append(button)
                self.button_boxes[(i // 3) * 3 + j // 3].append(button)
            self.button_rows.append(button_row)

    def on_click(self, btn, c_row, c_col):
        print(f"Button at row {c_row},"
              f" column {c_col} was clicked"
              f"\nvalue: {btn.value}"
              f"\npossible_values: {btn.possible_values}")
        # Leave a reference to the last cell selected
        self.selected_cell = btn
        # color relevant cells
        if not self.solve_is_running:
            box_containing_btn = []
            for box in self.button_boxes:
                if btn in box:
                    box_containing_btn = box
                    break
            for row, button_row in enumerate(self.button_rows):
                for col, button in enumerate(button_row):
                    if row == c_row and col == c_col:
                        btn.config(background="#007FFF")
                    elif row == c_row or col == c_col or button in box_containing_btn:
                        button.config(background="#00FFFF")
                    else:
                        button.config(background="#C1CDCD")

    def on_key_press(self, event):
        if self.selected_cell is not None:
            containing_col = next((col for col in self.button_cols if self.selected_cell in col), None)
            containing_row = next((row for row in self.button_rows if self.selected_cell in row), None)
            if event.keysym == "Up":
                for index, cell in enumerate(containing_col):
                    if cell == self.selected_cell:
                        if index == 0:
                            containing_col[8].invoke()
                        else:
                            containing_col[index - 1].invoke()
                        break
            elif event.keysym == "Down":
                for index, cell in enumerate(containing_col):
                    if cell == self.selected_cell:
                        if index == 8:
                            containing_col[0].invoke()
                        else:
                            containing_col[index + 1].invoke()
                        break
            elif event.keysym == "Left":
                for index, cell in enumerate(containing_row):
                    if cell == self.selected_cell:
                        if index == 0:
                            containing_row[8].invoke()
                        else:
                            containing_row[index - 1].invoke()
                        break
            elif event.keysym == "Right":
                for index, cell in enumerate(containing_row):
                    if cell == self.selected_cell:
                        if index == 8:
                            containing_row[0].invoke()
                        else:
                            containing_row[index + 1].invoke()
                        break
            elif event.keysym == "BackSpace" or (event.char.isdigit() and event.char != '0'):
                self.selected_cell.set_value_by_key_press(event)
                self.check_solved_status()
                self.check_move_legality()
                if self.isSolvable():
                    self.main_gui.is_solvable_label.config(text="Has a unique solution", fg="green")
                else:
                    self.main_gui.is_solvable_label.config(text="Has no unique solution", fg="red")

    def check_move_legality(self):
        pass

    def get_difficulty_range(self, difficulty: Difficulty):
        match difficulty:
            case Difficulty.EASY:
                return random.randrange(39, 43)
            case Difficulty.MEDIUM:
                return random.randrange(34, 38)
            case Difficulty.HARD:
                return random.randrange(29, 33)
            case Difficulty.EXTREME:
                return random.randrange(19, 23)

    def generate_new_board(self, difficulty: Difficulty):
        self.isGenerating = True
        self.clear_board()
        board = [[None for i in range(9)] for j in range(9)]
        self.solve_sudoku(board)
        self.reduce_board(difficulty=difficulty)

    def reduce_board(self, difficulty: Difficulty):
        self.isGenerating = False
        remaining_digits = 81
        goal_digit_count = self.get_difficulty_range(difficulty=difficulty)
        # Get all non-empty cells
        while remaining_digits != goal_digit_count:
            cells = [(i, j) for i in range(9) for j in range(9) if self.button_rows[i][j].value is not None]

            # Shuffle the cells to randomize which ones are emptied
            random.shuffle(cells)
            remaining_digits_before_loop = remaining_digits
            for (i, j) in cells:
                if remaining_digits == goal_digit_count:
                    return
                # Remove the number in the cell
                removed = self.button_rows[i][j].value
                if self.main_gui.show_alg:
                    self.button_rows[i][j].config(background="red")
                    tksleep(.1 / self.solve_speed_multiplier)
                self.button_rows[i][j].clear_value()
                if self.main_gui.show_alg:
                    tksleep(.1 / self.solve_speed_multiplier)
                    self.button_rows[i][j].config(background="#C1CDCD")
                remaining_digits -= 1

                # Check if the board still has a unique solution
                if not self.isSolvable():
                    # If not, put the number back
                    self.button_rows[i][j].set_value_by_com(removed)
                    remaining_digits += 1
            print(f"remaining digits: {remaining_digits}, goal digits: {goal_digit_count}")
            if remaining_digits == remaining_digits_before_loop:
                break

    def is_valid(self, board, row, col, num):
        # Check the number in the row
        for x in range(9):
            if board[row][x] == num:
                return False

        # Check the number in the column
        for x in range(9):
            if board[x][col] == num:
                return False

        # Check the number in the 3x3 square
        startRow = row - row % 3
        startCol = col - col % 3
        for i in range(3):
            for j in range(3):
                if board[i + startRow][j + startCol] == num:
                    return False
        return True

    def solve_sudoku(self, board):
        self.isGenerating = True
        print(f"solve_step: {self.isGenerating}")
        for i in range(9):
            for j in range(9):
                if board[i][j] is None:
                    random_numbers = list(range(1, 10))
                    random.shuffle(random_numbers)
                    for num in random_numbers:
                        if self.is_valid(board, i, j, num):
                            board[i][j] = num
                            self.button_rows[i][j].set_value_by_com(num)
                            if self.solve_sudoku(board):
                                return True
                            board[i][j] = None
                            if self.main_gui.show_alg:
                                self.button_rows[i][j].config(background="red")
                                tksleep(.1 / self.solve_speed_multiplier)
                            self.button_rows[i][j].clear_value()
                            if self.main_gui.show_alg:
                                tksleep(.1 / self.solve_speed_multiplier)
                                self.button_rows[i][j].config(background="#C1CDCD")
                    return False
        return True

    def decolor_board(self):
        for row in self.button_rows:
            for cell in row:
                cell.config(background="#C1CDCD")

    def reset_board(self):
        self.isGenerating = True
        for row in self.button_rows:
            for cell in row:
                if cell.cget('fg') == "#0000CD":
                    tksleep(0.01 / self.solve_speed_multiplier)
                    cell.clear_value()
        self.isGenerating = False

    def clear_board(self):
        self.isGenerating = True
        for row in self.button_rows:
            for cell in row:
                if cell.isResolved:
                    tksleep(0.01 / self.solve_speed_multiplier)
                    cell.clear_value()
        self.isGenerating = False
        self.isSolvable()
        self.check_solved_status()

    def on_scale_change(self, value):
        self.solve_speed_multiplier = float(value)

    def isSolvable(self):
        print(self.isGenerating)
        if not self.isGenerating:
            initialboard = [[cell.value for cell in self.button_rows[j]] for j in range(9)]
            board_copy = sudoku.SudokuBoard(initial_board=initialboard)
            board_copy.solve()
            if board_copy.isSolvable:
                self.main_gui.is_solvable_label.config(text="Has a unique Solution", fg="green")
            else:
                self.main_gui.is_solvable_label.config(text="Has no unique Solution", fg="red")
            return board_copy.isSolvable

    def solve_v2(self, solve_type: SolveType):
        self.solve_is_running = True
        self.selected_cell = None
        for row in self.button_rows:
            for button in row:
                button.config(background="#C1CDCD")
        self.solve_type = solve_type
        if self.isSolvable:
            while not self.isSolved:
                for index_row, row in enumerate(self.button_rows):
                    for index_col, cell in enumerate(row):
                        if cell.isResolved:
                            continue
                        else:
                            containing_row = row
                            resolved_values_in_row: set = {cell.value for cell in containing_row if cell.isResolved}
                            if resolved_values_in_row:  # if the set is empty this would be pointless
                                for cell_to_be_reduced in containing_row:
                                    if cell_to_be_reduced.isResolved:
                                        continue
                                    else:
                                        if cell_to_be_reduced.reduce_possible_values(resolved_values_in_row):
                                            return

                            containing_col = self.button_cols[index_col]
                            resolved_values_in_col = {cell.value for cell in containing_col if cell.isResolved}
                            if resolved_values_in_col:
                                for cell_to_be_reduced in containing_col:
                                    if cell_to_be_reduced.isResolved:
                                        continue
                                    else:
                                        if cell_to_be_reduced.reduce_possible_values(resolved_values_in_col):
                                            return

                            containing_box = self.button_boxes[(index_row // 3) * 3 + index_col // 3]
                            resolved_values_in_box = [cell.value for cell in containing_box if cell.isResolved]
                            if resolved_values_in_box:
                                for cell_to_be_reduced in containing_box:
                                    if cell_to_be_reduced.isResolved:
                                        continue
                                    else:
                                        if cell_to_be_reduced.reduce_possible_values(resolved_values_in_box):
                                            return

                            unresolved_cells_in_row = [cell for cell in containing_row if not cell.isResolved]
                            if unresolved_cells_in_row:
                                min_constellation_size = min(
                                    [len(cell.possible_values) for cell in unresolved_cells_in_row])
                                max_constellation_size = len(unresolved_cells_in_row) - 1
                                possible_constellations = []
                                for size in range(min_constellation_size, max_constellation_size + 1, 1):
                                    possible_constellations += combinations(unresolved_cells_in_row, size)
                                for combo in possible_constellations:
                                    set_of_shared_possible_digits = set()
                                    for cell_to_check in combo:
                                        if self.main_gui.show_alg:
                                            cell_to_check.config(background="#FF4040")
                                            tksleep(0.01 / self.solve_speed_multiplier)
                                        set_of_shared_possible_digits |= cell_to_check.possible_values
                                    if len(set_of_shared_possible_digits) == len(combo):
                                        if self.main_gui.show_alg:
                                            for cell_to_check in combo:
                                                cell_to_check.config(background="#ED9121")
                                                tksleep(0.01 / self.solve_speed_multiplier)
                                            for cell_to_check in combo:
                                                cell_to_check.config(background="#C1CDCD")
                                                tksleep(0.001 / self.solve_speed_multiplier)
                                        for cell_to_be_reduced in unresolved_cells_in_row:
                                            if cell_to_be_reduced not in combo and not cell_to_be_reduced.isResolved:
                                                # if self.main_gui.show_alg:
                                                #     cell_to_be_reduced.config(background="#FF4040")
                                                #     tksleep(0.01 / self.solve_speed_multiplier)
                                                #     cell_to_be_reduced.config(background="#ED9121")
                                                #     tksleep(0.01 / self.solve_speed_multiplier)
                                                if cell_to_be_reduced.reduce_possible_values(
                                                        set_of_shared_possible_digits):
                                                    return
                                                if [cell for cell in unresolved_cells_in_row if not cell.isResolved]:
                                                    continue
                                                # else:
                                                #     if self.main_gui.show_alg:
                                                #         cell_to_be_reduced.config(background="#C1CDCD")
                                                #         tksleep(0.001 / self.solve_speed_multiplier)
                                            # else:
                                            #     if self.main_gui.show_alg:
                                            #         cell_to_be_reduced.config(background="#C1CDCD")
                                            #         tksleep(0.001 / self.solve_speed_multiplier)
                                    # untint the cells when they are no valid reduction constellation
                                    if self.main_gui.show_alg:
                                        for cell_to_check in combo:
                                            cell_to_check.config(background="#C1CDCD")
                                            tksleep(0.001 / self.solve_speed_multiplier)

                            unresolved_cells_in_col = [cell for cell in containing_col if not cell.isResolved]
                            if unresolved_cells_in_col:
                                min_constellation_size = min(
                                    [len(cell.possible_values) for cell in unresolved_cells_in_col])
                                max_constellation_size = len(unresolved_cells_in_col) - 1
                                possible_constellations = []
                                for size in range(min_constellation_size, max_constellation_size + 1, 1):
                                    possible_constellations += combinations(unresolved_cells_in_col, size)
                                for combo in possible_constellations:
                                    set_of_shared_possible_digits = set()
                                    for cell_to_check in combo:
                                        if self.main_gui.show_alg:
                                            cell_to_check.config(background="#FF4040")
                                            tksleep(0.01 / self.solve_speed_multiplier)
                                        set_of_shared_possible_digits |= cell_to_check.possible_values
                                    if len(set_of_shared_possible_digits) == len(combo):
                                        if self.main_gui.show_alg:
                                            for cell_to_check in combo:
                                                cell_to_check.config(background="#ED9121")
                                                tksleep(0.01 / self.solve_speed_multiplier)
                                            for cell_to_check in combo:
                                                cell_to_check.config(background="#C1CDCD")
                                                tksleep(0.001 / self.solve_speed_multiplier)
                                        for cell_to_be_reduced in unresolved_cells_in_col:
                                            if cell_to_be_reduced not in combo and not cell_to_be_reduced.isResolved:
                                                # if self.main_gui.show_alg:
                                                #     cell_to_be_reduced.config(background="#FF4040")
                                                #     tksleep(0.01 / self.solve_speed_multiplier)
                                                #     cell_to_be_reduced.config(background="#ED9121")
                                                #     tksleep(0.01 / self.solve_speed_multiplier)
                                                if cell_to_be_reduced.reduce_possible_values(
                                                        set_of_shared_possible_digits):
                                                    return
                                                if [cell for cell in unresolved_cells_in_col if not cell.isResolved]:
                                                    continue
                                            #     else:
                                            #         if self.main_gui.show_alg:
                                            #             cell_to_be_reduced.config(background="#C1CDCD")
                                            #             tksleep(0.001 / self.solve_speed_multiplier)
                                            # else:
                                            #     if self.main_gui.show_alg:
                                            #         cell_to_be_reduced.config(background="#C1CDCD")
                                            #         tksleep(0.001 / self.solve_speed_multiplier)
                                    # untint the cells when they are no valid reduction constellation
                                    if self.main_gui.show_alg:
                                        for cell_to_check in combo:
                                            cell_to_check.config(background="#C1CDCD")
                                            tksleep(0.001 / self.solve_speed_multiplier)

                            unresolved_cells_in_box = [cell for cell in containing_box if not cell.isResolved]
                            if unresolved_cells_in_box:
                                min_constellation_size = min(
                                    [len(cell.possible_values) for cell in unresolved_cells_in_box])
                                max_constellation_size = len(unresolved_cells_in_box) - 1
                                possible_constellations = []
                                for size in range(min_constellation_size, max_constellation_size + 1, 1):
                                    possible_constellations += combinations(unresolved_cells_in_box, size)
                                for combo in possible_constellations:
                                    set_of_shared_possible_digits = set()
                                    for cell_to_check in combo:
                                        if self.main_gui.show_alg:
                                            cell_to_check.config(background="#FF4040")
                                            tksleep(0.01 / self.solve_speed_multiplier)
                                        set_of_shared_possible_digits |= cell_to_check.possible_values
                                    if len(set_of_shared_possible_digits) == len(combo):
                                        if self.main_gui.show_alg:
                                            for cell_to_check in combo:
                                                cell_to_check.config(background="#ED9121")
                                                tksleep(0.01 / self.solve_speed_multiplier)
                                            for cell_to_check in combo:
                                                cell_to_check.config(background="#C1CDCD")
                                                tksleep(0.001 / self.solve_speed_multiplier)
                                        for cell_to_be_reduced in unresolved_cells_in_box:
                                            if cell_to_be_reduced not in combo and not cell_to_be_reduced.isResolved:
                                                # if self.main_gui.show_alg:
                                                #     cell_to_be_reduced.config(background="#FF4040")
                                                #     tksleep(0.01 / self.solve_speed_multiplier)
                                                #     cell_to_be_reduced.config(background="#ED9121")
                                                #     tksleep(0.01 / self.solve_speed_multiplier)
                                                if cell_to_be_reduced.reduce_possible_values(
                                                        set_of_shared_possible_digits):
                                                    return
                                                if [cell for cell in unresolved_cells_in_box if not cell.isResolved]:
                                                    continue
                                            #     else:
                                            #         if self.main_gui.show_alg:
                                            #             cell_to_be_reduced.config(background="#C1CDCD")
                                            #             tksleep(0.001 / self.solve_speed_multiplier)
                                            # else:
                                            #     if self.main_gui.show_alg:
                                            #         cell_to_be_reduced.config(background="#C1CDCD")
                                            #         tksleep(0.001 / self.solve_speed_multiplier)
                                    # untint the cells when they are no valid reduction constellation
                                    if self.main_gui.show_alg:
                                        for cell_to_check in combo:
                                            cell_to_check.config(background="#C1CDCD")
                                            tksleep(0.001 / self.solve_speed_multiplier)
        else:
            self.solve_is_running = False

    def check_solved_status(self):
        for row in self.button_rows:
            for cell in row:
                if cell.value is None:
                    self.isSolved = False
                    self.main_gui.solve_status_label.config(text="Not Solved", fg="red")
                    return False
        self.isSolved = True
        self.solve_is_running = False
        self.main_gui.solve_status_label.config(text="Solved", fg="green")
        return True


class MainGUI:

    def __init__(self):
        # main application
        self.root = tk.Tk()
        # Window dimensions
        self.root.geometry("1920x1080")
        # Window Title
        self.root.title("Sudoku Solver")

        # UI take two
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=6)
        self.root.columnconfigure(2, weight=2)
        self.root.columnconfigure(3, weight=4)
        self.root.columnconfigure(4, weight=1)
        self.root.rowconfigure(0, weight=3)
        self.root.rowconfigure(1, weight=8)
        self.root.rowconfigure(2, weight=1)

        self.label_frame = tk.Frame(master=self.root)
        self.label_frame.columnconfigure(0, weight=1)
        self.label_frame.rowconfigure(0, weight=1)
        self.label_frame.rowconfigure(1, weight=1)
        self.label_frame.grid(row=0, column=1, sticky="we", padx=5, pady=5)

        self.button_frame = tk.Frame(self.root)
        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)
        self.button_frame.rowconfigure(0, weight=1)
        self.button_frame.rowconfigure(1, weight=1)
        self.button_frame.rowconfigure(2, weight=1)
        self.button_frame.rowconfigure(3, weight=1)
        self.button_frame.rowconfigure(4, weight=1)
        self.button_frame.rowconfigure(5, weight=1)
        self.button_frame.rowconfigure(6, weight=1)
        self.button_frame.rowconfigure(7, weight=1)
        self.button_frame.grid(row=1, column=3, sticky="news", padx=5, pady=5)

        # Define the Sudoku Grid
        self.board_frame = SudokuBoard(master=self.root, main_gui=self)
        self.board_frame.grid(row=1, column=1, sticky="w")

        # UI Elements other than the Board
        self.is_solvable_label = tk.Label(self.label_frame, text="No unique Solution", background="#FF7256",
                                          font=("Arial", 20), fg="red")
        self.is_solvable_label.grid(row=0, column=0, sticky="we")

        self.solve_status_label = tk.Label(self.label_frame, text="Not solved", background="#FF7256",
                                           font=("Arial", 20), fg="red")
        self.solve_status_label.grid(row=1, column=0, sticky="we")

        self.solve_button = tk.Button(master=self.button_frame, text="Solve", font=("Arial", 20))
        self.solve_button.config(
            command=lambda solve_type=SolveType.COMPLETE: self.board_frame.solve_v2(solve_type=solve_type))
        self.solve_button.grid(row=0, column=0, sticky="we")

        self.solve_until_next_digit = tk.Button(master=self.button_frame, text="Solve until next digit",
                                                font=("Arial", 20))
        self.solve_until_next_digit.config(
            command=lambda solve_type=SolveType.NEXT_DIGIT: self.board_frame.solve_v2(solve_type=solve_type))
        self.solve_until_next_digit.grid(row=1, column=0, sticky="we")

        self.solve_until_next_reduction = tk.Button(master=self.button_frame, text="Solve until next Reduction",
                                                    font=("Arial", 20), command=lambda
                solve_type=SolveType.NEXT_REDUCTION: self.board_frame.solve_v2(solve_type=solve_type))
        self.solve_until_next_reduction.grid(row=1, column=1, sticky="we")

        self.solve_speed_label = tk.Label(self.button_frame, text="Solving Speed", font=("Arial", 20))
        self.solve_speed_label.grid(row=2, column=0, sticky="we")

        self.solve_speed_scale = tk.Scale(self.button_frame, from_=1, to=10, orient=tk.HORIZONTAL,
                                          command=lambda value: self.board_frame.on_scale_change(value=value))
        self.solve_speed_scale.grid(row=2, column=1, sticky="we")

        self.show_algorithm_label = tk.Label(self.button_frame, text="Show Algorithm:", font=("Arial", 20))
        self.show_algorithm_label.grid(row=3, column=0, sticky="we")

        self.toggle_show_alg_button = tk.Button(self.button_frame, text="False", font=("Arial", 20), background="red",
                                                command=self.toggle_show_alg)
        self.toggle_show_alg_button.grid(row=3, column=1, sticky="we")
        self.show_alg = False

        self.clear_board_button = tk.Button(self.button_frame, text="Clear Board", font=("Arial", 20),
                                            command=self.board_frame.clear_board)
        self.clear_board_button.grid(row=4, column=0, sticky="we")

        self.reset_board_button = tk.Button(self.button_frame, text="Reset Board", font=("Arial", 20), command=self.board_frame.reset_board)
        self.reset_board_button.grid(row=4, column=1, sticky="we")

        self.difficulty = Difficulty.EASY
        self.generate_board_button = tk.Button(
            self.button_frame,
            text="Generate new Board",
            font=("Arial", 20),
            command=lambda: self.board_frame.generate_new_board(difficulty=self.difficulty))
        self.generate_board_button.grid(row=5, column=0, sticky="we")

        self.cycle_difficulty_button = tk.Button(self.button_frame, text="Easy", font=("Arial", 20),
                                                 command=self.cycle_difficulty)
        self.cycle_difficulty_button.grid(row=5, column=1, sticky="we")

        self.test_button = tk.Button(self.button_frame, command=generate_board)
        self.test_button.grid(row=6, column=0, sticky="we")

        # keyboard logic
        self.root.bind("<Key>", self.board_frame.on_key_press)

        self.root.mainloop()

    def cycle_difficulty(self):
        match self.difficulty:
            case Difficulty.EASY:
                self.difficulty = Difficulty.MEDIUM
                self.cycle_difficulty_button.config(text="Medium")
            case Difficulty.MEDIUM:
                self.difficulty = Difficulty.HARD
                self.cycle_difficulty_button.config(text="Hard")
            case Difficulty.HARD:
                self.difficulty = Difficulty.EXTREME
                self.cycle_difficulty_button.config(text="Extreme")
            case Difficulty.EXTREME:
                self.difficulty = Difficulty.EASY
                self.cycle_difficulty_button.config(text="Easy")

    def toggle_show_alg(self):
        self.show_alg = not self.show_alg
        new_color = "green" if self.show_alg else "red"
        new_text = "True" if self.show_alg else "False"
        self.toggle_show_alg_button.config(background=new_color, text=new_text)
        if not self.show_alg:
            self.board_frame.decolor_board()


def main():
    board = sudoku.SudokuBoard(UnsolvedBoard)
    #    board.print_row(1)
    #    board.print_col(4)
    #    board.print_box(3)
    #board.solve()
    MainGUI()