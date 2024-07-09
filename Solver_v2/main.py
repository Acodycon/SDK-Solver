from itertools import combinations

import customtkinter as ctk
import random

from PyScripts import sudoku
from Solver_v3.Utils import Difficulty, SolveType, Algorithm, get_difficulty_range, ValueLabel
from Themes.colors import color_dict as cd
import Solver_v2.Sudoku as Sudoku

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def ctk_sleep(main_gui, t, alg_speed_multiplier):
    """emulating time.sleep(seconds)"""
    ctk_instance = main_gui.root
    ms = int(t * 1000 / alg_speed_multiplier)
    var = ctk.BooleanVar(ctk_instance, value=False)
    ctk_instance.after(ms, var.set, True)
    ctk_instance.wait_variable(var)


def print_board_back(main_gui):
    if main_gui.board_copy:
        main_gui.board_copy.print_back_to_og_board()


def copy_board(main_gui, board):
    board_copy = Sudoku.BackgroundBoardNbN(board=board)
    main_gui.board_copy = board_copy
    board_copy.print_board()
    board_copy.solve_alg_backtracking()
    board_copy.print_board()


def alg_progress_bar_handler(main_gui, progress):
    main_gui.alg_progress_bar.set(progress)


def alg_label_handler(main_gui, alg_type):
    if alg_type is None:
        main_gui.alg_is_running_label.configure(text="No Algorithm is currently running")
    else:
        main_gui.alg_is_running_label.configure(text=alg_type.value)


