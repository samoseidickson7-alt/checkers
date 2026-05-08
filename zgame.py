import pygame
import sys
import math
import random

# ---------- CONFIG ----------

WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

# Colors
RED = (200, 50, 50)
BLACK = (30, 30, 30)
WHITE = (240, 240, 240)
GREY = (120, 120, 120)
GREEN = (50, 200, 50)
BLUE = (50, 50, 200)
YELLOW = (230, 230, 50)

# Players
HUMAN = "RED"
AI = "BLACK"

pygame.init()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Checkers vs Computer (with Difficulty)")

FONT = pygame.font.SysFont("arial", 24)


# ---------- MODEL ----------

class Piece:
    def __init__(self, row, col, color, king=False):
        self.row = row
        self.col = col
        self.color = color
        self.king = king

    def move(self, row, col):
        self.row = row
        self.col = col

    def make_king(self):
        self.king = True

    def copy(self):
        return Piece(self.row, self.col, self.color, self.king)


class Board:
    def __init__(self):
        self.board = []
        self.red_left = self.black_left = 12
        self.red_kings = self.black_kings = 0
        self.create_board()

    def create_board(self):
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        for row in range(ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    if row < 3:
                        self.board[row][col] = Piece(row, col, BLACK)
                    elif row > 4:
                        self.board[row][col] = Piece(row, col, RED)

    def draw_squares(self, win):
        win.fill(WHITE)
        for row in range(ROWS):
            for col in range(row % 2, COLS, 2):
                pygame.draw.rect(
                    win, GREY, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                )

    def draw(self, win, selected=None, valid_moves=None):
        self.draw_squares(win)
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece:
                    x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                    y = row * SQUARE_SIZE + SQUARE_SIZE // 2
                    color = RED if piece.color == RED else BLACK
                    pygame.draw.circle(win, color, (x, y), SQUARE_SIZE // 2 - 10)
                    if piece.king:
                        pygame.draw.circle(win, YELLOW, (x, y), SQUARE_SIZE // 2 - 18, 3)

        if selected:
            r, c = selected
            pygame.draw.rect(
                win,
                BLUE,
                (c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE),
                3,
            )

        if valid_moves:
            for (r, c), _ in valid_moves.items():
                pygame.draw.circle(
                    win,
                    GREEN,
                    (c * SQUARE_SIZE + SQUARE_SIZE // 2, r * SQUARE_SIZE + SQUARE_SIZE // 2),
                    10,
                )

    def get_piece(self, row, col):
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self.board[row][col]
        return None

    def move_piece(self, piece, row, col):
        self.board[piece.row][piece.col], self.board[row][col] = None, piece
        piece.move(row, col)

        if piece.color == RED and row == 0 and not piece.king:
            piece.make_king()
            self.red_kings += 1
        elif piece.color == BLACK and row == ROWS - 1 and not piece.king:
            piece.make_king()
            self.black_kings += 1

    def remove(self, pieces):
        for piece in pieces:
            if piece:
                self.board[piece.row][piece.col] = None
                if piece.color == RED:
                    self.red_left -= 1
                else:
                    self.black_left -= 1

    def winner(self):
        if self.red_left <= 0:
            return BLACK
        if self.black_left <= 0:
            return RED
        return None

    def get_all_pieces(self, color):
        pieces = []
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece and piece.color == color:
                    pieces.append(piece)
        return pieces

    def get_valid_moves(self, piece):
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row

        if piece.color == RED or piece.king:
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))
        if piece.color == BLACK or piece.king:
            moves.update(self._traverse_left(row + 1, min(row + 3, ROWS), 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, ROWS), 1, piece.color, right))

        return moves

    def _traverse_left(self, start, stop, step, color, left, skipped=None):
        if skipped is None:
            skipped = []
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break
            current = self.board[r][left]
            if current is None:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, left)] = last + skipped
                else:
                    moves[(r, left)] = last

                if last:
                    if step == -1:
                        row = max(r - 3, -1)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(
                        self._traverse_left(r + step, row, step, color, left - 1, skipped=last)
                    )
                    moves.update(
                        self._traverse_right(r + step, row, step, color, left + 1, skipped=last)
                    )
                break
            elif current.color == color:
                break
            else:
                last = [current]

            left -= 1
        return moves

    def _traverse_right(self, start, stop, step, color, right, skipped=None):
        if skipped is None:
            skipped = []
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= COLS:
                break
            current = self.board[r][right]
            if current is None:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, right)] = last + skipped
                else:
                    moves[(r, right)] = last

                if last:
                    if step == -1:
                        row = max(r - 3, -1)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(
                        self._traverse_left(r + step, row, step, color, right - 1, skipped=last)
                    )
                    moves.update(
                        self._traverse_right(r + step, row, step, color, right + 1, skipped=last)
                    )
                break
            elif current.color == color:
                break
            else:
                last = [current]

            right += 1
        return moves

    def copy(self):
        new_board = Board()
        new_board.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        new_board.red_left = self.red_left
        new_board.black_left = self.black_left
        new_board.red_kings = self.red_kings
        new_board.black_kings = self.black_kings

        for r in range(ROWS):
            for c in range(COLS):
                p = self.board[r][c]
                if p:
                    new_board.board[r][c] = p.copy()
        return new_board


