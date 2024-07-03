from itertools import combinations
import time

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

    def set_value_by_com(self):
        self.config(text=str(list(self.possible_values)[0]), fg="#0000CD")
        self.value = list(self.possible_values)[0]
        self.isResolved = True

    def reduce_possible_values(self, values: set):
        self.possible_values -= set(values)
        if len(list(self.possible_values)) == 1:
            self.config(background="#3D9140")
            tksleep(0.5)
            self.value = list(self.possible_values)[0]
            self.config(text=str(self.value), fg="#0000CD")
            self.isResolved = True
            tksleep(0.5)
            self.config(background="#C1CDCD")
            tksleep(0.0001)
            return self.sudoku_board.check_solved_status()
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
                button = SudokuCellButton(master=self.frames[i // 3][j // 3], sudoku_board=self, text=" ", font=("Arial", 30), fg="#0000CD", width=3, height=1)
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
                if self.isSolvable:
                    self.main_gui.is_solvable_label.config(text="Has a unique solution", fg="green")
                else:
                    self.main_gui.is_solvable_label.config(text="Has no unique solution", fg="red")


    def check_move_legality(self):
        pass
    def on_scale_change(self, value):
        self.solve_speed_multiplier = float(value)
    @property
    def isSolvable(self):
        initialboard = [[cell.value for cell in self.button_rows[j]] for j in range(9)]
        print(initialboard)
        board_copy = sudoku.SudokuBoard(initial_board=initialboard)
        board_copy.solve()
        return board_copy.isSolvable

    def solve_v2(self, step_by_step):
        self.solve_is_running = True
        self.selected_cell = None
        for row in self.button_rows:
            for button in row:
                button.config(background="#C1CDCD")

        if True:
            while not self.isSolved:
                for index_row, row in enumerate(self.button_rows):
                    for index_col, cell in enumerate(row):
                        if cell.isResolved:
                            continue
                        else:
                            containing_row = row
                            resolved_values_in_row: set = {cell.value for cell in containing_row if cell.isResolved}
                            if resolved_values_in_row: # if the set is empty this would be pointless
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
                                min_constellation_size = min([len(cell.possible_values) for cell in unresolved_cells_in_row])
                                max_constellation_size = len(unresolved_cells_in_row) - 1
                                possible_constellations = []
                                for size in range(min_constellation_size, max_constellation_size + 1, 1):
                                    possible_constellations += combinations(unresolved_cells_in_row, size)
                                for combo in possible_constellations:
                                    set_of_shared_possible_digits = set()
                                    for cell_to_check in combo:
                                        cell_to_check.config(background="#FF4040")
                                        tksleep(0.01 / self.solve_speed_multiplier)
                                        set_of_shared_possible_digits |= cell_to_check.possible_values
                                    if len(set_of_shared_possible_digits) == len(combo):
                                        for cell_to_check in combo:
                                            cell_to_check.config(background="#ED9121")
                                            tksleep(0.01 / self.solve_speed_multiplier)
                                        for cell_to_check in combo:
                                            cell_to_check.config(background="#C1CDCD")
                                            tksleep(0.001 / self.solve_speed_multiplier)
                                        for cell_to_be_reduced in unresolved_cells_in_row:
                                            if cell_to_be_reduced not in combo and not cell_to_be_reduced.isResolved:
                                                cell_to_be_reduced.config(background="#FF4040")
                                                tksleep(0.01 / self.solve_speed_multiplier)
                                                cell_to_be_reduced.config(background="#ED9121")
                                                tksleep(0.01 / self.solve_speed_multiplier)
                                                if cell_to_be_reduced.reduce_possible_values(set_of_shared_possible_digits):
                                                    return
                                                if [cell for cell in unresolved_cells_in_row if not cell.isResolved]:
                                                    continue
                                                else:
                                                    cell_to_be_reduced.config(background="#C1CDCD")
                                                    tksleep(0.001 / self.solve_speed_multiplier)
                                            else:
                                                cell_to_be_reduced.config(background="#C1CDCD")
                                                tksleep(0.001 / self.solve_speed_multiplier)
                                    # untint the cells when they are no valid reduction constellation
                                    for cell_to_check in combo:
                                        cell_to_check.config(background="#C1CDCD")
                                        tksleep(0.001 / self.solve_speed_multiplier)

                            unresolved_cells_in_col = [cell for cell in containing_col if not cell.isResolved]
                            if unresolved_cells_in_col:
                                min_constellation_size = min([len(cell.possible_values) for cell in unresolved_cells_in_col])
                                max_constellation_size = len(unresolved_cells_in_col) - 1
                                possible_constellations = []
                                for size in range(min_constellation_size, max_constellation_size + 1, 1):
                                    possible_constellations += combinations(unresolved_cells_in_col, size)
                                for combo in possible_constellations:
                                    set_of_shared_possible_digits = set()
                                    for cell_to_check in combo:
                                        cell_to_check.config(background="#FF4040")
                                        tksleep(0.01 / self.solve_speed_multiplier)
                                        set_of_shared_possible_digits |= cell_to_check.possible_values
                                    if len(set_of_shared_possible_digits) == len(combo):
                                        for cell_to_check in combo:
                                            cell_to_check.config(background="#ED9121")
                                            tksleep(0.01 / self.solve_speed_multiplier)
                                        for cell_to_check in combo:
                                            cell_to_check.config(background="#C1CDCD")
                                            tksleep(0.001 / self.solve_speed_multiplier)
                                        for cell_to_be_reduced in unresolved_cells_in_col:
                                            if cell_to_be_reduced not in combo and not cell_to_be_reduced.isResolved:
                                                cell_to_be_reduced.config(background="#FF4040")
                                                tksleep(0.01 / self.solve_speed_multiplier)
                                                cell_to_be_reduced.config(background="#ED9121")
                                                tksleep(0.01 / self.solve_speed_multiplier)
                                                if cell_to_be_reduced.reduce_possible_values(set_of_shared_possible_digits):
                                                    return
                                                if [cell for cell in unresolved_cells_in_col if not cell.isResolved]:
                                                    continue
                                                else:
                                                    cell_to_be_reduced.config(background="#C1CDCD")
                                                    tksleep(0.001 / self.solve_speed_multiplier)
                                            else:
                                                cell_to_be_reduced.config(background="#C1CDCD")
                                                tksleep(0.001 / self.solve_speed_multiplier)
                                    # untint the cells when they are no valid reduction constellation
                                    for cell_to_check in combo:
                                        cell_to_check.config(background="#C1CDCD")
                                        tksleep(0.001 / self.solve_speed_multiplier)

                            unresolved_cells_in_box = [cell for cell in containing_box if not cell.isResolved]
                            if unresolved_cells_in_box:
                                min_constellation_size = min([len(cell.possible_values) for cell in unresolved_cells_in_box])
                                max_constellation_size = len(unresolved_cells_in_box) - 1
                                possible_constellations = []
                                for size in range(min_constellation_size, max_constellation_size + 1, 1):
                                    possible_constellations += combinations(unresolved_cells_in_box, size)
                                for combo in possible_constellations:
                                    set_of_shared_possible_digits = set()
                                    for cell_to_check in combo:
                                        cell_to_check.config(background="#FF4040")
                                        tksleep(0.01 / self.solve_speed_multiplier)
                                        set_of_shared_possible_digits |= cell_to_check.possible_values
                                    if len(set_of_shared_possible_digits) == len(combo):
                                        for cell_to_check in combo:
                                            cell_to_check.config(background="#ED9121")
                                            tksleep(0.01 / self.solve_speed_multiplier)
                                        for cell_to_check in combo:
                                            cell_to_check.config(background="#C1CDCD")
                                            tksleep(0.001 / self.solve_speed_multiplier)
                                        for cell_to_be_reduced in unresolved_cells_in_box:
                                            if cell_to_be_reduced not in combo and not cell_to_be_reduced.isResolved:
                                                cell_to_be_reduced.config(background="#FF4040")
                                                tksleep(0.01 / self.solve_speed_multiplier)
                                                cell_to_be_reduced.config(background="#ED9121")
                                                tksleep(0.01 / self.solve_speed_multiplier)
                                                if cell_to_be_reduced.reduce_possible_values(set_of_shared_possible_digits):
                                                    return
                                                if [cell for cell in unresolved_cells_in_box if not cell.isResolved]:
                                                    continue
                                                else:
                                                    cell_to_be_reduced.config(background="#C1CDCD")
                                                    tksleep(0.001 / self.solve_speed_multiplier)
                                            else:
                                                cell_to_be_reduced.config(background="#C1CDCD")
                                                tksleep(0.001 / self.solve_speed_multiplier)
                                    # untint the cells when they are no valid reduction constellation
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

        # Define the Sudoku Grid
        self.board_frame = SudokuBoard(master=self.root, main_gui=self)

        self.board_frame.place(x=200, y=200)

        # UI Elements other than the Board
        self.is_solvable_label = tk.Label(self.root, text="No unique Solution", font=("Arial", 20), fg="red")
        self.is_solvable_label.place(x=440, y=100)

        self.solve_status_label = tk.Label(self.root, text="Not solved", font=("Arial", 20), fg="red")
        self.solve_status_label.place(x=440, y=130)

        self.solve_button = tk.Button(text="Solve", font=("Arial", 30), width=10, height=2)
        self.solve_button.config(command=lambda sbs=False: self.board_frame.solve_v2(step_by_step=sbs))
        self.solve_button.place(x=1200, y=200)

        self.solve_step_by_step_button = tk.Button(text="Solve step by step", font=("Arial", 30), width=15, height=2)
        self.solve_step_by_step_button.config(command=lambda sbs=True: self.board_frame.solve_v2(step_by_step=sbs))
        self.solve_step_by_step_button.place(x=1200, y=400)

        self.solve_speed_scale = tk.Scale(self.root, from_=1, to=10, orient=tk.HORIZONTAL, width=15, command=lambda value: self.board_frame.on_scale_change(value=value))
        self.solve_speed_scale.place(x=1200, y=350)
        # keyboard logic
        self.root.bind("<Key>", self.board_frame.on_key_press)

        self.root.mainloop()


def main():
    board = sudoku.SudokuBoard(UnsolvedBoard)
    #    board.print_row(1)
    #    board.print_col(4)
    #    board.print_box(3)
    #board.solve()
    MainGUI()


if __name__ == "__main__":
    main()
