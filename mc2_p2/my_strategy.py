# __author__ = 'Mowgli'

import os
import math
import pandas as pd
import matplotlib.pyplot as plot
import csv


def symbol_to_path(symbol, base_dir=os.path.join("..", "data")):
    """Return CSV file path given ticker symbol."""
    return os.path.join(base_dir, "{}.csv".format(str(symbol)))


def plot_data(df, title="Stock prices", xlabel="Date", ylabel="Price"):
    """Plot stock prices with a custom title and meaningful axis labels."""
    ax = df.plot(title=title, fontsize=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plot.show()


def get_data(symbols, dates, addSPY=True):
    """Read stock data (adjusted close) for given symbols from CSV files."""
    df = pd.DataFrame(index=dates)
    if addSPY and 'SPY' not in symbols:  # add SPY for reference, if absent
        symbols = ['SPY'] + symbols

    for symbol in symbols:
        df_temp = pd.read_csv(symbol_to_path(symbol), index_col='Date',
                parse_dates=True, usecols=['Date', 'Adj Close'], na_values=['nan'])
        df_temp = df_temp.rename(columns={'Adj Close': symbol})
        df = df.join(df_temp)
        if symbol == 'SPY':  # drop dates SPY did not trade
            df = df.dropna(subset=["SPY"])

    return df


def plot_normalized_data(df, title="Normalized prices", xlabel="Date", ylabel="Normalized price"):
    """Normalize given stock prices and plot for comparison.

    Parameters
    ----------
        df: DataFrame containing stock prices to plot (non-normalized)
        title: plot title
        xlabel: X-axis label
        ylabel: Y-axis label
    """
    # TODO: Your code here
    df = df / df.ix[0, :]
    plot_data(df, title, xlabel, ylabel)


def get_portfolio_value(prices, allocs, start_val=1):
    """Compute daily portfolio value given stock prices, allocations and starting value.

    Parameters
    ----------
        prices: daily prices for each stock in portfolio
        allocs: initial allocations, as fractions that sum to 1
        start_val: total starting value invested in portfolio (default: 1)

    Returns
    -------
        port_val: daily portfolio value
    """

    normed = prices / prices.ix[0, :]
    alloced = normed * allocs
    pos_vals = alloced * start_val
    port_val = pos_vals.sum(axis=1)

    return port_val


def get_portfolio_stats(port_val, daily_rf=0, samples_per_year=252):
    """Calculate statistics on given portfolio values.

    Parameters
    ----------
        port_val: daily portfolio value
        daily_rf: daily risk-free rate of return (default: 0%)
        samples_per_year: frequency of sampling (default: 252 trading days)

    Returns
    -------
        cum_ret: cumulative return
        avg_daily_ret: average of daily returns
        std_daily_ret: standard deviation of daily returns
        sharpe_ratio: annualized Sharpe ratio
    """
    # TODO: Your code here

    daily_ret = (port_val / port_val.shift(1)) - 1
    daily_ret.ix[0] = 0
    daily_ret = daily_ret[1:]
    avg_daily_ret = daily_ret.mean()
    std_daily_ret = daily_ret.std()
    cum_ret = (port_val[-1] / port_val[0]) - 1
    sharpe_ratio = math.sqrt(samples_per_year) * ((avg_daily_ret - daily_rf) / std_daily_ret)

    return cum_ret, avg_daily_ret, std_daily_ret, sharpe_ratio


# THIS FUNCTION WOULD NOT PASS THE LEVERAGE TEST CASES

def compute_portvals(start_date, end_date, orders_file, start_val):
    """Compute daily portfolio value given a sequence of orders in a CSV file.

    Parameters
    ----------
        start_date: first date to track
        end_date: last date to track
        orders_file: CSV file to read orders from
        start_val: total starting cash available

    Returns
    -------
        portvals: portfolio value for each trading day from start_date to end_date (inclusive)
    """

    # read csv file
    reader = csv.reader(open(orders_file, 'rU'), delimiter=',')

    # eliminate duplicate symbols
    symbols = []
    symbol_dict = {}
    i = 0
    for row in reader:
        if i != 0:
            if (symbol_dict.get(row[1], -1)) == -1:
                symbol_dict[row[1]] = row[1]
                symbols.append(row[1])

        i += 1

    # create dataframes
    dates = pd.date_range(start_date, end_date)
    prices_all = get_data(symbols, dates)  # automatically adds SPY
    prices_df = prices_all[symbols]  # only portfolio symbols
    prices_df['Cash'] = 1.0

    count_df = pd.DataFrame(index=prices_df.index, columns=symbols)
    count_df = count_df.fillna(0)

    cash_df = pd.DataFrame(index=prices_df.index, columns=['Cash_Value'])
    cash_df = cash_df.fillna(start_val)

    # populate dataframes
    reader = csv.reader(open(orders_file, 'rU'), delimiter=',')
    i = 0
    for row in reader:
        if i != 0:
            if row[0] in count_df.index:
                if row[2] == 'SELL':
                    count_df.ix[row[0], row[1]] += -float(row[3])
                    cash_df.ix[row[0]] += -float(row[3]) * prices_df.ix[row[0], row[1]]
                if row[2] == 'BUY':
                    count_df.ix[row[0], row[1]] += float(row[3])
                    cash_df.ix[row[0]] += float(row[3]) * prices_df.ix[row[0], row[1]]

        i += 1

    value = start_val
    for date_index, row in count_df.iterrows():
        for i in range(0, len(row), 1):
            if date_index in count_df.index and date_index in prices_df.index:
                value += -(prices_df.ix[date_index, symbols[i]] * count_df.ix[date_index, symbols[i]])
        cash_df.ix[date_index] = value

    count_df['Cash'] = cash_df

    # print prices_df
    # print
    # print count_df
    # print
    # find cumulative sum
    for i in range(0, len(count_df.columns)-1, 1):
        count_df[symbols[i]] = count_df[symbols[i]].cumsum()
    # print count_df
    # print
    # dot product of matrices
    count_df = prices_df * count_df
    count_df['Sum'] = count_df.sum(axis=1)
    # print count_df

    # rearrange columns
    columns = count_df.columns.tolist()
    columns = columns[-1:] + columns[:-1]
    count_df = count_df[columns]

    return count_df


def test_run():
    """Driver function."""
    # Define input parameters
    start_date = '2007-12-31'
    end_date = '2009-12-31'
    dates = pd.date_range(start_date, end_date)

    # Simulate a $SPX-only reference portfolio to get stats
    data = get_data(['IBM'], pd.date_range(start_date, end_date))
    data = data[['IBM']]  # remove SPY by choosing IBM

    prices_SPY = get_data(['SPY'], pd.date_range(start_date, end_date))
    prices_SPY = prices_SPY[['SPY']]

    data['SMA'] = pd.rolling_mean(data['IBM'], window=20)
    data['Momentum'] = 0
    pd.set_option('display.max_rows', len(data))

    row_count = 0
    date_array = []

    for index, row in data.iterrows():
        date_array.append(index)
        if row_count >= 10:
            data.loc[index, 'Momentum'] = data.loc[index, 'IBM']/data.loc[date_array[row_count-10], 'IBM'] - 1
        row_count += 1

    # data['avg_momentum'] = pd.rolling_mean(data['Momentum'], window=20)
    # print data
    plot.figure()
    ax = plot.gca()
    data['IBM'].plot(label='IBM', ax=ax, color='b')
    data['SMA'].plot(label='SMA', ax=ax, color='y')
    ax.legend(loc='best')

    count = 0
    line_count = 0
    short_flag = False
    long_flag = False

    data_array = [('Date', 'Symbol', 'Order', 'Shares')]

    for index, row in data.iterrows():
        current = row.values[0]
        avg = row.values[1]
        momentum = row.values[2]
        if count == 0:
            last = row.values[0]

        if last > avg >= current:
            # print "short entry"
            # print momentum
            line_count += 1
            plot.axvline(index, color='red')
            short_flag = True
            data_array.append((str(index.strftime('%Y-%m-%d')), 'IBM', 'SELL', '100'))
        elif current >= avg > last:
            # print "long entry"
            # print momentum
            line_count += 1
            plot.axvline(index, color='green')
            long_flag = True
            data_array.append((str(index.strftime('%Y-%m-%d')), 'IBM', 'BUY', '100'))


        count += 1
        last = current

    with open('orders.csv', 'w') as fp:
        data_writer = csv.writer(fp, delimiter=',')
        data_writer.writerows(data_array)

    plot.show()

    orders_file = os.path.join("", "orders.csv")
    start_val = 10000
    # Process orders
    portvals = compute_portvals(start_date, end_date, orders_file, start_val)
    if isinstance(portvals, pd.DataFrame):
        portvals = portvals[portvals.columns[0]]  # if a DataFrame is returned select the first column to get a Series

    # Get portfolio stats
    cum_ret, avg_daily_ret, std_daily_ret, sharpe_ratio = get_portfolio_stats(portvals)

    # Simulate a $SPX-only reference portfolio to get stats
    prices_SPY = get_data(['SPY'], pd.date_range(start_date, end_date))
    prices_SPY = prices_SPY[['SPY']]
    portvals_SPY = get_portfolio_value(prices_SPY, [1.0])
    cum_ret_SPY, avg_daily_ret_SPY, std_daily_ret_SPY, sharpe_ratio_SPY = get_portfolio_stats(portvals_SPY)

    # Compare portfolio against $SPX
    print "Data Range: {} to {}".format(start_date, end_date)
    print
    print "Sharpe Ratio of Fund: {}".format(sharpe_ratio)
    print "Sharpe Ratio of SPY: {}".format(sharpe_ratio_SPY)
    print
    print "Cumulative Return of Fund: {}".format(cum_ret)
    print "Cumulative Return of SPY: {}".format(cum_ret_SPY)
    print
    print "Standard Deviation of Fund: {}".format(std_daily_ret)
    print "Standard Deviation of SPY: {}".format(std_daily_ret_SPY)
    print
    print "Average Daily Return of Fund: {}".format(avg_daily_ret)
    print "Average Daily Return of SPY: {}".format(avg_daily_ret_SPY)
    print
    print "Final Portfolio Value: {}".format(portvals[-1])

    # Plot computed daily portfolio value
    df_temp = pd.concat([portvals, prices_SPY['SPY']], keys=['Portfolio', 'SPY'], axis=1)
    plot_normalized_data(df_temp, title="Daily portfolio value and SPY")

if __name__ == "__main__":
    test_run()