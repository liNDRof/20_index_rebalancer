# зверху файлу додай
import traceback
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from trader.btceth_trader import BTCETH_CMC20_Trader
from django.http import JsonResponse
import threading
import time
from dashboard.models import TraderSettings



trader_thread = None
trader_running = False
next_run_time = None
last_portfolio = {}
last_rebalance_info = {}


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            response = redirect('dashboard:index')
            response.set_cookie('is_logged_in', 'true', max_age=3600*24*7)  # cookie на 7 днів
            return response
        else:
            return render(request, 'dashboard/login.html', {'error': 'Невірний логін або пароль'})

    return render(request, 'dashboard/login.html')

@login_required
def index(request):
    """Головна сторінка керування трейдером"""
    global trader_running, trader_thread

    # 🚀 Автоматичний запуск трейдера при вході
    if not trader_running:
        trader_running = True
        trader_thread = threading.Thread(target=trader_loop, daemon=True)
        trader_thread.start()

    return render(request, 'dashboard/index.html', {
        'is_running': trader_running,
        'next_run_time': next_run_time,
        'portfolio': last_portfolio,
        'rebalance': last_rebalance_info,
    })


def logout_view(request):
    logout(request)
    response = redirect('login')
    response.delete_cookie('is_logged_in')
    return response


from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Перевірка заповненості полів
        if not username or not email or not password1 or not password2:
            return render(request, 'dashboard/register.html', {'error': 'Заповни всі поля'})

        # Перевірка співпадіння паролів
        if password1 != password2:
            return render(request, 'dashboard/register.html', {'error': 'Паролі не співпадають'})

        # Перевірка унікальності
        if User.objects.filter(username=username).exists():
            return render(request, 'dashboard/register.html', {'error': 'Такий логін вже існує'})
        if User.objects.filter(email=email).exists():
            return render(request, 'dashboard/register.html', {'error': 'Цей email вже зареєстровано'})

        # Створення користувача
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()

        # Автоматичний логін
        login(request, user)
        response = redirect('dashboard:index')
        response.set_cookie('is_logged_in', 'true', max_age=3600 * 24 * 7)
        return response

    return render(request, 'dashboard/register.html')



def trader_loop():
    global trader_running, next_run_time, last_portfolio, last_rebalance_info

    try:
        trader = BTCETH_CMC20_Trader()
        print("DEBUG: trader_loop created trader, interval:", trader.update_interval)
    except Exception:
        print("ERROR: cannot create trader in trader_loop")
        traceback.print_exc()
        trader_running = False
        return

    interval = trader.update_interval

    while trader_running:
        try:
            print("🔁 Запуск ребалансування (background)...")
            balances, total = trader.get_all_binance_balances()
            print("DEBUG: background balances total:", total)
            last_portfolio = balances

            rebalance_result = trader.execute_portfolio_rebalance(dry_run=True)
            print("DEBUG: background rebalance_result:", repr(rebalance_result))
            last_rebalance_info = rebalance_result if rebalance_result is not None else {"note": "no result (None)"}

            print("✅ Ребалансування завершено (background).")
        except Exception as e:
            print("❌ Помилка у трейдері (background):", e)
            traceback.print_exc()
            last_rebalance_info = {"error": str(e), "trace": traceback.format_exc()}
        # ... (залиш остальну частину)


@login_required
def start_trader(request):
    global trader_thread, trader_running
    if not trader_running:
        trader_running = True
        trader_thread = threading.Thread(target=trader_loop, daemon=True)
        trader_thread.start()
        return JsonResponse({'status': 'started'})
    else:
        return JsonResponse({'status': 'already_running'})

@login_required
def stop_trader(request):
    global trader_running
    trader_running = False
    return JsonResponse({'status': 'stopped'})