# ---------- AI (MINIMAX) ----------

def evaluate(board: Board):
    # Simple heuristic: pieces + king bonus
    return (board.red_left - board.black_left) + (board.red_kings * 0.5 - board.black_kings * 0.5)


def get_all_moves(board: Board, color):
    moves = []
    for piece in board.get_all_pieces(color):
        valid_moves = board.get_valid_moves(piece)
        for (r, c), skipped in valid_moves.items():
            temp_board = board.copy()
            temp_piece = temp_board.get_piece(piece.row, piece.col)
            temp_board.move_piece(temp_piece, r, c)
            if skipped:
                temp_board.remove(skipped)
            moves.append(temp_board)
    return moves


def minimax(board: Board, depth, maximizing_player, difficulty_color):
    winner = board.winner()
    if depth == 0 or winner is not None:
        score = evaluate(board)
        return score, board

    if maximizing_player:
        max_eval = -math.inf
        best_board = None
        for move in get_all_moves(board, difficulty_color):
            eval_score, _ = minimax(move, depth - 1, False, difficulty_color)
            if eval_score > max_eval:
                max_eval = eval_score
                best_board = move
        return max_eval, best_board
    else:
        min_eval = math.inf
        opp_color = RED if difficulty_color == BLACK else BLACK
        for move in get_all_moves(board, opp_color):
            eval_score, _ = minimax(move, depth - 1, True, difficulty_color)
            if eval_score < min_eval:
                min_eval = eval_score
                best_board = move
        return min_eval, best_board


def ai_move(board: Board, depth):
    _, new_board = minimax(board, depth, True, BLACK)
    return new_board


# ---------- GAME LOOP ----------

def draw_status(win, turn, difficulty_name):
    text = f"Turn: {'You (RED)' if turn == RED else 'Computer (BLACK)'} | Difficulty: {difficulty_name}"
    label = FONT.render(text, True, BLACK)
    pygame.draw.rect(win, WHITE, (0, HEIGHT - 40, WIDTH, 40))
    win.blit(label, (10, HEIGHT - 35))


def main():
    run = True
    clock = pygame.time.Clock()
    board = Board()
    selected = None
    valid_moves = {}
    turn = RED  # human starts

    # Difficulty: depth of minimax
    difficulty_levels = {
        "Easy": 1,
        "Medium": 3,
        "Hard": 5,
    }
    difficulty_name = "Medium"
    depth = difficulty_levels[difficulty_name]

    while run:
        clock.tick(60)

        winner = board.winner()
        if winner:
            WIN.fill(WHITE)
            msg = "You win!" if winner == RED else "Computer wins!"
            label = FONT.render(msg + "  (Press R to restart)", True, BLACK)
            WIN.blit(label, (WIDTH // 2 - label.get_width() // 2, HEIGHT // 2))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    board = Board()
                    turn = RED
                    selected = None
                    valid_moves = {}
            continue

        if turn == BLACK:
            # AI turn
            pygame.time.delay(400)
            board = ai_move(board, depth)
            turn = RED
            selected = None
            valid_moves = {}

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    difficulty_name = "Easy"
                    depth = difficulty_levels[difficulty_name]
                elif event.key == pygame.K_2:
                    difficulty_name = "Medium"
                    depth = difficulty_levels[difficulty_name]
                elif event.key == pygame.K_3:
                    difficulty_name = "Hard"
                    depth = difficulty_levels[difficulty_name]

            if event.type == pygame.MOUSEBUTTONDOWN and turn == RED:
                pos = pygame.mouse.get_pos()
                row = pos[1] // SQUARE_SIZE
                col = pos[0] // SQUARE_SIZE

                if selected:
                    if (row, col) in valid_moves:
                        piece = board.get_piece(*selected)
                        board.move_piece(piece, row, col)
                        skipped = valid_moves[(row, col)]
                        if skipped:
                            board.remove(skipped)
                        turn = BLACK
                        selected = None
                        valid_moves = {}
                    else:
                        selected = None
                        valid_moves = {}
                else:
                    piece = board.get_piece(row, col)
                    if piece and piece.color == RED:
                        selected = (row, col)
                        valid_moves = board.get_valid_moves(piece)

        board.draw(WIN, selected, valid_moves)
        draw_status(WIN, turn, difficulty_name)
        pygame.display.update()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
