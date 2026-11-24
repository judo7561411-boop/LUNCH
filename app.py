import streamlit as st
import pandas as pd
import requests
import json
import time
import re
import hashlib
from datetime import date, timedelta

st.set_page_config(page_title="中餐友善點餐系統", page_icon="🍱", layout="wide")

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbw0UEIp80umbupbDQkMQAa5-3Z4HQp01r9VH_Zr-0nYnPzXv6jgY_gKYFyScn7e2Lrj/exec"
SHEET_ID = "1mHnXoG-Duq45EvwZTRVuq86rsK8T5DA9NkLnOi30wuM"
ORDERS_GID = "1002"

SVG_100 = """<svg width="180" height="90" viewBox="0 0 180 90" xmlns="http://www.w3.org/2000/svg" style="border-radius:6px; box-shadow:2px 3px 6px rgba(0,0,0,0.3); margin:4px;"><rect width="180" height="90" rx="6" fill="#C53030"/><rect x="4" y="4" width="172" height="82" rx="4" fill="none" stroke="#FED7D7" stroke-width="1.5" stroke-dasharray="4,2"/><circle cx="45" cy="45" r="22" fill="#9B2C2C"/><circle cx="45" cy="45" r="18" fill="none" stroke="#FEB2B2" stroke-width="1"/><text x="45" y="52" font-family="sans-serif" font-size="20" font-weight="bold" fill="#FED7D7" text-anchor="middle">100</text><text x="135" y="55" font-family="sans-serif" font-size="44" font-weight="900" fill="#FFFFFF" text-anchor="middle">100</text><text x="90" y="22" font-family="sans-serif" font-size="12" font-weight="bold" fill="#FED7D7" text-anchor="middle">中華民國中央銀行</text><text x="135" y="75" font-family="sans-serif" font-size="14" font-weight="bold" fill="#FEEBC8" text-anchor="middle">壹佰圓</text></svg>"""
SVG_50 = """<svg width="84" height="84" viewBox="0 0 84 84" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.35)); margin:4px;"><circle cx="42" cy="42" r="40" fill="#D69E2E" stroke="#744210" stroke-width="2"/><circle cx="42" cy="42" r="34" fill="#ECC94B" stroke="#B7791F" stroke-width="1.5"/><circle cx="42" cy="42" r="26" fill="#D69E2E"/><text x="42" y="49" font-family="sans-serif" font-size="28" font-weight="900" fill="#5A3207" text-anchor="middle">50</text><text x="42" y="61" font-family="sans-serif" font-size="11" font-weight="bold" fill="#744210" text-anchor="middle">圓</text></svg>"""
SVG_10 = """<svg width="76" height="76" viewBox="0 0 76 76" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:4px;"><circle cx="38" cy="38" r="36" fill="#A0AEC0" stroke="#4A5568" stroke-width="2"/><circle cx="38" cy="38" r="30" fill="#E2E8F0" stroke="#718096" stroke-width="1.5"/><text x="38" y="44" font-family="sans-serif" font-size="26" font-weight="900" fill="#2D3748" text-anchor="middle">10</text><text x="38" y="56" font-family="sans-serif" font-size="11" font-weight="bold" fill="#4A5568" text-anchor="middle">圓</text></svg>"""
SVG_5 = """<svg width="66" height="66" viewBox="0 0 66 66" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(2px 3px 4px rgba(0,0,0,0.3)); margin:
