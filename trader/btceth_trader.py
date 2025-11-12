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
    """
    Updated: Now supports both CMC20 and CMC100 indices
    """

    def __init__(self, binance_api_key=None, binance_api_secret=None,
                 cmc_api_key=None, update_interval=None,
                 index_type='CMC20', min_trade_threshold=5.0,
                 auto_convert_dust=True):
        """
        Initialize trader with index configuration

        Args:
            index_type: 'top2', 'top5', ..., 'top100'
            index_base: 'cmc20' or 'cmc100'
        """
        debug_logger.info("Initializing BTCETH_CMC20_Trader...")

        # Binance API - use provided credentials or fall back to .env
        self.binance_api_key = binance_api_key or os.getenv("BINANCE_API_KEY")
        self.binance_api_secret = binance_api_secret or os.getenv("BINANCE_API_SECRET")

        if not self.binance_api_key or not self.binance_api_secret:
            raise ValueError("Binance API credentials required")

        self.client = Client(self.binance_api_key, self.binance_api_secret)

        try:
            server_time = self.client.get_server_time()
            local_time = int(time.time() * 1000)
            time_offset = server_time['serverTime'] - local_time
            self.client.timestamp_offset = time_offset
        except Exception as e:
            debug_logger.warning(f"Failed to sync timestamp: {e}")

            # New configuration
        self.index_type = index_type  # 'CMC20' or 'CMC100'
        self.min_trade_threshold = min_trade_threshold
        self.auto_convert_dust = auto_convert_dust

        self.cmc_api_key = cmc_api_key or os.getenv("COINMARKETCAP_API_KEY")
        self.cmc_api_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        self.update_interval = update_interval or int(os.getenv("CMC_INDEX_UPDATE_INTERVAL", 3600))

        self.stablecoins = ['USDT', 'USDC', 'BUSD', 'FDUSD', 'USDe', 'DAI', 'TUSD', 'USDP', 'USDD', 'GUSD', 'PYUSD']

        api_logger.info(
            f"Trader initialized: index={self.index_type}, threshold=${self.min_trade_threshold}, auto_convert={self.auto_convert_dust}")

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

    def get_allocation_from_cmc(self) -> dict:
        """
        Get allocation based on selected index base and type
        Supports both CMC20 and CMC100

        Returns:
            dict: Allocation data for selected coins
        """
        api_logger.info(f"Fetching {self.index_base.upper()} allocation for {self.index_type}")

        try:
            headers = {
                'X-CMC_PRO_API_KEY': self.cmc_api_key,
                'Accept': 'application/json'
            }

            # Determine how many coins to fetch based on base
            limit = 50 if self.index_base == 'cmc20' else 150

            params = {
                'start': '1',
                'limit': str(limit),
                'convert': 'USD'
            }

            api_logger.debug(f"Calling CoinMarketCap API with limit={limit}")
            response = requests.get(self.cmc_api_url, headers=headers, params=params)
            data = response.json()

            if response.status_code != 200:
                error_msg = data.get('status', {}).get('error_message', 'Unknown error')
                error_logger.error(f"CoinMarketCap API error: {error_msg}")
                return {}

            coins = data['data']

            # Remove all stablecoins
            coins = [coin for coin in coins if coin['symbol'] not in self.stablecoins]

            # Determine base limit and selected count
            if self.index_base == 'cmc20':
                base_limit = 20
                index_map = {
                    'top2': 2, 'top5': 5, 'top10': 10, 'top20': 20
                }
            else:  # cmc100
                base_limit = 100
                index_map = {
                    'top30': 30, 'top40': 40, 'top50': 50, 'top60': 60,
                    'top70': 70, 'top80': 80, 'top90': 90, 'top100': 100
                }

            selected_count = index_map.get(self.index_type, 2)

            # Get coins within base limit
            base_coins = coins[:base_limit]

            # Calculate total market cap of base coins
            total_market_cap = sum(coin['quote']['USD']['market_cap'] for coin in base_coins)

            # Get selected coins
            selected_coins = base_coins[:selected_count]
            remaining_coins = base_coins[selected_count:]

            # Calculate market caps
            selected_market_cap = sum(coin['quote']['USD']['market_cap'] for coin in selected_coins)
            remaining_market_cap = sum(coin['quote']['USD']['market_cap'] for coin in remaining_coins)

            # Calculate redistribution per selected coin
            redistribution_per_coin = (remaining_market_cap / total_market_cap * 100) / selected_count

            # Build allocation data
            allocation_data = {}

            print(f"\n{'=' * 80}")
            print(f"🔍 INDEX DISTRIBUTION: {self.index_base.upper()} - {self.index_type.upper()}")
            print(f"{'=' * 80}")
            print(f"   📊 Total {self.index_base.upper()} market cap: ${total_market_cap:,.0f}")
            print(f"   🎯 Selected coins: {selected_count}")
            print(f"   📦 Remaining coins in base: {len(remaining_coins)}")
            print(f"   ➗ Redistribution per coin: +{redistribution_per_coin:.4f}%")
            print(f"{'=' * 80}\n")

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

                print(f"   #{coin['cmc_rank']:2d} {symbol:8s}: "
                      f"{original_weight:6.2f}% + {redistribution_per_coin:6.2f}% = "
                      f"{final_weight:6.2f}%")

            # Verify total is 100%
            total_weight = sum(data['weight'] for data in allocation_data.values())
            print(f"\n   {'=' * 76}")
            print(f"   ✅ Total weight: {total_weight:.4f}% (should be ≈100%)")
            print(f"   {'=' * 76}\n")

            api_logger.info(f"Successfully calculated {self.index_base.upper()} - {self.index_type} allocation")
            api_logger.info(f"Selected {len(allocation_data)} coins with total weight: {total_weight:.2f}%")

            return allocation_data

        except Exception as e:
            error_logger.error(f"Error fetching {self.index_base.upper()} allocation: {e}")
            error_logger.error(traceback.format_exc())
            return {}

    def display_allocation_chart(self, total_portfolio_value: float):
        """
        Display allocation chart for selected index
        Works with both CMC20 and CMC100
        """
        print("\n" + "=" * 120)
        print(f"📈 PORTFOLIO ALLOCATION ({self.index_base.upper()} - {self.index_type.upper()})")
        print("=" * 120)

        allocation_data = self.get_allocation_from_cmc()

        if not allocation_data:
            print("❌ Failed to retrieve index data")
            return {}

        print(f"\n💼 Total Portfolio Value: ${total_portfolio_value:,.2f} USDC")
        print(f"🎯 Target Distribution: {len(allocation_data)} coins from {self.index_base.upper()}\n")

        # Sort by rank
        sorted_coins = sorted(allocation_data.items(), key=lambda x: x[1]['rank'])

        print("┌" + "─" * 118 + "┐")
        print(f"│ {'#':>3} │ {'Token':^8} │ {'Name':<18} │ {'Original %':>12} │ {'Bonus %':>10} │ "
              f"{'Final %':>12} │ {'Target USD':>16} │ {'Price':>14} │ {'24h %':>8} │")
        print("├" + "─" * 118 + "┤")

        final_allocation = {}
        total_allocated = 0.0

        for symbol, data in sorted_coins:
            target_value = total_portfolio_value * (data['weight'] / 100)
            total_allocated += target_value

            final_allocation[symbol] = {
                'weight': data['weight'] / 100,
                'target_value': target_value,
                'price': data['price'],
                'change_24h': data['change_24h'],
                'rank': data['rank']
            }

            change_prefix = "+" if data['change_24h'] >= 0 else ""

            print(f"│ {data['rank']:>3} │ {symbol:^8} │ {data['name']:<18.18} │ "
                  f"{data['original_weight']:>11.2f}% │ {data['redistribution_bonus']:>9.2f}% │ "
                  f"{data['weight']:>11.2f}% │ ${target_value:>14,.2f} │ "
                  f"${data['price']:>13,.2f} │ {change_prefix}{data['change_24h']:>7.2f}% │")

        print("└" + "─" * 118 + "┘")

        print(f"\n💼 Total Allocated: ${total_allocated:,.2f} USDC")
        print(f"📊 Average bonus per coin: +{allocation_data[next(iter(allocation_data))]['redistribution_bonus']:.4f}%")
        print(f"⚖️ Number of coins: {len(allocation_data)}")
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

    def can_place_market_order(self, pair: str, quantity: float, value: float) -> tuple:
        """
        Check if market order can be placed for given pair

        Args:
            pair: Trading pair (e.g., "BTCUSDC")
            quantity: Amount to trade
            value: Value in quote currency (USD)

        Returns:
            tuple: (can_place: bool, reason: str, details: dict)
        """
        try:
            # Get symbol info from Binance
            symbol_info = self.client.get_symbol_info(pair)

            if not symbol_info:
                return False, f"Symbol {pair} not found", {}

            # Check if symbol is trading
            if symbol_info['status'] != 'TRADING':
                return False, f"Symbol {pair} not trading (status: {symbol_info['status']})", {}

            # Get filters
            filters = {f['filterType']: f for f in symbol_info['filters']}

            # Check LOT_SIZE filter (quantity constraints)
            if 'LOT_SIZE' in filters:
                lot_filter = filters['LOT_SIZE']
                min_qty = float(lot_filter['minQty'])
                max_qty = float(lot_filter['maxQty'])
                step_size = float(lot_filter['stepSize'])

                if quantity < min_qty:
                    return False, f"Quantity {quantity} below minimum {min_qty}", {
                        'min_qty': min_qty,
                        'max_qty': max_qty,
                        'step_size': step_size
                    }

                if quantity > max_qty:
                    return False, f"Quantity {quantity} above maximum {max_qty}", {
                        'min_qty': min_qty,
                        'max_qty': max_qty,
                        'step_size': step_size
                    }

            # Check MIN_NOTIONAL filter (minimum order value)
            if 'MIN_NOTIONAL' in filters:
                min_notional = float(filters['MIN_NOTIONAL']['minNotional'])

                if value < min_notional:
                    return False, f"Order value ${value:.2f} below minimum ${min_notional:.2f}", {
                        'min_notional': min_notional,
                        'order_value': value
                    }

            # Check NOTIONAL filter (alternative to MIN_NOTIONAL)
            if 'NOTIONAL' in filters:
                min_notional = float(filters['NOTIONAL']['minNotional'])

                if value < min_notional:
                    return False, f"Order value ${value:.2f} below minimum ${min_notional:.2f}", {
                        'min_notional': min_notional,
                        'order_value': value
                    }

            # Check MARKET_LOT_SIZE if exists
            if 'MARKET_LOT_SIZE' in filters:
                market_filter = filters['MARKET_LOT_SIZE']
                min_qty = float(market_filter['minQty'])
                max_qty = float(market_filter['maxQty'])

                if quantity < min_qty:
                    return False, f"Market order quantity {quantity} below minimum {min_qty}", {
                        'market_min_qty': min_qty,
                        'market_max_qty': max_qty
                    }

                if quantity > max_qty:
                    return False, f"Market order quantity {quantity} above maximum {max_qty}", {
                        'market_min_qty': min_qty,
                        'market_max_qty': max_qty
                    }

            # All checks passed
            return True, "OK", {
                'pair': pair,
                'quantity': quantity,
                'value': value
            }

        except BinanceAPIException as e:
            error_logger.error(f"Binance API error checking {pair}: {e}")
            return False, f"API error: {str(e)}", {}

        except Exception as e:
            error_logger.error(f"Error checking {pair}: {e}")
            error_logger.error(traceback.format_exc())
            return False, f"Unknown error: {str(e)}", {}

    def calculate_rebalancing_orders(self, current_balances: dict, target_allocation: dict,
                                     total_portfolio_value: float) -> dict:
        """
        ПОКРАЩЕНА логіка розрахунку з автоматичним вибором методу
        """
        operations = {
            'sell_orders': {},
            'sell_convert': {},
            'buy_orders': {},
            'buy_convert': {},
            'dust_to_convert': {}  # NEW: малі залишки для конвертації
        }

        FEE_RESERVE = 0.01
        MIN_USDC_RESERVE = 1.0

        print(f"\n💵 Розрахунок операцій (поріг market order: ${self.min_trade_threshold})")
        print("-" * 80)

        # Determine quote currency
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

        print(f"💰 Quote currency: {quote_currency}, баланс: ${quote_balance:.2f}")

        total_sell_value = 0
        dust_balances = {}  # Collect dust

        # PHASE 1: Calculate SELLS
        for symbol, target_data in target_allocation.items():
            current_value = current_balances.get(symbol, {}).get('usdc_value', 0)
            current_quantity = current_balances.get(symbol, {}).get('total', 0)
            target_value = target_data['target_value']
            difference_value = target_value - current_value

            if abs(difference_value) < 0.5:  # Skip very small differences
                continue

            price = self.get_binance_price(symbol)
            if price == 0:
                continue

            # SELL operations
            if difference_value < 0:
                sell_value = abs(difference_value)
                quantity = sell_value / price
                total_sell_value += sell_value

                pair = f"{symbol}{quote_currency}"
                can_place, reason, details = self.can_place_market_order(pair, quantity, sell_value)

                # Decision: market order or convert?
                if sell_value >= self.min_trade_threshold and can_place:
                    operations['sell_orders'][symbol] = {
                        'quantity': quantity,
                        'value_usdc': sell_value,
                        'price': price,
                        'quote_currency': quote_currency,
                        'reason': reason
                    }
                    print(f"🔴 MARKET SELL {symbol}: {quantity:,.8f} (${sell_value:,.2f})")
                else:
                    # Use convert for values >= $5 that can't use market order
                    # OR values < $5
                    if sell_value >= self.min_trade_threshold:
                        print(f"🟠 CONVERT {symbol}→{quote_currency}: ${sell_value:,.2f} (причина: {reason})")
                    else:
                        print(f"🧹 DUST {symbol}: ${sell_value:,.2f} (буде конвертовано)")
                        dust_balances[symbol] = current_quantity

                    operations['sell_convert'][symbol] = {
                        'from_asset': symbol,
                        'to_asset': quote_currency,
                        'amount': current_quantity,
                        'value': sell_value,
                        'type': 'convert',
                        'reason': reason,
                        'is_dust': sell_value < self.min_trade_threshold
                    }

        # Calculate available balance after sells
        available_after_sell = quote_balance + (total_sell_value * (1 - FEE_RESERVE))

        print(f"\n💰 Баланс після продажу: ${available_after_sell:.2f}")

        # PHASE 2: Calculate BUYS
        buy_operations_temp = []

        for symbol, target_data in target_allocation.items():
            current_value = current_balances.get(symbol, {}).get('usdc_value', 0)
            target_value = target_data['target_value']
            difference_value = target_value - current_value

            if difference_value <= 0.5:
                continue

            price = self.get_binance_price(symbol)
            if price == 0:
                continue

            needed_usdc = difference_value * (1 + FEE_RESERVE)
            quantity = difference_value / price

            buy_operations_temp.append({
                'symbol': symbol,
                'quantity': quantity,
                'needed_usdc': needed_usdc,
                'difference_value': difference_value,
                'price': price,
                'priority': target_data.get('rank', 999)
            })

        # Sort by priority
        buy_operations_temp.sort(key=lambda x: x['priority'])

        # PHASE 3: Allocate buys
        remaining_balance = available_after_sell - MIN_USDC_RESERVE

        for op in buy_operations_temp:
            symbol = op['symbol']
            needed = op['needed_usdc']

            if needed > remaining_balance:
                if remaining_balance < 1.0:
                    print(f"⚠️ Пропуск {symbol}: недостатньо коштів")
                    continue

                scale_factor = remaining_balance / needed
                op['needed_usdc'] = remaining_balance
                op['difference_value'] = op['difference_value'] * scale_factor
                op['quantity'] = op['quantity'] * scale_factor

            pair = f"{symbol}{quote_currency}"
            can_place, reason, details = self.can_place_market_order(
                pair, op['quantity'], op['difference_value']
            )

            # Decision: market order or convert?
            if op['difference_value'] >= self.min_trade_threshold and can_place:
                operations['buy_orders'][symbol] = {
                    'quantity': op['quantity'],
                    'value_usdc': op['difference_value'],
                    'price': op['price'],
                    'quote_currency': quote_currency,
                    'reason': reason
                }
                print(f"🟢 MARKET BUY {symbol}: {op['quantity']:,.8f} (${op['difference_value']:,.2f})")
            else:
                if op['difference_value'] >= self.min_trade_threshold:
                    print(f"🔵 CONVERT {quote_currency}→{symbol}: ${op['difference_value']:,.2f} (причина: {reason})")
                else:
                    print(f"🔵 CONVERT {quote_currency}→{symbol}: ${op['difference_value']:,.2f} (< порогу)")

                operations['buy_convert'][symbol] = {
                    'from_asset': quote_currency,
                    'to_asset': symbol,
                    'amount': op['difference_value'],
                    'type': 'convert',
                    'reason': reason
                }

            remaining_balance -= op['needed_usdc']

        # Store dust for later conversion
        if dust_balances:
            operations['dust_to_convert'] = dust_balances

        print("-" * 80)
        return operations

    def execute_portfolio_rebalance(self, dry_run=False):
        """
        ПОКРАЩЕНЕ виконання ребалансування з конвертацією залишків
        """
        trade_logger.info("=" * 80)
        trade_logger.info(f"[START] REBALANCE - Index: {self.index_type}, Dry run: {dry_run}")
        trade_logger.info("=" * 80)

        print(f"\n🚀 РЕБАЛАНСУВАННЯ ({self.index_type})")
        print(f"⚠️ Режим: {'DRY RUN' if dry_run else '🔴 LIVE'}")
        print("=" * 80)

        # Get current state
        current_balances, total_portfolio_value = self.get_all_binance_balances()

        if total_portfolio_value <= 0:
            return {"error": "Portfolio empty"}

        # Get target allocation based on selected index
        target_allocation = self.get_btc_eth_allocation_from_cmc()

        if not target_allocation:
            return {"error": "Failed to fetch CMC data"}

        # Calculate target values
        for symbol, data in target_allocation.items():
            data['target_value'] = total_portfolio_value * (data['weight'] / 100)

        # Calculate operations
        operations = self.calculate_rebalancing_orders(
            current_balances, target_allocation, total_portfolio_value
        )

        if dry_run:
            return {
                "status": "dry_run",
                "operations": operations,
                "index_type": self.index_type
            }

        # Execute operations
        results = {
            "sell_orders": [],
            "sell_convert": [],
            "buy_orders": [],
            "buy_convert": [],
            "dust_conversion": {}
        }

        # PHASE 1: SELLS
        if operations['sell_orders'] or operations['sell_convert']:
            print("\n📤 ФАЗА 1: ПРОДАЖ")
            print("=" * 80)

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

            for symbol, data in operations['sell_convert'].items():
                if not data.get('is_dust'):  # Process non-dust converts now
                    success = self.execute_convert(
                        from_asset=data['from_asset'],
                        to_asset=data['to_asset'],
                        amount=data['amount'],
                        dry_run=False
                    )
                    results['sell_convert'].append({
                        "symbol": symbol,
                        "success": success
                    })
                    if success:
                        time.sleep(2)

        # PHASE 1.5: Update balance
        time.sleep(2)
        current_balances, _ = self.get_all_binance_balances()

        quote_currency = 'USDC'
        for stable in ['USDC', 'USDT', 'BUSD', 'FDUSD']:
            if current_balances.get(stable, {}).get('total', 0) > 0.1:
                quote_currency = stable
                break

        available_balance = current_balances.get(quote_currency, {}).get('total', 0)
        print(f"\n💰 Доступно після продажу: ${available_balance:.2f} {quote_currency}")

        # PHASE 2: BUYS
        if operations['buy_orders'] or operations['buy_convert']:
            print("\n📥 ФАЗА 2: КУПІВЛЯ")
            print("=" * 80)

            for symbol, data in operations['buy_orders'].items():
                needed = data['value_usdc'] * 1.01

                if needed > available_balance:
                    print(f"⚠️ Пропуск {symbol}: недостатньо коштів")
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
                    time.sleep(1)

                results['buy_orders'].append({
                    "symbol": symbol,
                    "success": success
                })

            for symbol, data in operations['buy_convert'].items():
                needed = data['amount'] * 1.01

                if needed > available_balance:
                    print(f"⚠️ Пропуск {symbol}: недостатньо коштів")
                    continue

                success = self.execute_convert(
                    from_asset=data['from_asset'],
                    to_asset=data['to_asset'],
                    amount=data['amount'],
                    dry_run=False
                )

                if success:
                    available_balance -= needed
                    time.sleep(2)

                results['buy_convert'].append({
                    "symbol": symbol,
                    "success": success
                })

        # PHASE 3: Convert dust to larger positions
        if operations.get('dust_to_convert') and self.auto_convert_dust:
            print("\n🧹 ФАЗА 3: КОНВЕРТАЦІЯ ЗАЛИШКІВ")
            print("=" * 80)

            # Determine which asset has lower allocation (needs more)
            current_btc = current_balances.get('BTC', {}).get('usdc_value', 0)
            current_eth = current_balances.get('ETH', {}).get('usdc_value', 0)
            target_btc = target_allocation['BTC']['target_value']
            target_eth = target_allocation['ETH']['target_value']

            btc_shortage = target_btc - current_btc
            eth_shortage = target_eth - current_eth

            # Convert to the asset with bigger shortage
            target_for_dust = 'BTC' if btc_shortage > eth_shortage else 'ETH'

            print(f"🎯 Залишки конвертуються в {target_for_dust}")
            print(f"   BTC дефіцит: ${btc_shortage:.2f}")
            print(f"   ETH дефіцит: ${eth_shortage:.2f}")

            dust_results = self.convert_dust_to_target(
                operations['dust_to_convert'],
                target_for_dust,
                quote_currency
            )

            results['dust_conversion'] = dust_results

        # Final summary
        print("\n✅ РЕБАЛАНСУВАННЯ ЗАВЕРШЕНО")
        print(f"💰 Кінцевий баланс {quote_currency}: ${available_balance:.2f}")
        print("=" * 80)

        return {
            "status": "completed",
            "results": results,
            "index_type": self.index_type,
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

    def get_btc_eth_allocation_from_cmc(self) -> dict:
        """
        Отримує топ-N токенів (20 або 100), бере ваги BTC та ETH + перерозподіл решти
        """
        index_size = 20 if self.index_type == 'CMC20' else 100
        api_logger.info(f"Fetching CMC Top {index_size} allocation data...")

        try:
            headers = {
                'X-CMC_PRO_API_KEY': self.cmc_api_key,
                'Accept': 'application/json'
            }

            # Fetch more to account for stablecoins
            fetch_limit = index_size + 30

            params = {
                'start': '1',
                'limit': str(fetch_limit),
                'convert': 'USD'
            }

            response = requests.get(self.cmc_api_url, headers=headers, params=params)
            data = response.json()

            if response.status_code != 200:
                error_msg = data.get('status', {}).get('error_message', 'Unknown error')
                error_logger.error(f"CoinMarketCap API error: {error_msg}")
                return {}

            coins = data['data']

            # Remove stablecoins
            coins = [coin for coin in coins if coin['symbol'] not in self.stablecoins]

            # Take top N (without stablecoins)
            top_coins = coins[:index_size]

            # Calculate total market cap
            total_market_cap = sum(coin['quote']['USD']['market_cap'] for coin in top_coins)

            # Find BTC and ETH
            btc_data = None
            eth_data = None
            other_total_market_cap = 0.0

            for coin in top_coins:
                market_cap = coin['quote']['USD']['market_cap']

                if coin['symbol'] == 'BTC':
                    btc_data = coin
                elif coin['symbol'] == 'ETH':
                    eth_data = coin
                else:
                    other_total_market_cap += market_cap

            if not btc_data or not eth_data:
                error_logger.error(f"BTC or ETH not found in CMC Top {index_size}")
                return {}

            # Calculate weights
            btc_original_weight = (btc_data['quote']['USD']['market_cap'] / total_market_cap) * 100
            eth_original_weight = (eth_data['quote']['USD']['market_cap'] / total_market_cap) * 100
            other_weight = (other_total_market_cap / total_market_cap) * 100

            # Split remaining tokens 50/50
            redistribution_per_token = other_weight / 2

            btc_final_weight = btc_original_weight + redistribution_per_token
            eth_final_weight = eth_original_weight + redistribution_per_token

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

            print(f"\n🔍 РОЗПОДІЛ {self.index_type} (50/50):")
            print(f"   📊 Топ-{index_size} капіталізація: ${total_market_cap:,.0f}")
            print(f"   💰 BTC: {btc_original_weight:.2f}% → {btc_final_weight:.2f}%")
            print(f"   💰 ETH: {eth_original_weight:.2f}% → {eth_final_weight:.2f}%")
            print(f"   📦 Решта {index_size - 2}: {other_weight:.2f}% → розподілено 50/50")
            print(f"   ✅ Сума: {btc_final_weight + eth_final_weight:.2f}%\n")

            api_logger.info(f"{self.index_type} allocation: BTC={btc_final_weight:.2f}%, ETH={eth_final_weight:.2f}%")
            return allocation_data

        except Exception as e:
            error_logger.error(f"Error fetching {self.index_type}: {e}")
            error_logger.error(traceback.format_exc())
            return {}

    def convert_dust_to_target(self, dust_balances: dict, target_asset: str,
                               quote_currency: str = 'USDC') -> dict:
        """
        Конвертує малі залишки (пил) в цільовий актив

        Args:
            dust_balances: {'BTC': 0.00001, 'ETH': 0.0001, ...}
            target_asset: 'BTC' or 'ETH'
            quote_currency: проміжна валюта для конвертації

        Returns:
            {'converted': [...], 'failed': [...], 'total_value': 0.0}
        """
        if not self.auto_convert_dust:
            return {'converted': [], 'failed': [], 'total_value': 0.0}

        print(f"\n🧹 КОНВЕРТАЦІЯ ЗАЛИШКІВ В {target_asset}")
        print("=" * 80)

        results = {
            'converted': [],
            'failed': [],
            'total_value': 0.0
        }

        for symbol, quantity in dust_balances.items():
            if symbol == target_asset:
                continue

            # Calculate value
            price = self.get_binance_price(symbol)
            if price == 0:
                results['failed'].append({
                    'symbol': symbol,
                    'reason': 'price_unavailable'
                })
                continue

            value_usdc = quantity * price

            if value_usdc < 0.10:  # Skip very small amounts
                print(f"   ⏭️ Пропуск {symbol}: ${value_usdc:.4f} (занадто мало)")
                continue

            print(f"   🔄 Конвертація {quantity:.8f} {symbol} (${value_usdc:.2f}) → {target_asset}")

            # Try direct conversion first
            try:
                success = self.execute_convert(
                    from_asset=symbol,
                    to_asset=target_asset,
                    amount=quantity,
                    dry_run=False
                )

                if success:
                    results['converted'].append({
                        'symbol': symbol,
                        'quantity': quantity,
                        'value': value_usdc,
                        'method': 'direct'
                    })
                    results['total_value'] += value_usdc
                    time.sleep(1)
                    continue
            except Exception as e:
                debug_logger.debug(f"Direct convert failed for {symbol}: {e}")

            # Try two-step conversion: symbol → quote → target
            try:
                # Step 1: symbol → quote_currency
                success1 = self.execute_convert(
                    from_asset=symbol,
                    to_asset=quote_currency,
                    amount=quantity,
                    dry_run=False
                )

                if not success1:
                    raise Exception("Step 1 failed")

                time.sleep(1)

                # Step 2: quote_currency → target_asset
                # Get new balance of quote_currency
                balance = self.client.get_asset_balance(asset=quote_currency)
                quote_amount = float(balance['free'])

                if quote_amount < 0.10:
                    raise Exception("Insufficient quote currency after step 1")

                success2 = self.execute_convert(
                    from_asset=quote_currency,
                    to_asset=target_asset,
                    amount=quote_amount,
                    dry_run=False
                )

                if success2:
                    results['converted'].append({
                        'symbol': symbol,
                        'quantity': quantity,
                        'value': value_usdc,
                        'method': 'two_step'
                    })
                    results['total_value'] += value_usdc
                    time.sleep(1)
                else:
                    raise Exception("Step 2 failed")

            except Exception as e:
                print(f"   ❌ Помилка: {e}")
                results['failed'].append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'value': value_usdc,
                    'reason': str(e)
                })

        print("=" * 80)
        print(f"✅ Конвертовано: {len(results['converted'])} активів на ${results['total_value']:.2f}")
        print(f"❌ Помилки: {len(results['failed'])} активів")
        print("=" * 80 + "\n")

        return results