def solve_v3(main_gui, board):
    if board.selected_cell:
        board.selected_cell.deselect()
    no_change_iter_count = 0
    n_of_pV_before_solve = board.get_possible_value_count()
    main_gui.possible_values_remaining_label.value = n_of_pV_before_solve
    while True:
        main_gui.current_alg_type = Algorithm.SOLVING.ELIMINATION_BY_SUDOKU
        board_before = [[cell.value for cell in board.cell_rows[j]] for j in range(9)]
        for index_row, row in enumerate(board.cell_rows):
            for index_col, cell in enumerate(row):
                if cell.isResolved:
                    continue
                else:
                    containing_row = row
                    resolved_values_in_row = {cell.value for cell in containing_row if cell.isResolved}
                    if resolved_values_in_row:  # if the set is empty this would be pointless
                        for cell_to_be_reduced in containing_row:
                            if cell_to_be_reduced.isResolved:
                                continue
                            else:
                                if main_gui.show_alg:
                                    cell_to_be_reduced.configure(fg_color=cd["grey"])
                                    ctk_sleep(main_gui=main_gui, t=0.1,
                                              alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                # if we resolve the cell other cells in the current loop get also checked for the newly resolved cells value
                                if cell_to_be_reduced.reduce_possible_values(values=resolved_values_in_row, n_of_pV_before_solve=n_of_pV_before_solve):
                                    resolved_values_in_row |= cell_to_be_reduced.possible_values
                                else:
                                    if main_gui.show_alg:
                                        cell_to_be_reduced.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                    containing_col = cell.containing_col
                    resolved_values_in_col = {cell.value for cell in containing_col if cell.isResolved}
                    if resolved_values_in_col:
                        for cell_to_be_reduced in containing_col:
                            if cell_to_be_reduced.isResolved:
                                continue
                            else:
                                if main_gui.show_alg:
                                    cell_to_be_reduced.configure(fg_color=cd["grey"])
                                    ctk_sleep(main_gui=main_gui, t=0.1,
                                              alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                if cell_to_be_reduced.reduce_possible_values(values=resolved_values_in_col, n_of_pV_before_solve=n_of_pV_before_solve):
                                    resolved_values_in_col |= cell_to_be_reduced.possible_values
                                else:
                                    if main_gui.show_alg:
                                        cell_to_be_reduced.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)

                    containing_box = cell.containing_box
                    resolved_values_in_box = {cell.value for cell in containing_box if cell.isResolved}
                    if resolved_values_in_box:
                        for cell_to_be_reduced in containing_box:
                            if cell_to_be_reduced.isResolved:
                                continue
                            else:
                                if main_gui.show_alg:
                                    cell_to_be_reduced.configure(fg_color=cd["grey"])
                                    ctk_sleep(main_gui=main_gui, t=0.1,
                                              alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                if cell_to_be_reduced.reduce_possible_values(values=resolved_values_in_box, n_of_pV_before_solve=n_of_pV_before_solve):
                                    resolved_values_in_box |= cell_to_be_reduced.possible_values
                                else:
                                    if main_gui.show_alg:
                                        cell_to_be_reduced.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
        main_gui.current_alg_type = Algorithm.SOLVING.ELIMINATION_BY_CONSTELLATION
        for index_row, row in enumerate(board.cell_rows):
            for index_col, cell in enumerate(row):
                if cell.isResolved:
                    continue
                else:
                    containing_row = row
                    containing_col = cell.containing_col
                    containing_box = cell.containing_box
                    unresolved_cells_in_row = [cell for cell in containing_row if not cell.isResolved]
                    if unresolved_cells_in_row:
                        min_constellation_size = min(
                            [len(cell.possible_values) for cell in unresolved_cells_in_row])
                        max_constellation_size = len(unresolved_cells_in_row) - 1
                        possible_constellations = []
                        for size in range(min_constellation_size, max_constellation_size + 1):
                            possible_constellations += combinations(unresolved_cells_in_row, size)
                        for combo in possible_constellations:
                            set_of_shared_possible_digits = set()
                            main_gui.constellations_checked_label.value += 1
                            for cell_to_check in combo:
                                if main_gui.show_alg:
                                    cell_to_check.configure(fg_color=cd["grey"])
                                    ctk_sleep(main_gui=main_gui, t=0.1,
                                              alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                set_of_shared_possible_digits |= cell_to_check.possible_values
                            if len(set_of_shared_possible_digits) == len(combo):
                                if main_gui.show_alg:
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["light-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                for cell_to_be_reduced in unresolved_cells_in_row:
                                    if cell_to_be_reduced not in combo and not cell_to_be_reduced.isResolved:
                                        cell_to_be_reduced.reduce_possible_values(values=set_of_shared_possible_digits, n_of_pV_before_solve=n_of_pV_before_solve)
                                        if [cell for cell in unresolved_cells_in_row if not cell.isResolved]:
                                            break  # set a bool flag to break out of the combo in constellations loop
                            else:
                                if main_gui.show_alg:
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                    unresolved_cells_in_col = [cell for cell in containing_col if not cell.isResolved]
                    if unresolved_cells_in_col:
                        min_constellation_size = min(
                            [len(cell.possible_values) for cell in unresolved_cells_in_col])
                        max_constellation_size = len(unresolved_cells_in_col) - 1
                        possible_constellations = []
                        for size in range(min_constellation_size, max_constellation_size + 1, 1):
                            possible_constellations += combinations(unresolved_cells_in_col, size)
                        for combo in possible_constellations:
                            main_gui.constellations_checked_label.value += 1
                            set_of_shared_possible_digits = set()
                            for cell_to_check in combo:
                                if main_gui.show_alg:
                                    cell_to_check.configure(fg_color=cd["grey"])
                                    ctk_sleep(main_gui=main_gui, t=0.1,
                                              alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                set_of_shared_possible_digits |= cell_to_check.possible_values
                            if len(set_of_shared_possible_digits) == len(combo):
                                if main_gui.show_alg:
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["light-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                for cell_to_be_reduced in unresolved_cells_in_col:
                                    if cell_to_be_reduced not in combo and not cell_to_be_reduced.isResolved:
                                        cell_to_be_reduced.reduce_possible_values(values=set_of_shared_possible_digits, n_of_pV_before_solve=n_of_pV_before_solve)
                                        if [cell for cell in unresolved_cells_in_col if not cell.isResolved]:
                                            break  # set a bool flag to break out of the combo in constellations loop
                            else:
                                if main_gui.show_alg:
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                    unresolved_cells_in_box = [cell for cell in containing_box if not cell.isResolved]
                    if unresolved_cells_in_box:
                        min_constellation_size = min(
                            [len(cell.possible_values) for cell in unresolved_cells_in_box])
                        max_constellation_size = len(unresolved_cells_in_box) - 1
                        possible_constellations = []
                        for size in range(min_constellation_size, max_constellation_size + 1, 1):
                            possible_constellations += combinations(unresolved_cells_in_box, size)
                        for combo in possible_constellations:
                            main_gui.constellations_checked_label.value += 1
                            set_of_shared_possible_digits = set()
                            for cell_to_check in combo:
                                if main_gui.show_alg:
                                    cell_to_check.configure(fg_color=cd["grey"])
                                    ctk_sleep(main_gui=main_gui, t=0.1,
                                              alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                set_of_shared_possible_digits |= cell_to_check.possible_values
                            if len(set_of_shared_possible_digits) == len(combo):
                                if main_gui.show_alg:
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["light-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                for cell_to_be_reduced in unresolved_cells_in_box:
                                    if cell_to_be_reduced not in combo and not cell_to_be_reduced.isResolved:
                                        cell_to_be_reduced.reduce_possible_values(values=set_of_shared_possible_digits, n_of_pV_before_solve=n_of_pV_before_solve)
                                        if [cell for cell in unresolved_cells_in_box if not cell.isResolved]:
                                            break  # set a bool flag to break out of the combo in constellations loop
                            else:
                                if main_gui.show_alg:
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)

        board_after = [[cell.value for cell in board.cell_rows[j]] for j in range(9)]
        if board_after == board_before:
            no_change_iter_count += 1
            if no_change_iter_count == 2:
                alg_progress_bar_handler(main_gui=main_gui, progress=1)
                main_gui.current_alg_type = None
                main_gui.root.after(100, alg_progress_bar_handler(main_gui=main_gui, progress=0))
                return
        else:
            no_change_iter_count = 0


def solve_backtracking(main_gui, board):
    alg_label_handler(main_gui=main_gui, alg_type=Algorithm.SOLVING.BACKTRACKING)
    main_gui.current_alg_type = Algorithm.SOLVING.BACKTRACKING
    main_gui.recursions_checked_label.value += 1
    empty_cells = board.get_unresolved_cells()
    for try_cell in empty_cells:
        for num in try_cell.possible_values:
            if try_cell.is_valid(num):
                try_cell.set_value_for_opmzd_bcktrckng(value=num)
                if solve_backtracking(main_gui=main_gui, board=board):
                    return True
                try_cell.clear_value_for_opmzd_bcktrckng()
        return False
    main_gui.current_alg_type = None
    return True


def reduce_all_possible_values(main_gui, board):
    """reduction by soduko"""
    n_of_pV_before_solve = board.get_possible_value_count()
    alg_label_handler(main_gui=main_gui, alg_type=Algorithm.SOLVING.ELIMINATION_BY_SUDOKU)
    main_gui.current_alg_type = Algorithm.SOLVING.ELIMINATION_BY_SUDOKU
    unresolved_cells = board.get_unresolved_cells()
    for unresolved_cell in unresolved_cells:
        impossible_values_for_unresolved_cell = set()
        for pV in range(1, 10):
            if not unresolved_cell.is_valid(pV):
                impossible_values_for_unresolved_cell |= {pV}
        unresolved_cell.reduce_values_for_opmzd_bcktrckng(impossible_values_for_unresolved_cell)
    main_gui.current_alg_type = None


def optimized_elimination(main_gui, board):
    n_of_pV_before_solve = board.get_possible_value_count()
    alg_label_handler(main_gui=main_gui, alg_type=Algorithm.SOLVING.ELIMINATION_OPTIMIZED)
    main_gui.current_alg_type = Algorithm.SOLVING.ELIMINATION_OPTIMIZED
    while not board.is_solved():
        unresolved_cells = board.get_unresolved_cells()
        for unresolved_cell in unresolved_cells:
            impossible_values_for_unresolved_cell = set()
            for pV in range(1, 10):
                if not unresolved_cell.is_valid(pV):
                    impossible_values_for_unresolved_cell |= {pV}
            unresolved_cell.reduce_possible_values(values=impossible_values_for_unresolved_cell, n_of_pV_before_solve=n_of_pV_before_solve)
        break_out = False
        for row in board.cell_rows:
            break_out = False
            for cell in row:
                if cell.isResolved:
                    continue
                else:
                    containing_row = row
                    containing_col = cell.containing_col
                    containing_box = cell.containing_box
                    unresolved_cells_in_row = [cell for cell in containing_row if not cell.isResolved]
                    if unresolved_cells_in_row:
                        min_constellation_size = min(
                            [len(cell.possible_values) for cell in unresolved_cells_in_row])
                        max_constellation_size = len(unresolved_cells_in_row) - 1
                        possible_constellations = []
                        for size in range(min_constellation_size, max_constellation_size + 1):
                            possible_constellations += combinations(unresolved_cells_in_row, size)
                        for combo in possible_constellations:
                            set_of_shared_possible_digits = set()
                            main_gui.constellations_checked_label.value += 1
                            for cell_to_check in combo:
                                if main_gui.show_alg:
                                    cell_to_check.configure(fg_color=cd["grey"])
                                    ctk_sleep(main_gui=main_gui, t=0.1,
                                              alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                set_of_shared_possible_digits |= cell_to_check.possible_values
                            if len(set_of_shared_possible_digits) == len(combo):
                                if main_gui.show_alg:
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["light-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                for cell_to_be_reduced in unresolved_cells_in_row:
                                    if cell_to_be_reduced not in combo and not cell_to_be_reduced.isResolved:
                                        cell_to_be_reduced.reduce_possible_values(values=set_of_shared_possible_digits, n_of_pV_before_solve=n_of_pV_before_solve)
                                        if [cell for cell in unresolved_cells_in_row if not cell.isResolved]:
                                            break_out = True
                                            break  # set a bool flag to break out of the combo in constellations loop
                            else:
                                if main_gui.show_alg:
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                            if break_out:
                                break
                    unresolved_cells_in_col = [cell for cell in containing_col if not cell.isResolved]
                    if unresolved_cells_in_col:
                        min_constellation_size = min(
                            [len(cell.possible_values) for cell in unresolved_cells_in_col])
                        max_constellation_size = len(unresolved_cells_in_col) - 1
                        possible_constellations = []
                        for size in range(min_constellation_size, max_constellation_size + 1, 1):
                            possible_constellations += combinations(unresolved_cells_in_col, size)
                        for combo in possible_constellations:
                            main_gui.constellations_checked_label.value += 1
                            set_of_shared_possible_digits = set()
                            for cell_to_check in combo:
                                if main_gui.show_alg:
                                    cell_to_check.configure(fg_color=cd["grey"])
                                    ctk_sleep(main_gui=main_gui, t=0.1,
                                              alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                set_of_shared_possible_digits |= cell_to_check.possible_values
                            if len(set_of_shared_possible_digits) == len(combo):
                                if main_gui.show_alg:
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["light-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                for cell_to_be_reduced in unresolved_cells_in_col:
                                    if cell_to_be_reduced not in combo and not cell_to_be_reduced.isResolved:
                                        cell_to_be_reduced.reduce_possible_values(values=set_of_shared_possible_digits, n_of_pV_before_solve=n_of_pV_before_solve)
                                        if [cell for cell in unresolved_cells_in_col if not cell.isResolved]:
                                            break  # set a bool flag to break out of the combo in constellations loop
                            else:
                                if main_gui.show_alg:
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                    unresolved_cells_in_box = [cell for cell in containing_box if not cell.isResolved]
                    if unresolved_cells_in_box:
                        min_constellation_size = min(
                            [len(cell.possible_values) for cell in unresolved_cells_in_box])
                        max_constellation_size = len(unresolved_cells_in_box) - 1
                        possible_constellations = []
                        for size in range(min_constellation_size, max_constellation_size + 1, 1):
                            possible_constellations += combinations(unresolved_cells_in_box, size)
                        for combo in possible_constellations:
                            main_gui.constellations_checked_label.value += 1
                            set_of_shared_possible_digits = set()
                            for cell_to_check in combo:
                                if main_gui.show_alg:
                                    cell_to_check.configure(fg_color=cd["grey"])
                                    ctk_sleep(main_gui=main_gui, t=0.1,
                                              alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                set_of_shared_possible_digits |= cell_to_check.possible_values
                            if len(set_of_shared_possible_digits) == len(combo):
                                if main_gui.show_alg:
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["light-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                                for cell_to_be_reduced in unresolved_cells_in_box:
                                    if cell_to_be_reduced not in combo and not cell_to_be_reduced.isResolved:
                                        cell_to_be_reduced.reduce_possible_values(values=set_of_shared_possible_digits, n_of_pV_before_solve=n_of_pV_before_solve)
                                        if [cell for cell in unresolved_cells_in_box if not cell.isResolved]:
                                            break  # set a bool flag to break out of the combo in constellations loop
                            else:
                                if main_gui.show_alg:
                                    for cell_to_check in combo:
                                        cell_to_check.configure(fg_color=cd["dark-grey"])
                                        ctk_sleep(main_gui=main_gui, t=0.1,
                                                  alg_speed_multiplier=main_gui.alg_speed_multiplier)
                if break_out:
                    break
            if break_out:
                break
    alg_progress_bar_handler(main_gui=main_gui, progress=1)
    main_gui.current_alg_type = None
    alg_label_handler(main_gui=main_gui, alg_type=None)
    main_gui.root.after(100, alg_progress_bar_handler(main_gui=main_gui, progress=0))


def reset_board(main_gui, board):
    print("reset board")
    main_gui.current_alg_type = Algorithm.CLEARING.RESETTING
    main_gui.recursions_checked_label.value = 0
    main_gui.reductions_by_constellation_label.value = 0
    main_gui.constellations_checked_label.value = 0
    solved_cells = []
    for row in board.cell_rows:  # Gets all cells to be cleared in one list, to enable progressbar tracking
        for cell in row:
            if cell.cget('text_color') == cd["banana"]:
                solved_cells.append(cell)
    for index, cell in enumerate(solved_cells):
        cell.clear_value()
        # set progress bar
        progress = index / len(solved_cells) - 1
        alg_progress_bar_handler(main_gui=main_gui, progress=progress)
    main_gui.current_alg_type = None


def clear_board(main_gui, board):
    print("clear board")
    main_gui.current_alg_type = Algorithm.CLEARING.CLEARING
    main_gui.recursions_checked_label.value = 0
    main_gui.numbers_given_label.value = 0
    main_gui.numbers_unresolved_label.value = 81
    main_gui.recursions_made_label.value = 0
    main_gui.reductions_checked_label.value = 0
    main_gui.reductions_by_constellation_label.value = 0
    main_gui.constellations_checked_label.value = 0
    resolved_cells = []
    for row in board.cell_rows:  # Gets all cells to be cleared in one list, to enable progressbar tracking
        for cell in row:
            if cell.isResolved:
                resolved_cells.append(cell)
    for index, cell in enumerate(resolved_cells):
        cell.clear_value()
        # set progress bar
        progress = index / len(resolved_cells) - 1
        alg_progress_bar_handler(main_gui=main_gui, progress=progress)
    main_gui.current_alg_type = None


def generate(main_gui, board, diff):
    print("generate")
    if board.selected_cell:
        board.selected_cell.deselect()
    clear_board(main_gui=main_gui, board=board)
    main_gui.current_alg_type = Algorithm.GENERATING.FILLING
    fill_board(main_gui, board)
    reduce_board(main_gui=main_gui, board=board, diff=diff)


def reduce_board(main_gui, board, diff):
    main_gui.current_alg_type = Algorithm.GENERATING.REDUCING
    remaining_digits = 81
    goal_digit_count = get_difficulty_range(diff=diff)
    # Get all non-empty cells
    while remaining_digits != goal_digit_count:
        cells = [(i, j) for i in range(9) for j in range(9) if board.cell_rows[i][j].value is not None]

        # Shuffle the cells to randomize which ones are emptied
        random.shuffle(cells)
        remaining_digits_before_loop = remaining_digits
        board_before = [[cell.value for cell in board.cell_rows[j]] for j in range(9)]
        for (i, j) in cells:
            main_gui.reductions_checked_label.value += 1
            cell = board.cell_rows[i][j]
            if remaining_digits == goal_digit_count:
                alg_progress_bar_handler(main_gui=main_gui, progress=0)  # reset progress bar after algorithm is finished
                main_gui.current_alg_type = None
                return
            # Remove the number in the cell
            removed = cell.value
            if main_gui.show_alg:
                ctk_sleep(main_gui=main_gui, t=0.1, alg_speed_multiplier=main_gui.alg_speed_multiplier)
            cell.clear_value()
            # set progress bar
            progress = 3/4 + ((81 - remaining_digits) / (81 - goal_digit_count)) * 1/4
            print(f"progress: {progress}, remaining: {remaining_digits}, goal: {goal_digit_count}")
            alg_progress_bar_handler(main_gui=main_gui, progress=progress)
            if main_gui.show_alg:
                ctk_sleep(main_gui=main_gui, t=0.1, alg_speed_multiplier=main_gui.alg_speed_multiplier)
            remaining_digits -= 1

            # Check if the board still has a unique solution
            if not isSolvable(board):
                # If not, put the number back
                cell.set_value_by_com_generating(removed)
                remaining_digits += 1
        if remaining_digits == remaining_digits_before_loop:
            alg_progress_bar_handler(main_gui=main_gui, progress=1)
            break
    alg_progress_bar_handler(main_gui=main_gui, progress=0)  # reset progress bar after algorithm is finished
    main_gui.current_alg_type = None


def fill_board(main_gui, board):
    main_gui.recursions_made_label.value += 1
    progress = board.get_fill_status() * 3/4
    alg_progress_bar_handler(main_gui=main_gui, progress=progress)
    for i in range(9):
        for j in range(9):
            if board.cell_rows[i][j].value is None:
                random_numbers = list(range(1, 10))
                random.shuffle(random_numbers)
                for num in random_numbers:
                    if board.cell_rows[i][j].is_valid(value=num):
                        if main_gui.show_alg:
                            ctk_sleep(main_gui=main_gui, t=0.1, alg_speed_multiplier=main_gui.alg_speed_multiplier)
                        board.cell_rows[i][j].set_value_by_com_generating(num)
                        if fill_board(main_gui=main_gui, board=board):
                            return True
                        if main_gui.show_alg:
                            ctk_sleep(main_gui=main_gui, t=0.1, alg_speed_multiplier=main_gui.alg_speed_multiplier)
                        board.cell_rows[i][j].clear_value()
                        if main_gui.show_alg:
                            ctk_sleep(main_gui=main_gui, t=0.1, alg_speed_multiplier=main_gui.alg_speed_multiplier)
                return False
    return True


class MainGUI:

    def __init__(self):
        self.root = ctk.CTk()
        self.root.geometry("2304x1296")

        # values

        self._current_alg_type = None
        self.alg_speed_multiplier = 1
        self.show_alg = False
        self.difficulty = Difficulty.EASY
        self.solve_until = SolveType.COMPLETE

        self.main_frame = ctk.CTkFrame(master=self.root)
        # self.main_frame.configure(fg_color="#E3CF57")  Color = Banana
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=3)
        self.main_frame.columnconfigure(2, weight=3)
        self.main_frame.rowconfigure(0, weight=2)
        self.main_frame.rowconfigure(1, weight=7)
        self.main_frame.pack(fill="both", expand=True)

        # Board
        self.board = Sudoku.Board9x9(master=self.main_frame, main_gui=self, width=500)
        self.board.grid(row=1, column=0, padx=25, pady=(25, 50))

        # Labels associated with the Board
        self.board_extension_frame = ctk.CTkFrame(master=self.main_frame)
        self.board_extension_frame.grid(row=0, column=0, columnspan=1, padx=50, pady=(25, 0))

        self.board_unique_solution_label = ctk.CTkLabel(
            master=self.board_extension_frame,
            text="Does not have a unique solution",
            text_color=cd["red"],
            font=("Arial", 20)
        )
        self.board_unique_solution_label.grid(row=0, column=0, sticky="nw", padx=(10, 10), pady=(10, 10))

        self.board_solved_status_label = ctk.CTkLabel(
            master=self.board_extension_frame,
            text="Solved Status Label",
            font=("Arial", 20)
        )
        self.board_solved_status_label.grid(row=1, column=0, sticky="sw", padx=(10, 10), pady=(10, 10))

        self.alg_is_running_label = ctk.CTkLabel(
            master=self.board_extension_frame,
            width=300,
            text="No Algorithm is currently running",
            font=("Arial", 20)
        )
        self.alg_is_running_label.grid(row=0, column=1, sticky="ne", padx=(480, 10), pady=(10, 10))

        self.alg_progress_bar = ctk.CTkProgressBar(
            self.board_extension_frame,
            progress_color=cd["banana"]
        )
        self.alg_progress_bar.set(0)
        self.alg_progress_bar.grid(row=1, column=1, sticky="e", padx=(480, 10), pady=(10, 10))

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
                Algorithm.SOLVING.BACKTRACKING.value,
                Algorithm.SOLVING.BACKTRACKING_OPTIMIZED.value,
                Algorithm.SOLVING.ELIMINATION_BY_CONSTELLATION.value,
                Algorithm.SOLVING.ELIMINATION_OPTIMIZED.value
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
        self.selected_solving_algorithm = Algorithm.SOLVING.BACKTRACKING
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
        self.alg_speed_label.grid(row=0, column=0, padx=50, pady=(50, 25))

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
            command=lambda: generate(main_gui=self, board=self.board, diff=self.difficulty)
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
        self.choose_difficulty_combo_box.set(Difficulty.EASY.name)
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
            command=lambda: clear_board(main_gui=self, board=self.board)
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
            command=lambda: reset_board(main_gui=self, board=self.board)
        )
        self.reset_board_button.grid(row=3, column=1, padx=(110, 50), pady=25)

        self.board_copy = None

        self.test_aglorithms_button = ctk.CTkButton(
            master=self.button_frame,
            text="Copy Board and solve",
            font=("Arial", 20),
            text_color=cd["black"],
            height=50,
            corner_radius=30,
            border_width=3,
            border_color=cd["dark-grey"],
            fg_color=cd["banana"],
            hover_color=cd["pale-yellow"],
            command=lambda: copy_board(main_gui=self, board=self.board)
        )
        self.test_aglorithms_button.grid(row=4, column=0, padx=(110, 50), pady=25)

        self.print_back_to_baord_button = ctk.CTkButton(
            master=self.button_frame,
            text="Print board back",
            font=("Arial", 20),
            text_color=cd["black"],
            height=50,
            corner_radius=30,
            border_width=3,
            border_color=cd["dark-grey"],
            fg_color=cd["banana"],
            hover_color=cd["pale-yellow"],
            command=lambda: print_board_back(main_gui=self)
        )
        self.print_back_to_baord_button.grid(row=4, column=1, padx=(110, 50), pady=25)

        # Statistics 4 Nerds
        self.statistics_4_nerds_frame = ctk.CTkFrame(master=self.main_frame)
        self.statistics_4_nerds_frame.grid(row=1, column=1, columnspan=1, rowspan=1, sticky="news", padx=(0, 10), pady=(25, 50))

        self.solving_alg_label = ctk.CTkLabel(
            master=self.statistics_4_nerds_frame,
            text="Solving Algorithm:",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.solving_alg_label.grid(row=0, padx=(25, 0), pady=(25, 25), sticky="w")

        self.reductions_made_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Reductions made",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.reductions_made_label.value = 0
        self.reductions_made_label.grid(row=1, padx=(25, 0), pady=(10, 0), sticky="w")

        self.constellations_checked_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Constellations checked",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.constellations_checked_label.value = 0
        self.constellations_checked_label.grid(row=2, padx=(25, 0), pady=(10, 0), sticky="w")

        self.recursions_checked_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Recursions checked",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.recursions_checked_label.value = 0
        self.recursions_checked_label.grid(row=3, padx=(25, 0), pady=(10, 0), sticky="w")

        self.possible_mutations_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Possible mutations",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.possible_mutations_label.value = 0
        self.possible_mutations_label.grid(row=4, padx=(25, 0), pady=(10, 0), sticky="w")

        self.generating_alg_label = ctk.CTkLabel(
            master=self.statistics_4_nerds_frame,
            text="Generating Algorithm:",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.generating_alg_label.grid(row=5, padx=(25, 0), pady=(35, 25), sticky="w")

        self.recursions_made_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Recursions made",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.recursions_made_label.value = 0
        self.recursions_made_label.grid(row=6, padx=(25, 0), pady=(10, 0), sticky="w")

        self.reductions_checked_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Reductions checked",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.reductions_checked_label.value = 0
        self.reductions_checked_label.grid(row=7, padx=(25, 0), pady=(10, 0), sticky="w")

        self.board_label = ctk.CTkLabel(
            master=self.statistics_4_nerds_frame,
            text="Board:",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.board_label.grid(row=8, padx=(25, 0), pady=(35, 25), sticky="w")

        self.numbers_given_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Numbers given",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.numbers_given_label.value = 0
        self.numbers_given_label.grid(row=9, padx=(25, 0), pady=(10, 0), sticky="w")

        self.numbers_resolved_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Numbers resolved",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.numbers_resolved_label.value = 0
        self.numbers_resolved_label.grid(row=10, padx=(25, 0), pady=(10, 0), sticky="w")

        self.numbers_unresolved_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Numbers unresolved",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.numbers_unresolved_label.value = 81
        self.numbers_unresolved_label.grid(row=11, padx=(25, 0), pady=(10, 0), sticky="w")

        self.possible_values_remaining_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="possible values remaining",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.possible_values_remaining_label.value = self.board.get_possible_value_count()
        self.possible_values_remaining_label.grid(row=12, padx=(25, 0), pady=(10, 0), sticky="w")

        self.cell_label = ctk.CTkLabel(
            master=self.statistics_4_nerds_frame,
            text="Cell:",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.cell_label.grid(row=13, padx=(25, 0), pady=(35, 25), sticky="w")

        self.cell_row_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Row",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.cell_row_label.grid(row=14, padx=(25, 0), pady=(10, 0), sticky="w")

        self.cell_col_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Col",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.cell_col_label.grid(row=15, padx=(25, 0), pady=(10, 0), sticky="w")

        self.cell_value_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="Value",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.cell_value_label.grid(row=16, padx=(25, 0), pady=(10, 0), sticky="w")

        self.cell_pV_label = ValueLabel(
            master=self.statistics_4_nerds_frame,
            init_text="possible Values",
            font=("Arial", 20),
            text_color=cd["black"]
        )
        self.cell_pV_label.grid(row=17, padx=(25, 0), pady=(10, 0), sticky="w")

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

    def on_key_press(self, event):
        if self.board.selected_cell is not None:
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
                    self.board.selected_cell.set_value_by_key_press(value=int(event.char))
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

    def solve(self):
        match self.selected_solving_algorithm:
            case Algorithm.SOLVING.ELIMINATION_BY_CONSTELLATION:
                solve_v3(main_gui=self, board=self.board)
            case Algorithm.SOLVING.BACKTRACKING:
                solve_backtracking(main_gui=self, board=self.board)
            case Algorithm.SOLVING.BACKTRACKING_OPTIMIZED:
                reduce_all_possible_values(main_gui=self, board=self.board)
                solve_backtracking(main_gui=self, board=self.board)
            case Algorithm.SOLVING.ELIMINATION_OPTIMIZED:
                optimized_elimination(main_gui=self, board=self.board)

def isSolvable(board):
    initialboard = [[cell.value for cell in board.cell_rows[j]] for j in range(9)]
    board_copy = sudoku.SudokuBoard(initial_board=initialboard)
    board_copy.solve()
    board_copy.print_board()
    return board_copy.isSolvable