@login_required
def get_status(request):
    """Повертає статус, портфель і останнє ребалансування"""
    if next_run_time:
        remaining = max(0, int(next_run_time - time.time()))
    else:
        remaining = None

    return JsonResponse({
        'is_running': trader_running,
        'remaining': remaining,
        'portfolio': last_portfolio,
        'rebalance': last_rebalance_info,
    })


@login_required
def update_default_interval(request):
    """Оновлення дефолтного інтервалу ребалансування"""
    global default_interval
    try:
        days = int(request.GET.get("days", 0))
        hours = int(request.GET.get("hours", 0))
        minutes = int(request.GET.get("minutes", 0))
        seconds = int(request.GET.get("seconds", 0))
        total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
        default_interval = max(60, total_seconds)  # мінімум 60 с
        return JsonResponse({"status": "ok", "default_interval": default_interval})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)})

@login_required
def set_next_rebalance_time(request):
    """Встановити час до наступного ребалансування"""
    global next_run_time
    try:
        days = int(request.GET.get("days", 0))
        hours = int(request.GET.get("hours", 0))
        minutes = int(request.GET.get("minutes", 0))
        seconds = int(request.GET.get("seconds", 0))
        total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
        next_run_time = time.time() + total_seconds
        return JsonResponse({"status": "ok", "next_in": total_seconds})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)})



