class STATE:
    WAIT_OPPONENT = 0
    WAIT_X_ENTER = 1
    WAIT_O_ENTER = 2
    GAME_OVER = 3
    OPPONENT_DISCONNECTED = 4


SIGN_X = 1
SIGN_O = 2


class User:
    ws = None
    sign = 0

    def __init__(self, ws):
        self.ws = ws


class Game:
    id = 0
    board = None
    user_x = None
    user_o = None
    state = STATE.WAIT_OPPONENT

    def __init__(self):
        self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

    def connect(self, user):
        # Кто присоединяется к игре первым, тот играет за X
        if self.user_x is None:
            self.user_x = user
            self.user_x.sign = SIGN_X
        else:
            self.user_o = user
            self.user_o.sign = SIGN_O
            # Если игрок присоединился вторым, то необходимо перевести игру в другое состояние
            self.state = STATE.WAIT_X_ENTER

    def get_opponent(self, user):
        if self.user_x is user:
            return self.user_o
        elif self.user_o is user:
            return self.user_x

    def set_in_field(self, user, i, j):
        if self.board[i][j] == 0:
            self.board[i][j] = user.sign
            return True
        return False

    def get_winner(self):
        board = self.board
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2]:
                return board[i][0]
        for i in range(3):
            if board[0][i] == board[1][i] == board[2][i]:
                return board[0][i]
        if board[0][0] == board[1][1] == board[2][2]:
            return board[1][1]
        if board[0][2] == board[1][1] == board[2][0]:
            return board[1][1]


def get_game(request):
    game_list = list(request.app['ws'].values())
    if game_list and game_list[-1].state == STATE.WAIT_OPPONENT:
        # Если есть игра к которой можно присоединиться
        game = game_list[-1]
    else:
        # Если не удалось найти свободного игрока, создаём новую игру
        game = Game()
        game.id = len(game_list)
        request.app['ws'][game.id] = game
    return game
