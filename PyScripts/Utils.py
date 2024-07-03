from enum import Enum
import random


class SolveType(Enum):
    COMPLETE = 0
    NEXT_DIGIT = 1
    NEXT_REDUCTION = 2


class Difficulty(Enum):
    EASY = range(39, 43)
    MEDIUM = range(34, 38)
    HARD = range(29, 33)
    EXTREME = range(19, 23)


def generate_board():

    board = [[None for i in range(9)] for j in range(9)]
    solve_sudoku(board)
    for row in board:
        print(row)

def is_valid(board, row, col, num):
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

def solve_sudoku(board):
    for i in range(9):
        for j in range(9):
            if board[i][j] is None:
                random_numbers = list(range(1, 10))
                random.shuffle(random_numbers)
                for num in random_numbers:
                    if is_valid(board, i, j, num):
                        board[i][j] = num
                        print(board)
                        if solve_sudoku(board):
                            return True
                        board[i][j] = None
                return False
    return True
