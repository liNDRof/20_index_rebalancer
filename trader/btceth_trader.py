import os
import time
import requests
import logging
import traceback
from datetime import datetime, timedelta
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException

load_dotenv()

# Get specialized loggers
api_logger = logging.getLogger('api')
trade_logger = logging.getLogger('trades')
error_logger = logging.getLogger('errors')
debug_logger = logging.getLogger('debug')


class BTCETH_CMC20_Trader:
    def __init__(self, binance_api_key=None, binance_api_secret=None,
                 cmc_api_key=None, update_interval=None, index_type='top2'):
        """
        Initialize trader with index type

        Args:
            index_type: 'top2', 'top5', 'top10', or 'top20'
        """

    def __init__(self, binance_api_key=None, binance_api_secret=None, cmc_api_key=None, update_interval=None):
        """
        Initialize trader with user-specific or default credentials

        Args:
            binance_api_key: User's Binance API key (if None, uses .env)
            binance_api_secret: User's Binance API secret (if None, uses .env)
            cmc_api_key: User's CoinMarketCap API key (if None, uses .env)
            update_interval: Custom update interval in seconds (if None, uses .env)
        """
        debug_logger.info("Initializing BTCETH_CMC20_Trader...")

        # Binance API - use provided credentials or fall back to .env
        self.binance_api_key = binance_api_key or os.getenv("BINANCE_API_KEY")
        self.binance_api_secret = binance_api_secret or os.getenv("BINANCE_API_SECRET")

        if not self.binance_api_key or not self.binance_api_secret:
            error_logger.error("Binance API credentials missing")
            raise ValueError("Binance API credentials are required. Please configure them in your profile.")

        debug_logger.info("Creating Binance client...")
        self.client = Client(self.binance_api_key, self.binance_api_secret)

        self.index_type = index_type

        # Synchronize timestamp with Binance server to avoid timestamp errors
        try:
            debug_logger.info("Synchronizing timestamp with Binance server...")
            server_time = self.client.get_server_time()
            local_time = int(time.time() * 1000)
            time_offset = server_time['serverTime'] - local_time
            self.client.timestamp_offset = time_offset
            debug_logger.info(f"Timestamp synchronized. Offset: {time_offset}ms")
        except Exception as e:
            debug_logger.warning(f"Failed to synchronize timestamp: {e}. Continuing without sync.")

        debug_logger.info("Binance client created successfully")

        # CoinMarketCap API - use provided or fall back to .env
        self.cmc_api_key = cmc_api_key or os.getenv("COINMARKETCAP_API_KEY")
        self.cmc_api_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        self.update_interval = update_interval or int(os.getenv("CMC_INDEX_UPDATE_INTERVAL", 3600))

        # Список стейблкоїнів для виключення
        self.stablecoins = ['USDT', 'USDC', 'BUSD', 'FDUSD', 'USDe', 'DAI', 'TUSD', 'USDP', 'USDD', 'GUSD', 'PYUSD']

        debug_logger.info(f"Trader initialized with update_interval={self.update_interval}s, stablecoins={len(self.stablecoins)}")

    def get_binance_balance(self, asset="USDC") -> float:
        """Отримує доступний баланс на Binance"""
        try:
            balance = self.client.get_asset_balance(asset=asset)
            free_balance = float(balance['free'])
            print(f"💰 Доступний баланс {asset}: {free_balance:,.2f}")
            return free_balance
        except BinanceAPIException as e:
            print(f"❌ Помилка отримання балансу: {e}")
            return 0.0

    def get_all_binance_balances(self) -> dict:
        """Отримує всі баланси на Binance з вартістю в USDC"""
        api_logger.info("Fetching all Binance balances...")
        try:
            account = self.client.get_account()
            balances = {}
            total_portfolio_usdc = 0.0

            print("\n💼 Поточні баланси на Binance:")
            print("-" * 90)

            for balance in account['balances']:
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked

                if total > 0:
                    asset = balance['asset']

                    # Розраховуємо вартість в USDC
                    usdc_value = 0.0
                    if asset in self.stablecoins:
                        usdc_value = total
                    else:
                        try:
                            ticker = self.client.get_symbol_ticker(symbol=f"{asset}USDC")
                            price = float(ticker['price'])
                            usdc_value = total * price
                        except:
                            try:
                                ticker = self.client.get_symbol_ticker(symbol=f"{asset}USDT")
                                price = float(ticker['price'])
                                usdc_value = total * price
                            except:
                                try:
                                    ticker_btc = self.client.get_symbol_ticker(symbol=f"{asset}BTC")
                                    btc_price = float(ticker_btc['price'])
                                    btc_usdc = float(self.client.get_symbol_ticker(symbol="BTCUSDC")['price'])
                                    usdc_value = total * btc_price * btc_usdc
                                except:
                                    usdc_value = 0.0

                    balances[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': total,
                        'usdc_value': usdc_value
                    }

                    total_portfolio_usdc += usdc_value

                    print(f"{asset:6s} | Вільно: {free:12,.6f} | Заблоковано: {locked:12,.6f} | "
                          f"≈ ${usdc_value:10,.2f} USDC")

            print("-" * 90)
            print(f"{'РАЗОМ':6s} | {'':12s}   {'':12s}   {'':15s}   ≈ ${total_portfolio_usdc:10,.2f} USDC")
            print("-" * 90)

            api_logger.info(f"Successfully fetched balances: {len(balances)} assets, total=${total_portfolio_usdc:.2f}")
            debug_logger.debug(f"Balance details: {balances}")
            return balances, total_portfolio_usdc

        except BinanceAPIException as e:
            error_logger.error(f"Binance API error fetching balances: {e}")
            error_logger.error(traceback.format_exc())
            print(f"❌ Помилка отримання балансів: {e}")
            return {}, 0.0

    def get_btc_eth_allocation_from_cmc20(self) -> dict:
        """Отримує топ-20 токенів, бере ваги BTC та ETH + перерозподіл решти 18 ПРОПОРЦІЙНО"""
        api_logger.info("Fetching CMC Top 20 allocation data...")
        try:
            headers = {
                'X-CMC_PRO_API_KEY': self.cmc_api_key,
                'Accept': 'application/json'
            }

            params = {
                'start': '1',
                'limit': '50',
                'convert': 'USD'
            }

            api_logger.debug(f"Calling CoinMarketCap API: {self.cmc_api_url}")
            response = requests.get(self.cmc_api_url, headers=headers, params=params)
            data = response.json()
            api_logger.debug(f"CMC API response status: {response.status_code}")

            if response.status_code != 200:
                error_msg = data.get('status', {}).get('error_message', 'Unknown error')
                error_logger.error(f"CoinMarketCap API error: {error_msg}")
                print(f"❌ Помилка API: {error_msg}")
                return {}

            coins = data['data']

            # Видаляємо всі стейблкоїни зі списку
            coins = [coin for coin in coins if coin['symbol'] not in self.stablecoins]

            # Беремо топ-20 (без стейблкоїнів)
            top20_coins = coins[:20]

            # Розраховуємо загальну ринкову капіталізацію топ-20
            total_market_cap = sum(coin['quote']['USD']['market_cap'] for coin in top20_coins)

            # Знаходимо BTC та ETH
            btc_data = None
            eth_data = None
            other_18_total_market_cap = 0.0

            for coin in top20_coins:
                market_cap = coin['quote']['USD']['market_cap']

                if coin['symbol'] == 'BTC':
                    btc_data = coin
                elif coin['symbol'] == 'ETH':
                    eth_data = coin
                else:
                    other_18_total_market_cap += market_cap

            if not btc_data or not eth_data:
                error_logger.error("BTC or ETH not found in CMC Top 20")
                print("❌ BTC або ETH не знайдено в топ-20")
                return {}

            # Розраховуємо початкові ваги BTC та ETH в топ-20
            btc_original_weight = (btc_data['quote']['USD']['market_cap'] / total_market_cap) * 100
            eth_original_weight = (eth_data['quote']['USD']['market_cap'] / total_market_cap) * 100

            # Розраховуємо вагу решти 18 токенів
            other_18_weight = (other_18_total_market_cap / total_market_cap) * 100

            # Ділимо вагу решти 18 токенів ПОРІВНУ (50/50) між BTC та ETH
            redistribution_per_token = other_18_weight / 2

            # Фінальні ваги: кожен отримує свою оригінальну вагу + 50% від решти 18
            btc_final_weight = btc_original_weight + redistribution_per_token
            eth_final_weight = eth_original_weight + redistribution_per_token

            # Формуємо результат
            allocation_data = {
                'BTC': {
                    'rank': btc_data['cmc_rank'],
                    'name': btc_data['name'],
                    'original_weight': btc_original_weight,
                    'redistribution_bonus': redistribution_per_token,
                    'weight': btc_final_weight,
                    'market_cap': btc_data['quote']['USD']['market_cap'],
                    'price': btc_data['quote']['USD']['price'],
                    'change_24h': btc_data['quote']['USD']['percent_change_24h']
                },
                'ETH': {
                    'rank': eth_data['cmc_rank'],
                    'name': eth_data['name'],
                    'original_weight': eth_original_weight,
                    'redistribution_bonus': redistribution_per_token,
                    'weight': eth_final_weight,
                    'market_cap': eth_data['quote']['USD']['market_cap'],
                    'price': eth_data['quote']['USD']['price'],
                    'change_24h': eth_data['quote']['USD']['percent_change_24h']
                }
            }

            # Виводимо інформацію про розподіл для верифікації
            print(f"\n🔍 ДЕТАЛІ РОЗПОДІЛУ CMC20 (50/50):")
            print(f"   📊 Загальна капіталізація топ-20: ${total_market_cap:,.0f}")
            print(f"   💰 BTC оригінал: {btc_original_weight:.2f}% (${btc_data['quote']['USD']['market_cap']:,.0f})")
            print(f"   💰 ETH оригінал: {eth_original_weight:.2f}% (${eth_data['quote']['USD']['market_cap']:,.0f})")
            print(f"   📦 Решта 18 токенів: {other_18_weight:.2f}% (${other_18_total_market_cap:,.0f})")
            print(f"   ➗ Розподіл 18 токенів: 50% BTC + 50% ETH")
            print(f"   ➕ BTC отримує: +{redistribution_per_token:.2f}%")
            print(f"   ➕ ETH отримує: +{redistribution_per_token:.2f}%")
            print(f"   ✅ BTC фінал: {btc_final_weight:.2f}%")
            print(f"   ✅ ETH фінал: {eth_final_weight:.2f}%")
            print(f"   🎯 Перевірка суми: {btc_final_weight + eth_final_weight:.2f}% (має бути 100%)\n")

            api_logger.info(f"CMC allocation calculated: BTC={btc_final_weight:.2f}%, ETH={eth_final_weight:.2f}%")
            debug_logger.debug(f"Full allocation data: {allocation_data}")
            return allocation_data

        except Exception as e:
            error_logger.error(f"Error fetching CMC20 index: {e}")
            error_logger.error(traceback.format_exc())
            print(f"❌ Помилка отримання CMC20 індексу: {e}")
            return {}

    def display_btc_eth_allocation_chart(self, total_portfolio_value: float):
        """Відображає BTC та ETH з перерозподілом решти 18 токенів"""
        print("\n" + "=" * 120)
        print("📈 BTC + ETH PORTFOLIO (НА ОСНОВІ COINMARKETCAP TOP-20 INDEX)")
        print("=" * 120)

        allocation_data = self.get_btc_eth_allocation_from_cmc20()

        if not allocation_data:
            print("❌ Не вдалося отримати дані індексу")
            return {}

        print(f"\n💼 Загальна вартість портфеля: ${total_portfolio_value:,.2f} USDC")
        print(f"🎯 Цільовий розподіл: BTC + ETH з перерозподілом решти 18 токенів CMC20 порівну\n")

        # Сортуємо за рангом
        sorted_coins = sorted(allocation_data.items(), key=lambda x: x[1]['rank'])

        print("┌" + "─" * 118 + "┐")
        print(f"│ {'#':>3} │ {'Токен':^8} │ {'Назва':<18} │ {'Початкова %':>13} │ {'Бонус %':>10} │ "
              f"{'Фінальна %':>12} │ {'Цільова сума $':>16} │ {'Ціна USD':>14} │ {'24h %':>8} │")
        print("├" + "─" * 118 + "┤")

        final_allocation = {}
        total_allocated = 0.0

        for display_num, (symbol, data) in enumerate(sorted_coins, 1):
            target_value = total_portfolio_value * (data['weight'] / 100)
            total_allocated += target_value

            final_allocation[symbol] = {
                'weight': data['weight'] / 100,
                'target_value': target_value,
                'price': data['price'],
                'change_24h': data['change_24h'],
                'rank': data['rank']
            }

            # Форматування
            change_color = "+" if data['change_24h'] >= 0 else ""
            target_str = f"${target_value:,.2f}"
            original_weight_str = f"{data['original_weight']:.2f}%"
            bonus_str = f"+{data['redistribution_bonus']:.2f}%"
            final_weight_str = f"{data['weight']:.2f}%"

            print(f"│ {display_num:>3} │ {symbol:^8} │ {data['name']:<18.18} │ "
                  f"{original_weight_str:>13} │ {bonus_str:>10} │ {final_weight_str:>12} │ "
                  f"{target_str:>16} │ ${data['price']:>13,.2f} │ {change_color}{data['change_24h']:>7.2f}% │")

        print("└" + "─" * 118 + "┘")

        # Підсумок
        print(f"\n💼 Цільова сума BTC+ETH: ${total_allocated:,.2f} USDC (100% від ${total_portfolio_value:,.2f})")
        print(
            f"📊 Кожен токен отримав додатково: +{allocation_data['BTC']['redistribution_bonus']:.2f}% (50% від решти 18 токенів)")
        print(
            f"⚖️ Фінальне співвідношення: BTC {allocation_data['BTC']['weight']:.2f}% / ETH {allocation_data['ETH']['weight']:.2f}%")
        print("=" * 120 + "\n")

        return final_allocation

    def display_rebalancing_table(self, current_balances: dict, target_allocation: dict, total_portfolio_value: float):
        """Відображає таблицю з поточними балансами та необхідним ребалансуванням (BTC+ETH)"""
        print("\n" + "=" * 120)
        print("⚖️ ТАБЛИЦЯ РЕБАЛАНСУВАННЯ ПОРТФЕЛЯ (BTC + ETH)")
        print("=" * 120)

        print(f"\n💰 Загальна вартість портфеля: ${total_portfolio_value:,.2f} USDC\n")

        print("┌" + "─" + "─" * 118 + "┐")
        print(f"│ {'Токен':^8} │ {'Поточна к-сть':>15} │ {'Поточна $':>14} │ {'Поточна %':>11} │ "
              f"{'Цільова $':>14} │ {'Цільова %':>11} │ {'Різниця $':>14} │ {'Дія':^15} │")
        print("├" + "─" * 118 + "┤")

        # Беремо тільки BTC та ETH
        tokens = ['BTC', 'ETH']
        total_difference = 0.0

        for token in tokens:
            # Поточні дані
            current_balance = current_balances.get(token, {}).get('total', 0)
            current_value = current_balances.get(token, {}).get('usdc_value', 0)
            current_percent = (current_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0

            # Цільові дані
            target_value = target_allocation.get(token, {}).get('target_value', 0)
            target_percent = target_allocation.get(token, {}).get('weight', 0) * 100

            # Різниця
            difference = target_value - current_value
            total_difference += abs(difference)

            # Визначаємо дію
            if abs(difference) < 1:
                action = "✓ OK"
            elif difference > 0:
                action = f"🟢 КУПИТИ"
            else:
                action = f"🔴 ПРОДАТИ"

            # Форматування
            current_str = f"{current_balance:,.8f}".rstrip('0').rstrip('.')
            difference_str = f"{difference:+,.2f}" if difference != 0 else "0.00"

            print(f"│ {token:^8} │ {current_str:>15} │ ${current_value:>12,.2f} │ {current_percent:>10.2f}% │ "
                  f"${target_value:>12,.2f} │ {target_percent:>10.2f}% │ ${difference_str:>12} │ {action:^15} │")

        print("└" + "─" * 118 + "┘")

        # Показуємо стейблкоїни окремо
        stablecoins_total = sum(current_balances.get(coin, {}).get('usdc_value', 0)
                                for coin in self.stablecoins)

        print(f"\n💵 Доступні стейблкоїни для купівлі: ${stablecoins_total:,.2f} USDC")
        print(f"📊 Загальна різниця для ребалансування: ${total_difference / 2:,.2f}")
        print("=" * 120 + "\n")

    def get_binance_price(self, symbol: str) -> float:
        """Отримує поточну ціну токена на Binance"""
        try:
            pair = f"{symbol}USDC"
            ticker = self.client.get_symbol_ticker(symbol=pair)
            return float(ticker['price'])
        except BinanceAPIException:
            try:
                pair = f"{symbol}USDT"
                ticker = self.client.get_symbol_ticker(symbol=pair)
                return float(ticker['price'])
            except BinanceAPIException as e:
                print(f"❌ Не вдалося отримати ціну {symbol}: {e}")
                return 0.0

    def get_trading_pair(self, symbol: str) -> str:
        """Визначає доступну торгову пару"""
        try:
            pair = f"{symbol}USDC"
            self.client.get_symbol_ticker(symbol=pair)
            return "USDC"
        except BinanceAPIException:
            try:
                pair = f"{symbol}USDT"
                self.client.get_symbol_ticker(symbol=pair)
                return "USDT"
            except BinanceAPIException:
                return None

    def execute_market_order(self, symbol: str, side: str, quantity: float, quote_currency: str = "USDC",
                             dry_run: bool = False) -> bool:
        """Виконює ринковий ордер (для сум >$5)"""
        trade_logger.info(f"{'='*60}")
        trade_logger.info(f"MARKET ORDER: {side} {quantity:.8f} {symbol} for {quote_currency}")
        trade_logger.info(f"Dry run: {dry_run}")
        try:
            if dry_run:
                trade_logger.info(f"[DRY RUN] Would execute MARKET {side} {quantity} {symbol}")
                print(f"[DRY RUN] MARKET {side} {quantity} {symbol}...")
                return True

            pair = f"{symbol}{quote_currency}"
            info = self.client.get_symbol_info(pair)

            if not info:
                print(f"❌ Символ {pair} не знайдено")
                return False

            step_size = None

            for f in info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    break

            if step_size:
                precision = len(str(step_size).rstrip('0').split('.')[-1])
                quantity = round(quantity, precision)

            print(f"📊 Виконується {'КУПІВЛЯ' if side == 'BUY' else 'ПРОДАЖ'} {quantity} {symbol} (MARKET ORDER)...")
            trade_logger.info(f"Executing {side} order for {pair}, quantity={quantity}")

            if side == 'BUY':
                order = self.client.order_market_buy(symbol=pair, quantity=quantity)
            else:
                order = self.client.order_market_sell(symbol=pair, quantity=quantity)

            trade_logger.info(f"[SUCCESS] Order executed successfully: {order['orderId']}")
            trade_logger.info(f"  Executed quantity: {order['executedQty']} {symbol}")
            trade_logger.info(f"  Quote quantity: {order['cummulativeQuoteQty']} {quote_currency}")
            trade_logger.info(f"  Order details: {order}")

            print(f"✅ Ордер виконано: {order['orderId']}")
            print(f"   {'Куплено' if side == 'BUY' else 'Продано'}: {order['executedQty']} {symbol}")
            print(f"   {'Витрачено' if side == 'BUY' else 'Отримано'}: {order['cummulativeQuoteQty']} {quote_currency}")
            return True

        except BinanceAPIException as e:
            error_logger.error(f"[ERROR] Binance API error for {side} {symbol}: {e}")
            error_logger.error(f"  Error code: {e.code if hasattr(e, 'code') else 'N/A'}")
            error_logger.error(traceback.format_exc())
            print(f"❌ Помилка ордеру {symbol}: {e}")
            print(f"   Error code: {e.code if hasattr(e, 'code') else 'N/A'}")
            return False
        except Exception as e:
            error_logger.error(f"[ERROR] Unknown error in market order {side} {symbol}: {e}")
            error_logger.error(traceback.format_exc())
            print(f"❌ Невідома помилка: {e}")
            traceback.print_exc()
            return False
        finally:
            trade_logger.info(f"{'='*60}")

    def execute_convert(self, from_asset: str, to_asset: str, amount: float, dry_run: bool = False) -> bool:
        """Виконує конвертацію через Binance Convert API"""
        trade_logger.info(f"{'='*60}")
        trade_logger.info(f"CONVERT: {amount:.8f} {from_asset} → {to_asset}")
        trade_logger.info(f"Dry run: {dry_run}")
        try:
            if dry_run:
                trade_logger.info(f"[DRY RUN] Would convert {amount:.8f} {from_asset} → {to_asset}")
                print(f"[DRY RUN] Конвертація {amount:.8f} {from_asset} → {to_asset}...")
                return True

            print(f"🔄 Конвертація {amount:.8f} {from_asset} → {to_asset}...")
            trade_logger.info(f"Executing convert operation...")

            # ⚠️ ВАЖЛИВО: Binance Convert API може мати інший метод залежно від версії бібліотеки
            # Варіант 1: Для python-binance >= 1.0.16
            try:
                result = self.client.convert_request_quote(
                    fromAsset=from_asset,
                    toAsset=to_asset,
                    fromAmount=amount
                )

                if result and 'quoteId' in result:
                    # Підтверджуємо конвертацію
                    confirm = self.client.convert_accept_quote(quoteId=result['quoteId'])

                    if confirm and confirm.get('status') == 'SUCCESS':
                        trade_logger.info(f"[SUCCESS] Convert executed successfully!")
                        trade_logger.info(f"  Quote ID: {result['quoteId']}")
                        trade_logger.info(f"  Converted: {amount} {from_asset}")
                        trade_logger.info(f"  Received: {result.get('toAmount', 'N/A')} {to_asset}")
                        print(f"✅ Конвертацію виконано успішно!")
                        print(f"   Quote ID: {result['quoteId']}")
                        print(f"   Конвертовано: {amount} {from_asset}")
                        print(f"   Отримано: {result.get('toAmount', 'N/A')} {to_asset}")
                        return True
                    else:
                        error_logger.error("Convert confirmation failed")
                        print(f"❌ Помилка підтвердження конвертації")
                        return False
            except AttributeError:
                # Варіант 2: Для старіших версій або альтернативного API
                print("⚠️ convert_request_quote недоступний, пробуємо convert_asset...")
                result = self.client.convert_asset(
                    fromAsset=from_asset,
                    toAsset=to_asset,
                    fromAmount=amount
                )

            if result and result.get('orderId'):
                print(f"✅ Конвертацію виконано успішно!")
                print(f"   Order ID: {result['orderId']}")
                print(f"   Конвертовано: {result.get('fromAmount', amount)} {from_asset}")
                print(f"   Отримано: {result.get('toAmount', 'N/A')} {to_asset}")
                return True
            else:
                print(f"❌ Помилка конвертації: невідома відповідь від API")
                return False

        except BinanceAPIException as e:
            error_logger.error(f"[ERROR] Binance API error converting {from_asset} -> {to_asset}: {e}")
            error_logger.error(f"  Error code: {e.code if hasattr(e, 'code') else 'N/A'}")
            error_logger.error(f"  Error message: {e.message if hasattr(e, 'message') else str(e)}")
            error_logger.error(traceback.format_exc())
            print(f"❌ Помилка конвертації {from_asset} → {to_asset}: {e}")
            print(f"   Error code: {e.code if hasattr(e, 'code') else 'N/A'}")
            print(f"   Error message: {e.message if hasattr(e, 'message') else str(e)}")
            return False
        except Exception as e:
            error_logger.error(f"[ERROR] Unknown error converting {from_asset} -> {to_asset}: {e}")
            error_logger.error(traceback.format_exc())
            print(f"❌ Невідома помилка конвертації: {e}")
            traceback.print_exc()
            return False
        finally:
            trade_logger.info(f"{'='*60}")

    def calculate_rebalancing_orders(self, current_balances: dict, target_allocation: dict,
                                     total_portfolio_value: float) -> dict:
        """
        Розширена логіка з урахуванням комісій та мінімальних балансів.

        ВАЖЛИВІ ЗМІНИ:
        1. Резерв на комісії 1% (0.1% Binance + запас)
        2. Мінімальний залишок USDC для наступних операцій
        3. Пріоритетність продажу перед купівлею
        4. Перевірка достатності коштів для кожної операції
        """
        operations = {
            'sell_orders': {},
            'sell_convert': {},
            'buy_orders': {},
            'buy_convert': {}
        }

        THRESHOLD = 5.0  # Поріг для вибору між market/convert
        FEE_RESERVE = 0.01  # 1% резерв на комісії
        MIN_USDC_RESERVE = 1.0  # Мінімальний залишок USDC після всіх операцій

        print(f"\n💵 Розрахунок операцій для ребалансування (з резервом на комісії {FEE_RESERVE * 100}%)")
        print("-" * 80)

        # Визначаємо quote currency
        quote_currency = None
        quote_balance = 0

        for stable in ['USDC', 'USDT', 'BUSD', 'FDUSD']:
            balance = current_balances.get(stable, {}).get('total', 0)
            if balance > 0.1:
                quote_currency = stable
                quote_balance = balance
                break

        if not quote_currency:
            quote_currency = 'USDC'
            quote_balance = 0
            print(f"⚠️ Немає стейблкоїнів, використовуємо {quote_currency}")
        else:
            print(f"💰 Поточний баланс {quote_currency}: ${quote_balance:.2f}")

        def can_place_market(pair: str, quantity: float, value_usdc: float) -> (bool, str):
            """Перевіряє чи можна поставити market order"""
            try:
                info = self.client.get_symbol_info(pair)
                if not info:
                    return False, "no_symbol_info"

                step_size = None
                min_notional = None

                for f in info.get('filters', []):
                    if f.get('filterType') == 'LOT_SIZE':
                        step_size = float(f.get('stepSize', '0'))
                    elif f.get('filterType') == 'MIN_NOTIONAL':
                        min_notional = float(f.get('minNotional', f.get('notional', 0) or 0))

                if step_size and quantity < step_size:
                    return False, f"below_lot_size({quantity:.8f}<{step_size})"

                if min_notional and value_usdc < min_notional:
                    return False, f"below_min_notional(${value_usdc:.2f}<{min_notional})"

                return True, "ok"
            except Exception as e:
                return False, f"symbol_info_error:{e}"

        # ✅ ЕТАП 1: Розраховуємо ПРОДАЖІ (щоб отримати USDC)
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
                continue

            # ✅ ПРОДАЖ (спочатку рахуємо всі продажі)
            if difference_value < 0:
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
                    print(f"🔴 MARKET SELL {symbol}: {quantity:,.8f} токенів на ${sell_value:,.2f}")
                else:
                    operations['sell_convert'][symbol] = {
                        'from_asset': symbol,
                        'to_asset': quote_currency,
                        'amount': sell_value,
                        'current_quantity': current_quantity,
                        'type': 'convert',
                        'reason': reason
                    }
                    print(f"🟠 CONVERT {symbol}→{quote_currency}: ${sell_value:,.2f}")

        # ✅ ЕТАП 2: Розраховуємо доступні кошти після продажу
        # Враховуємо комісії при продажу
        available_after_sell = quote_balance + (total_sell_value * (1 - FEE_RESERVE))

        print(f"\n💰 Баланс {quote_currency}:")
        print(f"   Поточний: ${quote_balance:.2f}")
        print(f"   Від продажу: ${total_sell_value:.2f} (після комісій: ${total_sell_value * (1 - FEE_RESERVE):.2f})")
        print(f"   Доступно для купівлі: ${available_after_sell:.2f}")
        print(f"   Резерв на комісії: {FEE_RESERVE * 100}%")

        # ✅ ЕТАП 3: Розраховуємо КУПІВЛІ (з урахуванням доступних коштів)
        buy_operations_temp = []  # Тимчасовий список для сортування за пріоритетом

        for symbol, target_data in target_allocation.items():
            current_value = current_balances.get(symbol, {}).get('usdc_value', 0)
            target_value = target_data['target_value']
            difference_value = target_value - current_value

            if difference_value <= 0:
                continue

            price = self.get_binance_price(symbol)
            if price == 0:
                continue

            # Враховуємо комісії при купівлі
            needed_usdc = difference_value * (1 + FEE_RESERVE)
            quantity = difference_value / price

            buy_operations_temp.append({
                'symbol': symbol,
                'quantity': quantity,
                'needed_usdc': needed_usdc,
                'difference_value': difference_value,
                'price': price,
                'priority': target_data.get('rank', 999)  # Пріоритет за рангом CMC
            })

        # Сортуємо купівлі за пріоритетом (вища капіталізація = вищий пріоритет)
        buy_operations_temp.sort(key=lambda x: x['priority'])

        # ✅ ЕТАП 4: Розподіляємо купівлі з урахуванням доступних коштів
        remaining_balance = available_after_sell - MIN_USDC_RESERVE
        total_buy_allocated = 0

        for op in buy_operations_temp:
            symbol = op['symbol']
            needed = op['needed_usdc']

            # Якщо недостатньо коштів - пропорційно зменшуємо суму
            if needed > remaining_balance:
                if remaining_balance < 1.0:  # Занадто мало коштів
                    print(
                        f"⚠️ Пропуск {symbol}: недостатньо коштів (потрібно ${needed:.2f}, є ${remaining_balance:.2f})")
                    continue

                # Зменшуємо суму пропорційно
                scale_factor = remaining_balance / needed
                op['needed_usdc'] = remaining_balance
                op['difference_value'] = op['difference_value'] * scale_factor
                op['quantity'] = op['quantity'] * scale_factor
                print(f"⚠️ Зменшено купівлю {symbol} на {(1 - scale_factor) * 100:.1f}% через нестачу коштів")

            pair = f"{symbol}{quote_currency}"
            can_market, reason = can_place_market(pair, op['quantity'], op['difference_value'])

            if op['difference_value'] > THRESHOLD and can_market:
                operations['buy_orders'][symbol] = {
                    'quantity': op['quantity'],
                    'value_usdc': op['difference_value'],
                    'price': op['price'],
                    'quote_currency': quote_currency,
                    'reason': reason
                }
                print(f"🟢 MARKET BUY {symbol}: {op['quantity']:,.8f} токенів на ${op['difference_value']:,.2f}")
            else:
                operations['buy_convert'][symbol] = {
                    'from_asset': quote_currency,
                    'to_asset': symbol,
                    'amount': op['difference_value'],
                    'type': 'convert',
                    'reason': reason
                }
                print(f"🔵 CONVERT {quote_currency}→{symbol}: ${op['difference_value']:,.2f}")

            remaining_balance -= op['needed_usdc']
            total_buy_allocated += op['difference_value']

        # ✅ ПІДСУМОК
        print(f"\n📊 ПІДСУМОК РОЗРАХУНКІВ:")
        print(f"   Продаж: ${total_sell_value:.2f}")
        print(f"   Купівля: ${total_buy_allocated:.2f}")
        print(f"   Залишок {quote_currency}: ${max(0, remaining_balance):.2f}")

        if remaining_balance < 0:
            print(f"   ⚠️ УВАГА: Бракує ${abs(remaining_balance):.2f}!")
        else:
            print(f"   ✅ Достатньо коштів")

        print("-" * 80)
        return operations

    def execute_portfolio_rebalance(self, dry_run=False):
        """
        Виконує ребалансування з покращеною логікою:
        1. Отримує поточні баланси
        2. Виконує ВСІ продажі
        3. Оновлює баланс
        4. Виконує купівлі з перевіркою коштів
        """
        trade_logger.info("=" * 80)
        trade_logger.info("[START] PORTFOLIO REBALANCE STARTED")
        trade_logger.info(f"Mode: {'DRY RUN (test)' if dry_run else 'LIVE TRADING'}")
        trade_logger.info(f"Timestamp: {datetime.now().isoformat()}")
        trade_logger.info("=" * 80)

        print("\n" + "=" * 80)
        print(f"🚀 ПОЧАТОК РЕБАЛАНСУВАННЯ ПОРТФЕЛЯ (BTC + ETH)")
        print(f"⚠️ Режим: {'DRY RUN (тестовий)' if dry_run else '🔴 РЕАЛЬНІ ОПЕРАЦІЇ! 🔴'}")
        print(f"🕐 Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        current_balances, total_portfolio_value = self.get_all_binance_balances()

        if total_portfolio_value <= 0:
            print("❌ Портфель порожній")
            return {"error": "Portfolio is empty"}

        target_allocation = self.display_btc_eth_allocation_chart(total_portfolio_value)

        if not target_allocation:
            print("❌ Не вдалося отримати дані з CoinMarketCap")
            return {"error": "Failed to fetch CMC data"}

        self.display_rebalancing_table(current_balances, target_allocation, total_portfolio_value)

        operations = self.calculate_rebalancing_orders(current_balances, target_allocation, total_portfolio_value)

        if not any(operations.values()):
            print("✅ Портфель вже збалансований")
            return {"status": "balanced", "message": "Portfolio already balanced"}

        if dry_run:
            print("\n" + "=" * 80)
            print("⚠️ DRY RUN MODE - операції НЕ будуть виконані")
            print("=" * 80)
            return {
                "status": "dry_run",
                "operations": operations,
                "message": "Dry run completed"
            }

        # ✅ РЕАЛЬНІ ОПЕРАЦІЇ З ПОКРАЩЕНОЮ ЛОГІКОЮ
        print("\n" + "=" * 80)
        print("🔴 ПОЧИНАЄМО ВИКОНАННЯ ОПЕРАЦІЙ (РЕАЛЬНІ ТРЕЙДИ!) 🔴")
        print("=" * 80)

        results = {
            "sell_orders": [],
            "sell_convert": [],
            "buy_orders": [],
            "buy_convert": []
        }

        # ✅ ЕТАП 1: ВИКОНУЄМО ВСІ ПРОДАЖІ
        if operations['sell_orders'] or operations['sell_convert']:
            print("\n" + "=" * 80)
            print("📤 ЕТАП 1: ПРОДАЖ ТОКЕНІВ")
            print("=" * 80)

            # 1.1 Market Sell Orders
            if operations['sell_orders']:
                print("\n🔴 Виконання Market Sell ордерів:")
                for symbol, data in operations['sell_orders'].items():
                    success = self.execute_market_order(
                        symbol=symbol,
                        side='SELL',
                        quantity=data['quantity'],
                        quote_currency=data['quote_currency'],
                        dry_run=False
                    )
                    results['sell_orders'].append({
                        "symbol": symbol,
                        "success": success,
                        "quantity": data['quantity']
                    })
                    if success:
                        time.sleep(1)

            # 1.2 Convert Sell
            if operations['sell_convert']:
                print("\n🟠 Виконання Convert Sell операцій:")
                for symbol, data in operations['sell_convert'].items():
                    success = self.execute_convert(
                        from_asset=data['from_asset'],
                        to_asset=data['to_asset'],
                        amount=data['current_quantity'],
                        dry_run=False
                    )
                    results['sell_convert'].append({
                        "symbol": symbol,
                        "success": success
                    })
                    if success:
                        time.sleep(2)

        # ✅ ЕТАП 1.5: ОНОВЛЮЄМО БАЛАНС ПІСЛЯ ПРОДАЖУ
        print("\n" + "=" * 80)
        print("🔄 ОНОВЛЕННЯ БАЛАНСУ ПІСЛЯ ПРОДАЖУ")
        print("=" * 80)

        time.sleep(2)  # Даємо час Binance оновити баланси
        current_balances, _ = self.get_all_binance_balances()

        # Визначаємо доступні кошти
        quote_currency = 'USDC'
        for stable in ['USDC', 'USDT', 'BUSD', 'FDUSD']:
            if current_balances.get(stable, {}).get('total', 0) > 0.1:
                quote_currency = stable
                break

        available_balance = current_balances.get(quote_currency, {}).get('total', 0)
        print(f"💰 Доступний баланс {quote_currency} після продажу: ${available_balance:.2f}")

        # ✅ ЕТАП 2: ВИКОНУЄМО КУПІВЛІ З ПЕРЕВІРКОЮ БАЛАНСУ
        if operations['buy_orders'] or operations['buy_convert']:
            print("\n" + "=" * 80)
            print("📥 ЕТАП 2: КУПІВЛЯ ТОКЕНІВ")
            print("=" * 80)

            # 2.1 Market Buy Orders
            if operations['buy_orders']:
                print("\n🟢 Виконання Market Buy ордерів:")
                for symbol, data in operations['buy_orders'].items():
                    needed = data['value_usdc'] * 1.01  # +1% на комісії

                    # ✅ ПЕРЕВІРКА ПЕРЕД КУПІВЛЕЮ
                    if needed > available_balance:
                        print(
                            f"⚠️ Пропуск {symbol}: недостатньо коштів (потрібно ${needed:.2f}, є ${available_balance:.2f})")
                        results['buy_orders'].append({
                            "symbol": symbol,
                            "success": False,
                            "error": "Insufficient balance"
                        })
                        continue

                    success = self.execute_market_order(
                        symbol=symbol,
                        side='BUY',
                        quantity=data['quantity'],
                        quote_currency=data['quote_currency'],
                        dry_run=False
                    )

                    if success:
                        available_balance -= needed
                        print(f"   💰 Залишок {quote_currency}: ${available_balance:.2f}")

                    results['buy_orders'].append({
                        "symbol": symbol,
                        "success": success,
                        "quantity": data['quantity']
                    })

                    if success:
                        time.sleep(1)

            # 2.2 Convert Buy
            if operations['buy_convert']:
                print("\n🔵 Виконання Convert Buy операцій:")
                for symbol, data in operations['buy_convert'].items():
                    needed = data['amount'] * 1.01

                    # ✅ ПЕРЕВІРКА ПЕРЕД КУПІВЛЕЮ
                    if needed > available_balance:
                        print(
                            f"⚠️ Пропуск {symbol}: недостатньо коштів (потрібно ${needed:.2f}, є ${available_balance:.2f})")
                        results['buy_convert'].append({
                            "symbol": symbol,
                            "success": False,
                            "error": "Insufficient balance"
                        })
                        continue

                    success = self.execute_convert(
                        from_asset=data['from_asset'],
                        to_asset=data['to_asset'],
                        amount=data['amount'],
                        dry_run=False
                    )

                    if success:
                        available_balance -= needed
                        print(f"   💰 Залишок {quote_currency}: ${available_balance:.2f}")

                    results['buy_convert'].append({
                        "symbol": symbol,
                        "success": success
                    })

                    if success:
                        time.sleep(2)

        print("\n" + "=" * 80)
        print("✅ РЕБАЛАНСУВАННЯ ЗАВЕРШЕНО")
        print(f"💰 Кінцевий баланс {quote_currency}: ${available_balance:.2f}")
        print("=" * 80)

        trade_logger.info("=" * 80)
        trade_logger.info("[COMPLETED] PORTFOLIO REBALANCE COMPLETED")
        trade_logger.info(f"Final balance {quote_currency}: ${available_balance:.2f}")
        trade_logger.info(f"Results summary: {results}")
        trade_logger.info("=" * 80)

        return {
            "status": "completed",
            "results": results,
            "final_balance": available_balance,
            "timestamp": datetime.now().isoformat()
        }



    def run_continuous_rebalance(self, dry_run=False):
        """Постійне ребалансування кожні N секунд згідно з .env"""
        interval_seconds = self.update_interval

        print("\n" + "=" * 80)
        print("🤖 ЗАПУСК АВТОМАТИЧНОГО РЕБАЛАНСУВАННЯ (BTC + ETH)")
        print("=" * 80)
        print(f"⏱ Інтервал оновлення: {interval_seconds} секунд ({interval_seconds / 60:.1f} хвилин)")
        print(f"⚠️ Режим: {'DRY RUN (тестовий)' if dry_run else 'РЕАЛЬНІ КОНВЕРТАЦІЇ'}")
        print(f"🕐 Запуск: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        cycle_count = 0

        while True:
            cycle_count += 1
            print(f"\n\n{'=' * 80}")
            print(f"🔄 ЦИКЛ РЕБАЛАНСУВАННЯ #{cycle_count}")
            print(f"{'=' * 80}")

            try:
                self.execute_portfolio_rebalance(dry_run=dry_run)

                next_run = datetime.now() + timedelta(seconds=interval_seconds)

                print(f"\n⏰ Наступне ребалансування через {interval_seconds} секунд")
                print(f"📅 Заплановано на: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"\n{'=' * 80}")
                print("😴 Очікування...")
                print(f"{'=' * 80}\n")

                time.sleep(interval_seconds)

            except KeyboardInterrupt:
                print("\n\n" + "=" * 80)
                print("⛔ ЗУПИНКА АВТОМАТИЧНОГО РЕБАЛАНСУВАННЯ")
                print("=" * 80)
                print(f"📊 Всього виконано циклів: {cycle_count}")
                print(f"🕐 Час зупинки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 80)
                break
            except Exception as e:
                print(f"\n❌ Помилка в циклі ребалансування: {e}")
                print(f"⏰ Спроба повторного запуску через {interval_seconds} секунд...")
                time.sleep(interval_seconds)

    def get_btc_eth_allocation_from_cmc20(self) -> dict:
        """
        Get allocation based on selected index type
        Supports: top2, top5, top10, top20
        """
        api_logger.info(f"Fetching CMC allocation for index type: {self.index_type}")

        try:
            headers = {
                'X-CMC_PRO_API_KEY': self.cmc_api_key,
                'Accept': 'application/json'
            }

            params = {
                'start': '1',
                'limit': '50',
                'convert': 'USD'
            }

            response = requests.get(self.cmc_api_url, headers=headers, params=params)
            data = response.json()

            if response.status_code != 200:
                error_msg = data.get('status', {}).get('error_message', 'Unknown error')
                error_logger.error(f"CoinMarketCap API error: {error_msg}")
                return {}

            coins = data['data']

            # Remove all stablecoins
            coins = [coin for coin in coins if coin['symbol'] not in self.stablecoins]

            # Get top 20 (without stablecoins)
            top20_coins = coins[:20]

            # Calculate total market cap
            total_market_cap = sum(coin['quote']['USD']['market_cap'] for coin in top20_coins)

            # Determine number of coins based on index type
            index_size_map = {
                'top2': 2,
                'top5': 5,
                'top10': 10,
                'top20': 20
            }

            selected_count = index_size_map.get(self.index_type, 2)

            # Get selected coins
            selected_coins = top20_coins[:selected_count]
            remaining_coins = top20_coins[selected_count:]

            # Calculate weights
            selected_market_cap = sum(coin['quote']['USD']['market_cap'] for coin in selected_coins)
            remaining_market_cap = sum(coin['quote']['USD']['market_cap'] for coin in remaining_coins)

            # Calculate redistribution per selected coin
            redistribution_per_coin = (remaining_market_cap / total_market_cap * 100) / selected_count

            # Build allocation data
            allocation_data = {}

            print(f"\n🔍 INDEX DISTRIBUTION: {self.index_type.upper()}")
            print(f"   📊 Total CMC20 market cap: ${total_market_cap:,.0f}")
            print(f"   🎯 Selected coins: {selected_count}")
            print(f"   📦 Remaining coins: {len(remaining_coins)}")
            print(f"   ➗ Redistribution per coin: +{redistribution_per_coin:.2f}%\n")

            for coin in selected_coins:
                symbol = coin['symbol']
                market_cap = coin['quote']['USD']['market_cap']
                original_weight = (market_cap / total_market_cap) * 100
                final_weight = original_weight + redistribution_per_coin

                allocation_data[symbol] = {
                    'rank': coin['cmc_rank'],
                    'name': coin['name'],
                    'original_weight': original_weight,
                    'redistribution_bonus': redistribution_per_coin,
                    'weight': final_weight,
                    'market_cap': market_cap,
                    'price': coin['quote']['USD']['price'],
                    'change_24h': coin['quote']['USD']['percent_change_24h']
                }

                print(
                    f"   {symbol:6s}: {original_weight:6.2f}% + {redistribution_per_coin:6.2f}% = {final_weight:6.2f}%")

            # Verify total is 100%
            total_weight = sum(data['weight'] for data in allocation_data.values())
            print(f"\n   ✅ Total weight: {total_weight:.2f}% (should be 100%)\n")

            api_logger.info(f"Successfully calculated {self.index_type} allocation")
            return allocation_data

        except Exception as e:
            error_logger.error(f"Error fetching CMC allocation: {e}")
            error_logger.error(traceback.format_exc())
            return {}



