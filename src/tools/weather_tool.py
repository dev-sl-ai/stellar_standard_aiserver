from typing import Optional, Type, ClassVar, Dict
import aiohttp

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools import BaseTool
from pydantic.v1 import BaseModel

from src.api.websocket_manager import WebSocketManager
from src.agent.session_manager import ChatSessionManager
from src.helpers.enums import ActionType
from src.message_templates.websocket_message_template import WebsocketMessageTemplate


class ShowWeatherToolInput(BaseModel):
    pass


class ShowWeatherTool(BaseTool):
    name: str = "weather_info"
    description: str = "天気についての話しの時に役に立つツール。現在地を取得して天気予報を表示します。"
    args_schema: Type[BaseModel] = ShowWeatherToolInput
    ws_manager: Optional[WebSocketManager] = None
    message_manager: Optional[WebsocketMessageTemplate] = None
    session_manager: Optional[ChatSessionManager] = None
    return_direct: bool = False

    async def get_weather_forecast(self, lat: float, lon: float) -> dict:
        """Get weather forecast using Open-Meteo API"""
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m"
                f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
            )
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Weather fetch error: {e}")
        return None

    def get_weather_website_url(self, location: dict) -> str:
        """Return JMA weather forecast page (prefecture-based if possible)"""
        # Mapping of prefectures to JMA area codes
        jma_codes = {
            '北海道': '016000',
            '青森県': '020000',
            '宮城県': '040000',
            '東京都': '1310100',
            '神奈川県': '140000',
            '千葉県': '120000',
            '埼玉県': '110000',
            '新潟県': '150000',
            '愛知県': '230010',
            '大阪府': '270000',
            '京都府': '260000',
            '兵庫県': '280000',
            '広島県': '340000',
            '福岡県': '400010',
            '沖縄県': '4710100',
        }

        prefecture = location.get('prefecture', '東京都')
        area_code = jma_codes.get(prefecture, '1310100')  # default Tokyo

        return f"https://www.jma.go.jp/bosai/forecast/#area_type=class20s&area_code={area_code}&lang=jp"

    def get_weather_description(self, weather_code: int) -> str:
        """Convert WMO weather code to a Japanese description."""
        wmo_to_japanese = {
            0: "快晴",
            1: "晴れ",
            2: "くもり",
            3: "雨",
            45: "霧",
            48: "霧氷",
            51: "小雨",
            61: "雨",
            63: "強い雨",
            71: "雪",
            80: "にわか雨",
            95: "雷雨",
        }
        return wmo_to_japanese.get(weather_code, "不明")


    def get_location_string(self, location: dict) -> str:
        """Format prefecture and city name properly."""
        city = location.get("city", "")
        prefecture = location.get("prefecture", location.get("region", ""))
        return f"{prefecture} {city}" if prefecture and prefecture != city else city


    def summarize_weather_trend(self, desc: str, precip: Optional[float]) -> str:
        """Generate a short natural-language weather summary."""
        if precip and precip > 0:
            # Example: Rain followed by clouds
            if desc == "くもり":
                return "雨のちくもり"
            return "雨"
        return desc


    def build_weather_message(
        self,
        location_str: str,
        desc: str,
        temp: float,
        wind: float,
        temp_max: Optional[float],
        temp_min: Optional[float],
        summary: str,
        website_url: str,
    ) -> str:
        """Constructs the final formatted weather message."""
        lines = [
            f"{location_str}の天気予報",
            "",
            f"現在の天気: {desc}",
            f"気温: {temp}°C",
        ]
        if temp_max is not None and temp_min is not None:
            lines.append(f"今日の予想: 最高 {temp_max}°C / 最低 {temp_min}°C")

        lines.append(f"風速: {wind} km/h")
        lines.append("")
        lines.append(f"天気の傾向: {summary}")

        return "\n".join(lines)


    def format_weather_message(self, location: dict, weather: dict, website_url: str) -> str:
        """Main entry point: format the weather message neatly."""
        if not weather or "current" not in weather:
            city = location.get("city", "")
            prefecture = location.get("prefecture", location.get("region", ""))
            return f"{prefecture} {city}の天気情報を取得できませんでした。"

        current = weather.get("current", {})
        daily = weather.get("daily", {})

        weather_code = current.get("weather_code")
        desc = self.get_weather_description(weather_code)

        temp = current.get("temperature_2m", "N/A")
        wind = current.get("wind_speed_10m", "N/A")
        temp_max = daily.get("temperature_2m_max", [None])[0]
        temp_min = daily.get("temperature_2m_min", [None])[0]
        precip = daily.get("precipitation_sum", [None])[0]

        summary = self.summarize_weather_trend(desc, precip)
        location_str = self.get_location_string(location)

        return self.build_weather_message(
            location_str, desc, temp, wind, temp_max, temp_min, summary, website_url
        )

    async def show_weather_info(self):
        """Main execution: detect location, get weather, format + send"""
        location = self.ws_manager.get_location_data().to_dict()
        print(f"Retrieved location data in ShowWeatherTool: {location}")
        weather = await self.get_weather_forecast(location["lat"], location['lon'])
        website_url = self.get_weather_website_url(location)
        response_message = self.format_weather_message(location, weather, website_url)

        # Send action to the client
        action_message = self.message_manager.url_action_message(
            website_url,
            ActionType.SHOW_WEATHER.value
        )
        await self.ws_manager.send_to_client(action_message, self.ws_manager.room_id)

        return response_message

    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        import asyncio
        return asyncio.run(self.show_weather_info())

    async def _arun(
        self,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        self.session_manager.context.last_tool_name = self.name
        return await self.show_weather_info()
