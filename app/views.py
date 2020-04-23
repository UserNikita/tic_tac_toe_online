import json

import aiohttp_jinja2
from aiohttp import web

from models import User, get_game, STATE


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
