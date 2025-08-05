import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from config_SimPy import *

class Logger:
    def __init__(self, env):
        # Logger는 env만 저장하고 manager에 의존하지 않음
        self.env = env
        self.event_logs = []  # 이벤트 로그 저장소

    def log_event(self, event_type, message):
        """Log an event with a timestamp"""
        if EVENT_LOGGING:
            current_time = self.env.now
            days = int(current_time // (24 * 60))
            hours = int((current_time % (24 * 60)) // 60)
            minutes = int(current_time % 60)
            timestamp = f"{days:02d}:{hours:02d}:{minutes:02d}"
            total_minutes = int(current_time)
            print(f"[{timestamp}] [{total_minutes}] | {event_type}: {message}")

            # 나중에 분석을 위해 로그 저장
            self.event_logs.append((current_time, event_type, message))