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
    Trader that supports both CMC20 and CMC100 indices with flexible distribution
    """

    def __init__(self, binance_api_key=None, binance_api_secret=None,
                 cmc_api_key=None, update_interval=None,
                 index_type='CMC20', min_trade_threshold=5.0,
                 auto_convert_dust=True):
        """
        Initialize trader with index configuration

        Args:
            index_type: 'CMC20' or 'CMC100' (base index)
            min_trade_threshold: Minimum value for market orders (USD)
            auto_convert_dust: Automatically convert small balances
        """
        debug_logger.info("Initializing BTCETH_CMC20_Trader...")

        # Binance API - use provided credentials or fall back to .env
        self.binance_api_key = binance_api_key or os.getenv("BINANCE_API_KEY")
        self.binance_api_secret = binance_api_secret or os.getenv("BINANCE_API_SECRET")

        if not self.binance_api_key or not self.binance_api_secret:
            raise ValueError("Binance API credentials required")

        self.client = Client(self.binance_api_key, self.binance_api_secret)

        # Synchronize timestamp with Binance server
        try:
            server_time = self.client.get_server_time()
            local_time = int(time.time() * 1000)
            time_offset = server_time['serverTime'] - local_time
            self.client.timestamp_offset = time_offset
            debug_logger.info(f"Timestamp synchronized. Offset: {time_offset}ms")
        except Exception as e:
            debug_logger.warning(f"Failed to sync timestamp: {e}")

        # Configuration
        self.index_type = index_type  # 'CMC20' or 'CMC100'
        self.min_trade_threshold = min_trade_threshold
        self.auto_convert_dust = auto_convert_dust

        self.cmc_api_key = cmc_api_key or os.getenv("COINMARKETCAP_API_KEY")
        self.cmc_api_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        self.update_interval = update_interval or int(os.getenv("CMC_INDEX_UPDATE_INTERVAL", 3600))

        self.stablecoins = ['USDT', 'USDC', 'BUSD', 'FDUSD', 'USDe', 'DAI', 'TUSD', 'USDP', 'USDD', 'GUSD', 'PYUSD']

        api_logger.info(
            f"Trader initialized: index={self.index_type}, threshold=${self.min_trade_threshold}, auto_convert={self.auto_convert_dust}")

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

    def get_all_binance_balances(self) -> tuple:
        """Get all Binance balances with USDC value"""
        api_logger.info("Fetching all Binance balances...")
        try:
            account = self.client.get_account()
            balances = {}
            total_portfolio_usdc = 0.0

            print("\n💼 Current Binance balances:")
            print("-" * 90)

            for balance in account['balances']:
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked

                if total > 0:
                    asset = balance['asset']

                    # Calculate USDC value
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

                    print(f"{asset:6s} | Free: {free:12,.6f} | Locked: {locked:12,.6f} | "
                          f"≈ ${usdc_value:10,.2f} USDC")

            print("-" * 90)
            print(f"{'TOTAL':6s} | {'':12s}   {'':12s}   {'':15s}   ≈ ${total_portfolio_usdc:10,.2f} USDC")
            print("-" * 90)

            api_logger.info(f"Successfully fetched balances: {len(balances)} assets, total=${total_portfolio_usdc:.2f}")
            return balances, total_portfolio_usdc

        except BinanceAPIException as e:
            error_logger.error(f"Binance API error fetching balances: {e}")
            error_logger.error(traceback.format_exc())
            return {}, 0.0

    def get_allocation_from_cmc(self, index_base='cmc20', index_type='top2') -> dict:
        """
        Get allocation based on selected index base and type
        Supports both CMC20 and CMC100

        Args:
            index_base: 'cmc20' or 'cmc100'
            index_type: 'top2', 'top5', ..., 'top100'

        Returns:
            dict: Allocation data for selected coins
        """
        api_logger.info(f"Fetching {index_base.upper()} allocation for {index_type}")

        try:
            headers = {
                'X-CMC_PRO_API_KEY': self.cmc_api_key,
                'Accept': 'application/json'
            }

            # Determine how many coins to fetch based on base
            limit = 50 if index_base == 'cmc20' else 150

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
            if index_base == 'cmc20':
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

            selected_count = index_map.get(index_type, 2)

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
            print(f"🔍 INDEX DISTRIBUTION: {index_base.upper()} - {index_type.upper()}")
            print(f"{'=' * 80}")
            print(f"   📊 Total {index_base.upper()} market cap: ${total_market_cap:,.0f}")
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

            api_logger.info(f"Successfully calculated {index_base.upper()} - {index_type} allocation")
            api_logger.info(f"Selected {len(allocation_data)} coins with total weight: {total_weight:.2f}%")

            return allocation_data

        except Exception as e:
            error_logger.error(f"Error fetching {index_base.upper()} allocation: {e}")
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
        """Get current token price on Binance"""
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
                error_logger.error(f"Failed to get price for {symbol}: {e}")
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
        """Execute market order"""
        trade_logger.info(f"{'=' * 60}")
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
                print(f"❌ Symbol {pair} not found")
                return False

            # Get LOT_SIZE filter
            step_size = None
            for f in info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    break

            if step_size:
                precision = len(str(step_size).rstrip('0').split('.')[-1])
                quantity = round(quantity, precision)

            print(f"📊 Executing {'BUY' if side == 'BUY' else 'SELL'} {quantity} {symbol} (MARKET ORDER)...")
            trade_logger.info(f"Executing {side} order for {pair}, quantity={quantity}")

            if side == 'BUY':
                order = self.client.order_market_buy(symbol=pair, quantity=quantity)
            else:
                order = self.client.order_market_sell(symbol=pair, quantity=quantity)

            trade_logger.info(f"[SUCCESS] Order executed: {order['orderId']}")
            print(f"✅ Order executed: {order['orderId']}")
            return True

        except BinanceAPIException as e:
            error_logger.error(f"[ERROR] Binance API error for {side} {symbol}: {e}")
            error_logger.error(traceback.format_exc())
            print(f"❌ Order error {symbol}: {e}")
            return False
        except Exception as e:
            error_logger.error(f"[ERROR] Unknown error in market order {side} {symbol}: {e}")
            error_logger.error(traceback.format_exc())
            print(f"❌ Unknown error: {e}")
            return False
        finally:
            trade_logger.info(f"{'=' * 60}")

    def execute_convert(self, from_asset: str, to_asset: str, amount: float, dry_run: bool = False) -> bool:
        """Execute conversion via Binance Convert API"""
        trade_logger.info(f"{'=' * 60}")
        trade_logger.info(f"CONVERT: {amount:.8f} {from_asset} → {to_asset}")
        trade_logger.info(f"Dry run: {dry_run}")

        try:
            if dry_run:
                trade_logger.info(f"[DRY RUN] Would convert {amount:.8f} {from_asset} → {to_asset}")
                print(f"[DRY RUN] Convert {amount:.8f} {from_asset} → {to_asset}...")
                return True

            print(f"🔄 Converting {amount:.8f} {from_asset} → {to_asset}...")

            try:
                result = self.client.convert_request_quote(
                    fromAsset=from_asset,
                    toAsset=to_asset,
                    fromAmount=amount
                )

                if result and 'quoteId' in result:
                    confirm = self.client.convert_accept_quote(quoteId=result['quoteId'])

                    if confirm and confirm.get('status') == 'SUCCESS':
                        trade_logger.info(f"[SUCCESS] Convert executed successfully!")
                        print(f"✅ Conversion completed!")
                        return True
                    else:
                        print(f"❌ Conversion confirmation failed")
                        return False
            except AttributeError:
                result = self.client.convert_asset(
                    fromAsset=from_asset,
                    toAsset=to_asset,
                    fromAmount=amount
                )

                if result and result.get('orderId'):
                    print(f"✅ Conversion completed!")
                    return True

            return False

        except BinanceAPIException as e:
            error_logger.error(f"[ERROR] Binance API error converting {from_asset} -> {to_asset}: {e}")
            error_logger.error(traceback.format_exc())
            print(f"❌ Conversion error: {e}")
            return False
        except Exception as e:
            error_logger.error(f"[ERROR] Unknown error converting: {e}")
            error_logger.error(traceback.format_exc())
            print(f"❌ Unknown error: {e}")
            return False
        finally:
            trade_logger.info(f"{'=' * 60}")

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
        IMPROVED: Calculate operations to match EXACT CMC allocation
        SELLS ALL tokens not in target_allocation
        BUYS ONLY tokens in target_allocation to match weights
        """
        operations = {
            'sell_orders': {},
            'sell_convert': {},
            'buy_orders': {},
            'buy_convert': {},
            'tokens_to_remove': []  # NEW: Track tokens to completely remove
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

        print(f"💰 Quote currency: {quote_currency}, баланс: ${quote_balance:.2f}\n")

        # Get list of target symbols (what we WANT to have)
        target_symbols = set(target_allocation.keys())
        print(f"🎯 Target tokens: {', '.join(sorted(target_symbols))}")

        # Get list of current symbols (what we HAVE now)
        current_symbols = set(current_balances.keys()) - set(self.stablecoins)
        print(f"📦 Current tokens: {', '.join(sorted(current_symbols))}\n")

        # NEW: Find tokens to REMOVE (in portfolio but NOT in target)
        tokens_to_remove = current_symbols - target_symbols

        if tokens_to_remove:
            print(f"🗑️ Tokens to REMOVE (not in target index):")
            for symbol in sorted(tokens_to_remove):
                current_value = current_balances.get(symbol, {}).get('usdc_value', 0)
                current_quantity = current_balances.get(symbol, {}).get('total', 0)
                print(f"   ❌ {symbol}: {current_quantity:.8f} (${current_value:.2f})")
                operations['tokens_to_remove'].append({
                    'symbol': symbol,
                    'quantity': current_quantity,
                    'value': current_value
                })
            print()

        total_sell_value = 0

        # PHASE 1: SELL everything NOT in target + SELL excess of tokens that ARE in target
        print("📤 PHASE 1: ПРОДАЖ")
        print("-" * 80)

        for symbol in current_symbols:
            current_value = current_balances.get(symbol, {}).get('usdc_value', 0)
            current_quantity = current_balances.get(symbol, {}).get('total', 0)

            # Check if token should be in portfolio
            if symbol not in target_symbols:
                # SELL EVERYTHING - token not in target index
                sell_value = current_value
                quantity = current_quantity

                if sell_value < 0.1:
                    continue  # Skip dust

                print(f"🗑️ REMOVE {symbol}: {quantity:.8f} (${sell_value:.2f}) - NOT IN INDEX")

            else:
                # Token IS in target - check if we need to reduce position
                target_value = target_allocation[symbol]['target_value']
                difference_value = target_value - current_value

                if difference_value >= -0.5:  # No need to sell
                    continue

                sell_value = abs(difference_value)
                quantity = sell_value / self.get_binance_price(symbol)

                print(f"🔻 REDUCE {symbol}: {quantity:.8f} (${sell_value:.2f})")

            # Decide: market order or convert
            price = self.get_binance_price(symbol)
            if price == 0:
                continue

            total_sell_value += sell_value

            pair = f"{symbol}{quote_currency}"
            can_place, reason, details = self.can_place_market_order(pair, quantity, sell_value)

            if sell_value >= self.min_trade_threshold and can_place:
                operations['sell_orders'][symbol] = {
                    'quantity': quantity,
                    'value_usdc': sell_value,
                    'price': price,
                    'quote_currency': quote_currency,
                    'reason': reason,
                    'is_removal': symbol not in target_symbols
                }
                print(f"   → MARKET SELL")
            else:
                operations['sell_convert'][symbol] = {
                    'from_asset': symbol,
                    'to_asset': quote_currency,
                    'amount': current_quantity,
                    'value': sell_value,
                    'type': 'convert',
                    'reason': reason,
                    'is_dust': sell_value < self.min_trade_threshold,
                    'is_removal': symbol not in target_symbols
                }
                print(f"   → CONVERT (reason: {reason})")

        # Calculate available balance after sells
        available_after_sell = quote_balance + (total_sell_value * (1 - FEE_RESERVE))

        print(f"\n💰 Баланс після продажу: ${available_after_sell:.2f}")
        print()

        # PHASE 2: BUY all tokens in target allocation
        print("📥 PHASE 2: КУПІВЛЯ")
        print("-" * 80)

        buy_operations_temp = []

        for symbol, target_data in target_allocation.items():
            current_value = current_balances.get(symbol, {}).get('usdc_value', 0)
            target_value = target_data['target_value']
            difference_value = target_value - current_value

            if difference_value <= 0.5:  # Already have enough
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
                'priority': target_data.get('rank', 999),
                'target_weight': target_data['weight']
            })

            print(f"🔼 {symbol}: target ${target_value:.2f} (weight {target_data['weight']:.2f}%), "
                  f"current ${current_value:.2f}, need ${difference_value:.2f}")

        # Sort by priority (rank)
        buy_operations_temp.sort(key=lambda x: x['priority'])

        print(f"\n💵 Доступно для купівлі: ${available_after_sell:.2f}")
        print()

        # PHASE 3: Allocate buys with available funds
        remaining_balance = available_after_sell - MIN_USDC_RESERVE

        for op in buy_operations_temp:
            symbol = op['symbol']
            needed = op['needed_usdc']

            if needed > remaining_balance:
                if remaining_balance < 1.0:
                    print(f"⚠️ Пропуск {symbol}: недостатньо коштів")
                    continue

                # Scale down to available funds
                scale_factor = remaining_balance / needed
                op['needed_usdc'] = remaining_balance
                op['difference_value'] = op['difference_value'] * scale_factor
                op['quantity'] = op['quantity'] * scale_factor

            pair = f"{symbol}{quote_currency}"
            can_place, reason, details = self.can_place_market_order(
                pair, op['quantity'], op['difference_value']
            )

            # Decision: market order or convert
            if op['difference_value'] >= self.min_trade_threshold and can_place:
                operations['buy_orders'][symbol] = {
                    'quantity': op['quantity'],
                    'value_usdc': op['difference_value'],
                    'price': op['price'],
                    'quote_currency': quote_currency,
                    'reason': reason,
                    'target_weight': op['target_weight']
                }
                print(f"🟢 MARKET BUY {symbol}: {op['quantity']:,.8f} (${op['difference_value']:,.2f})")
            else:
                operations['buy_convert'][symbol] = {
                    'from_asset': quote_currency,
                    'to_asset': symbol,
                    'amount': op['difference_value'],
                    'type': 'convert',
                    'reason': reason,
                    'target_weight': op['target_weight']
                }
                print(f"🔵 CONVERT {quote_currency}→{symbol}: ${op['difference_value']:,.2f}")

            remaining_balance -= op['needed_usdc']

        print("-" * 80)
        print(f"\n📊 Summary:")
        print(f"   Tokens to remove: {len(tokens_to_remove)}")
        print(f"   Sell operations: {len(operations['sell_orders']) + len(operations['sell_convert'])}")
        print(f"   Buy operations: {len(operations['buy_orders']) + len(operations['buy_convert'])}")
        print(f"   Remaining balance: ${remaining_balance:.2f}")

        return operations

    def execute_portfolio_rebalance(self, dry_run=False, index_base='cmc20', index_type='top2'):
        """
        Execute portfolio rebalancing based on selected index

        Args:
            dry_run: Test mode (no real trades)
            index_base: 'cmc20' or 'cmc100'
            index_type: 'top2', 'top5', ..., 'top100'
        """
        trade_logger.info("=" * 80)
        trade_logger.info(f"[START] REBALANCE - Base: {index_base}, Type: {index_type}, Dry run: {dry_run}")
        trade_logger.info("=" * 80)

        print(f"\n🚀 REBALANCING ({index_base.upper()} - {index_type.upper()})")
        print(f"⚠️ Mode: {'DRY RUN' if dry_run else '🔴 LIVE'}")
        print("=" * 80)

        # Get current state
        current_balances, total_portfolio_value = self.get_all_binance_balances()

        if total_portfolio_value <= 0:
            return {"error": "Portfolio empty"}

        # Get target allocation based on selected index
        target_allocation = self.get_allocation_from_cmc(index_base, index_type)

        if not target_allocation:
            return {"error": "Failed to fetch CMC data"}

        # Calculate target values for each asset
        for symbol, data in target_allocation.items():
            data['target_value'] = total_portfolio_value * (data['weight'] / 100)

        # Display rebalancing plan
        print("\n⚖️ REBALANCING PLAN")
        print("=" * 120)
        print(
            f"{'Asset':^8} | {'Current $':>14} | {'Current %':>11} | {'Target $':>14} | {'Target %':>11} | {'Difference $':>14} | {'Action':^15}")
        print("-" * 120)

        operations = {'sell': [], 'buy': [], 'convert': []}

        for symbol, target_data in target_allocation.items():
            current_value = current_balances.get(symbol, {}).get('usdc_value', 0)
            current_percent = (current_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
            target_value = target_data['target_value']
            target_percent = target_data['weight']
            difference = target_value - current_value

            action = "✓ OK" if abs(difference) < 1 else ("🟢 BUY" if difference > 0 else "🔴 SELL")

            print(f"{symbol:^8} | ${current_value:>12,.2f} | {current_percent:>10.2f}% | "
                  f"${target_value:>12,.2f} | {target_percent:>10.2f}% | "
                  f"${difference:>+12,.2f} | {action:^15}")

            # Store operations
            if abs(difference) >= 1:
                if difference < 0:
                    operations['sell'].append({
                        'symbol': symbol,
                        'amount': abs(difference),
                        'current_qty': current_balances.get(symbol, {}).get('total', 0)
                    })
                else:
                    operations['buy'].append({
                        'symbol': symbol,
                        'amount': difference
                    })

        print("=" * 120)

        if dry_run:
            return {
                "status": "dry_run",
                "operations": operations,
                "index_base": index_base,
                "index_type": index_type
            }

        # Execute rebalancing
        print("\n📤 EXECUTING REBALANCING")
        print("=" * 80)

        # Determine quote currency
        quote_currency = 'USDC'
        for stable in ['USDC', 'USDT', 'BUSD', 'FDUSD']:
            if current_balances.get(stable, {}).get('total', 0) > 0.1:
                quote_currency = stable
                break

        results = {'sells': [], 'buys': []}

        # PHASE 1: SELLS
        if operations['sell']:
            print("\n🔴 PHASE 1: SELLING")
            for op in operations['sell']:
                symbol = op['symbol']
                sell_value = op['amount']
                quantity = op['current_qty']

                if quantity == 0:
                    continue

                # Try to sell via market order or convert
                pair = f"{symbol}{quote_currency}"

                success = self.execute_market_order(
                    symbol=symbol,
                    side='SELL',
                    quantity=quantity,
                    quote_currency=quote_currency,
                    dry_run=False
                )

                if not success:
                    # Try convert instead
                    success = self.execute_convert(
                        from_asset=symbol,
                        to_asset=quote_currency,
                        amount=quantity,
                        dry_run=False
                    )

                results['sells'].append({'symbol': symbol, 'success': success})

                if success:
                    time.sleep(1)

        # Update balances after sells
        time.sleep(2)
        current_balances, _ = self.get_all_binance_balances()
        available_balance = current_balances.get(quote_currency, {}).get('total', 0)

        print(f"\n💰 Available after sells: ${available_balance:.2f} {quote_currency}")

        # PHASE 2: BUYS
        if operations['buy']:
            print("\n🟢 PHASE 2: BUYING")
            for op in operations['buy']:
                symbol = op['symbol']
                buy_value = op['amount']

                if buy_value > available_balance:
                    print(f"⚠️ Skipping {symbol}: insufficient funds")
                    continue

                price = self.get_binance_price(symbol)
                if price == 0:
                    continue

                quantity = buy_value / price

                # Try to buy via market order or convert
                success = self.execute_market_order(
                    symbol=symbol,
                    side='BUY',
                    quantity=quantity,
                    quote_currency=quote_currency,
                    dry_run=False
                )

                if not success:
                    # Try convert instead
                    success = self.execute_convert(
                        from_asset=quote_currency,
                        to_asset=symbol,
                        amount=buy_value,
                        dry_run=False
                    )

                results['buys'].append({'symbol': symbol, 'success': success})

                if success:
                    available_balance -= buy_value * 1.01  # Account for fees
                    time.sleep(1)

        print("\n✅ REBALANCING COMPLETED")
        print("=" * 80)

        return {
            "status": "completed",
            "results": results,
            "index_base": index_base,
            "index_type": index_type,
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



