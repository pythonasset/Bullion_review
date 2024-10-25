import os
import threading
import tkinter as tk
from tkinter import messagebox

import pandas as pd
import plotly.graph_objects as go
import requests
import yfinance as yf


class MonitorAgent:
    def __init__(self):
        self.data = {
            'Gold': [],
            'Silver': [],
            'Platinum': [],
            'Palladium': []
        }
        self.forex_rate = self.get_forex_rate()

    def get_forex_rate(self):
        try:
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
            response.raise_for_status()
            data = response.json()
            return data['rates']['AUD']
        except Exception as e:
            print(f"Error fetching forex rate: {e}")
            return 1.4  # Fallback to an approximate value

    def collect_yearly_price_data(self):
        metals = {
            'Gold': 'GC=F',
            'Silver': 'SI=F',
            'Platinum': 'PL=F',
            'Palladium': 'PA=F'
        }

        for metal, ticker in metals.items():
            try:
                ticker_data = yf.Ticker(ticker)
                yearly_data = ticker_data.history(period='1y')
                if not yearly_data.empty:
                    yearly_data_aud = yearly_data['Close'] * self.forex_rate
                    self.data[metal] = yearly_data_aud.tolist()
                else:
                    print(f"No data available for {metal}.")
            except Exception as e:
                print(f"Error fetching data for {metal}: {e}")

    def collect_short_term_price_data(self):
        metals = {
            'Gold': 'GC=F',
            'Silver': 'SI=F',
            'Platinum': 'PL=F',
            'Palladium': 'PA=F'
        }

        short_term_data = {}
        for metal, ticker in metals.items():
            try:
                ticker_data = yf.Ticker(ticker)
                short_term_data[metal] = ticker_data.history(period='5d')['Close']
            except Exception as e:
                print(f"Error fetching short term data for {metal}: {e}")
        return pd.DataFrame(short_term_data)

    def get_data(self):
        return pd.DataFrame(self.data,
                            index=pd.date_range(end=pd.Timestamp.now(), periods=len(self.data['Gold']), freq='D'))


class TrendAnalysisAgent:
    def __init__(self):
        pass

    def analyze_trends(self, data):
        trends = {}
        for metal in data.columns:
            # Calculate a simple moving average trend direction
            if len(data[metal]) > 1:
                trends[metal] = 'Up' if data[metal].iloc[-1] > data[metal].mean() else 'Down'
            else:
                trends[metal] = 'No Data'
        return trends

    def analyze_short_term_trends(self, data):
        trends = {}
        for metal in data.columns:
            if len(data[metal]) > 1:
                trends[metal] = 'Up' if data[metal].iloc[-1] > data[metal].iloc[0] else 'Down'
            else:
                trends[metal] = 'No Data'
        return trends


class RecommendationAgent:
    def __init__(self):
        pass

    def recommend(self, long_term_trends, short_term_trends):
        recommendations = {}
        for metal in long_term_trends.keys():
            if long_term_trends[metal] == 'Up' and short_term_trends[metal] == 'Up':
                recommendations[metal] = 'Sell'
            elif long_term_trends[metal] == 'Down' and short_term_trends[metal] == 'Down':
                recommendations[metal] = 'Buy'
            else:
                recommendations[metal] = 'Hold'
        return recommendations


def plot_interactive_charts(data):
    for metal in data.columns:
        latest_price = data[metal].iloc[-1]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data[metal], mode='lines+markers', name=metal))
        fig.update_layout(
            title=f'{metal} Price Trend (Latest: {latest_price:.2f} AUD per Ounce)',
            xaxis_title='Time Period',
            yaxis_title='Price (in AUD)',
            xaxis=dict(
                tickformat='%Y-%m-%d %H:%M',
                rangeslider_visible=True,
                tickangle=-45,
                tickfont=dict(size=10)
            ),
            template='plotly_dark'
        )
        fig.show()


def display_alert(trends, recommendations):
    alert_message = ""
    for metal in trends:
        alert_message += f"{metal}: Trend - {trends[metal]}, Recommendation - {recommendations[metal]}\n"
    messagebox.showinfo("Price Alert", alert_message)


def main_app():
    # Create instances of agents
    monitor_agent = MonitorAgent()
    trend_agent = TrendAnalysisAgent()
    recommendation_agent = RecommendationAgent()

    # Collect yearly data
    monitor_agent.collect_yearly_price_data()

    # Get collected data
    price_data = monitor_agent.get_data()
    print("\nPrice Data:")
    print(price_data)

    # Analyze trends
    long_term_trends = trend_agent.analyze_trends(price_data)
    print("\nLong Term Trend Analysis:")
    for metal, trend in long_term_trends.items():
        print(f"{metal}: {trend}")

    # Collect short term data
    short_term_data = monitor_agent.collect_short_term_price_data()
    short_term_trends = trend_agent.analyze_short_term_trends(short_term_data)
    print("\nShort Term Trend Analysis:")
    for metal, trend in short_term_trends.items():
        print(f"{metal}: {trend}")

    # Get recommendations
    recommendations = recommendation_agent.recommend(long_term_trends, short_term_trends)
    print("\nRecommendations:")
    for metal, recommendation in recommendations.items():
        print(f"{metal}: {recommendation}")

    # Plot interactive charts for each bullion
    plot_interactive_charts(price_data)

    # Display alert with trends and recommendations
    display_alert(long_term_trends, recommendations)


def run_app():
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window

    app_thread = threading.Thread(target=main_app)
    app_thread.start()
    root.mainloop()


if __name__ == "__main__":
    # Schedule the script to run on Windows startup
    startup_file = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup',
                                'bullion_ai_agents.bat')
    with open(startup_file, 'w') as f:
        f.write(f'python "{os.path.realpath(__file__)}"')

    run_app()
