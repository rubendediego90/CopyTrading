from enum import Enum
from pydantic import BaseModel
import pandas as pd
from datetime import datetime

# Definición de los distintos tipos de eventos

class SignalType(str, Enum):
    """
    Represents the type of a trading signal.
    """
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    """
    Represents the type of an order.
    """
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    
class BaseEvent(BaseModel):
    class Config:
        arbitrary_types_allowed = True

class OrderEvent(BaseEvent):
    """
    Represents an order event.

    Attributes:
        event_type (EventType): The type of the event.
        symbol (str): The symbol of the order.
        signal (SignalType): The signal type of the order.
        target_order (OrderType): The target order type.
        target_price (float): The target price of the order.
        sl (float): The stop loss level of the order.
        tp (float): The take profit level of the order.
        volume (float): The volume of the order.
    """
    symbol: str
    signal: SignalType
    target_order: OrderType
    comment: str
    sl: float
    tp: float
    volume: float
    magic: int

