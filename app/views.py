import json

import aiohttp_jinja2
from aiohttp import web


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


async def index(request):
    current_ws = web.WebSocketResponse()
    if not current_ws.can_prepare(request).ok:
        return aiohttp_jinja2.render_template('index.html', request, {})

    await current_ws.prepare(request)

    game = get_game(request=request)
    user = User(ws=current_ws)
    game.connect(user=user)
    opponent = game.get_opponent(user=user)

    if opponent is not None:
        # Если есть оппонент, то его необходимо уведомить о подключении другого игрока
        opponent_message = {
            'action': 'join',
            'opponentSign': user.sign,
        }
        await opponent.ws.send_json(opponent_message)
    user_message = {
        'action': 'connect',
        'sign': user.sign,
        'game_id': game.id,
        'opponentName': str(opponent) if opponent else None,
    }
    await user.ws.send_json(user_message)

    async for msg in user.ws:
        if opponent is None:
            opponent = game.get_opponent(user=user)
        if msg.type == web.WSMsgType.text and opponent is not None:
            data = json.loads(msg.data)
            if 'coordinates' in data:
                i = int(data['coordinates']['i'])
                j = int(data['coordinates']['j'])
                if game.set_in_field(user, i, j):
                    await opponent.ws.send_json(data)

                winner = game.get_winner()
                if winner == user.sign:
                    await user.ws.send_json({'action': 'win'})
                    await opponent.ws.send_json({'action': 'lose'})
                    game.state = STATE.GAME_OVER
                elif winner == opponent.sign:
                    await user.ws.send_json({'action': 'lose'})
                    await opponent.ws.send_json({'action': 'win'})
                    game.state = STATE.GAME_OVER

    if opponent:
        await opponent.ws.send_json({'action': 'disconnect'})
    game.state = STATE.OPPONENT_DISCONNECTED
    del user

    return current_ws