def calculate_rebalancing_orders(self, current_balances: dict, target_allocation: dict,
                                 total_portfolio_value: float) -> dict:
    """Розширена логіка: обираємо market або convert з урахуванням LOT_SIZE та MIN_NOTIONAL."""
    operations = {
        'sell_orders': {},
        'sell_convert': {},
        'buy_orders': {},
        'buy_convert': {}
    }

    THRESHOLD = 5.0  # базовий поріг (запас)
    print(f"\n💵 Розрахунок операцій для ребалансування (threshold ${THRESHOLD})")
    print("-" * 80)

    # вибираємо quote currency
    quote_currency = None
    quote_balance = 0
    for stable in ['USDC', 'USDT', 'BUSD', 'FDUSD']:
        if current_balances.get(stable, {}).get('total', 0) > 0.1:
            quote_currency = stable
            quote_balance = current_balances.get(stable, {}).get('total', 0)
            break
    if not quote_currency:
        quote_currency = 'USDC'
        quote_balance = 0
        print(f"⚠️ Немає стейблкоїнів, використовую {quote_currency}")

    def can_place_market(pair: str, quantity: float, value_usdc: float) -> (bool, str):
        """
        Перевіряє, чи можна ставити market order:
        - існує пара
        - quantity >= LOT_SIZE.stepSize
        - value_usdc >= MIN_NOTIONAL (якщо є)
        Повертає (True/False, reason)
        """
        try:
            info = self.client.get_symbol_info(pair)
            if not info:
                return False, "no_symbol_info"

            # знайдемо LOT_SIZE і MIN_NOTIONAL
            step_size = None
            min_notional = None
            for f in info.get('filters', []):
                if f.get('filterType') == 'LOT_SIZE':
                    step_size = float(f.get('stepSize', '0'))
                elif f.get('filterType') == 'MIN_NOTIONAL':
                    # поле може бути 'minNotional' або 'minNotional' як str
                    min_notional = float(f.get('minNotional', f.get('minNotional', 0) or 0))

            # якщо step_size відомий — перевіряємо квант
            if step_size and quantity < step_size:
                return False, f"below_lot_size({quantity:.8f}<{step_size})"

            # якщо min_notional заданий — перевіряємо value
            if min_notional and value_usdc < min_notional:
                return False, f"below_min_notional(${value_usdc:.2f}<{min_notional})"

            return True, "ok"
        except Exception as e:
            # якщо не можемо отримати info — краще використати convert
            return False, f"symbol_info_error:{e}"

    total_sell_value = 0
    total_buy_value = 0

    for symbol, target_data in target_allocation.items():
        current_value = current_balances.get(symbol, {}).get('usdc_value', 0)
        current_quantity = current_balances.get(symbol, {}).get('total', 0)
        target_value = target_data['target_value']
        difference_value = target_value - current_value

        if abs(difference_value) < 1:
            continue

        price = self.get_binance_price(symbol)
        if price == 0:
            print(f"⚠️ Не вдалося отримати ціну для {symbol}, пропускаємо")
            continue

        if difference_value > 0:
            # КУПІВЛЯ
            quantity = difference_value / price
            total_buy_value += difference_value

            pair = f"{symbol}{quote_currency}"
            can_market, reason = can_place_market(pair, quantity, difference_value)
            if difference_value > THRESHOLD and can_market:
                operations['buy_orders'][symbol] = {
                    'quantity': quantity,
                    'value_usdc': difference_value,
                    'price': price,
                    'quote_currency': quote_currency,
                    'reason': reason
                }
                print(f"🟢 MARKET BUY {symbol}: {quantity:,.8f} токенів на ${difference_value:,.2f} (reason: {reason})")
            else:
                operations['buy_convert'][symbol] = {
                    'from_asset': quote_currency,
                    'to_asset': symbol,
                    'amount': difference_value,
                    'type': 'convert',
                    'reason': reason
                }
                print(f"🔵 CONVERT {quote_currency}→{symbol}: ${difference_value:,.2f} (reason: {reason})")
        else:
            # ПРОДАЖ
            sell_value = abs(difference_value)
            quantity = sell_value / price
            total_sell_value += sell_value

            pair = f"{symbol}{quote_currency}"
            can_market, reason = can_place_market(pair, quantity, sell_value)
            if sell_value > THRESHOLD and can_market:
                operations['sell_orders'][symbol] = {
                    'quantity': quantity,
                    'value_usdc': sell_value,
                    'price': price,
                    'quote_currency': quote_currency,
                    'reason': reason
                }
                print(f"🔴 MARKET SELL {symbol}: {quantity:,.8f} токенів на ${sell_value:,.2f} (reason: {reason})")
            else:
                operations['sell_convert'][symbol] = {
                    'from_asset': symbol,
                    'to_asset': quote_currency,
                    'amount': sell_value,
                    'current_quantity': current_quantity,
                    'type': 'convert',
                    'reason': reason
                }
                print(f"🟠 CONVERT {symbol}→{quote_currency}: ${sell_value:,.2f} (reason: {reason})")

    # Перевірка коштів
    if any(operations.values()):
        available_after_sell = quote_balance + total_sell_value
        print(f"\n💰 Баланс після продажу: ${available_after_sell:.2f}")
        print(f"📊 Потрібно для купівлі: ${total_buy_value:.2f}")
        if available_after_sell >= total_buy_value:
            print("✅ Достатньо коштів")
        else:
            print(f"⚠️ Недостатньо коштів: бракує ${total_buy_value - available_after_sell:.2f}")

    print("-" * 80)
    return operations



@login_required
def manual_rebalance(request):
    global last_portfolio, last_rebalance_info, next_run_time

    try:
        print("DEBUG: manual_rebalance called by", request.user)
        trader = BTCETH_CMC20_Trader()
        print("DEBUG: trader instance created")
        balances, total = trader.get_all_binance_balances()
        print("DEBUG: balances fetched, total =", total)
        last_portfolio = balances

        rebalance_result = trader.execute_portfolio_rebalance(dry_run=True)
        print("DEBUG: execute_portfolio_rebalance returned:", repr(rebalance_result))
        # якщо None -> покажемо зрозумілий dict
        last_rebalance_info = rebalance_result if rebalance_result is not None else {"note": "no result (None)"}

        next_run_time = time.time() + trader.update_interval

        return JsonResponse({
            "status": "ok",
            "rebalance": last_rebalance_info
        })

    except Exception as e:
        traceback.print_exc()
        last_rebalance_info = {"error": str(e), "trace": traceback.format_exc()}
        return JsonResponse({"status": "error", "error": str(e), "trace": traceback.format_exc()})


