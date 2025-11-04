"""Test Yahoo Finance BTC data quality."""
import yfinance as yf

ticker = yf.Ticker('BTC-USD')
df = ticker.history(period='1d', interval='15m')

print('Yahoo Finance BTC-USD Test:')
print(f'Rows fetched: {len(df)}')
print(f'\nLast 3 candles:')
print(df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(3))
print(f'\nVolume stats:')
print(f'Min: {df["Volume"].min():,.0f}')
print(f'Max: {df["Volume"].max():,.0f}')
print(f'Avg: {df["Volume"].mean():,.0f}')
print(f'\nVolume > 0: {(df["Volume"] > 0).sum()} / {len(df)} candles')
