import discord
import json 

from datetime import datetime
from discord.ext import commands
from discord.utils import escape_markdown
from utils.aiohttp_wrap import aio_get_json


class Stonks(commands.Cog):
    URL = "https://finnhub.io/api/v1/quote"
    PROFILE_URL = "https://finnhub.io/api/v1/stock/profile2"
    TTL = 60 * 15
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.aio_session
        self.redis_client = bot.redis_client
        # self.headers = {'X-Finnhub-Token': bot.api_keys["stonks"]}
        with open('data/apikeys.json') as f:
            self.api_key = json.load(f)["stonks"]
        self.headers = {'X-Finnhub-Token': self.api_key}
    
    @commands.command(name="stonk", aliases=["stonks", "stock", "stocks"])
    async def stonks(self, ctx: commands.Context, *, symbol: str):
        if len(symbol) > 5:
            return await ctx.error("Stock error", description=f"Invalid ticker symbol: `{escape_markdown(symbol)}`")

        symbol = symbol.upper()
        params = {"symbol": symbol}

        redis_key = f"stonks:{symbol}"
        if await self.redis_client.exists(redis_key):
            resp = json.loads(await self.redis_client.get(redis_key))
        else:
            resp = await aio_get_json(self.session, self.URL, headers=self.headers, params=params)

            if resp is None:
                return await ctx.error("API Error", description="There was an issue with the stocks API, try again later")
            
            if resp['t'] == 0:
                return await ctx.error("Stock error", description=f"Couldn't find any stock information for `{symbol}`")
            
            company_profile = await aio_get_json(self.session, self.PROFILE_URL, params=params, headers=self.headers)
            resp["company_profile"] = company_profile
            await self.redis_client.set(redis_key, json.dumps(resp), ex=self.TTL)
        
        em = discord.Embed(color=discord.Color.blurple())
        em.set_author(
            name=f"{resp['company_profile']['name']} ({symbol})" if resp["company_profile"] else symbol, 
            icon_url=resp["company_profile"]["logo"] if "logo" in resp["company_profile"] else "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/240/twitter/259/chart-increasing_1f4c8.png", 
            url=resp["company_profile"]["weburl"] if "weburl" in resp["company_profile"] else ""
        )
        em.add_field(name="Current Price", value=f"${resp['c']:,.2f}")
        em.add_field(name="Previous Close", value=f"${resp['pc']:,.2f}")
        em.add_field(name="% Change Today", value=f"{(resp['c'] - resp['pc'])/resp['pc']:.2%}")

        em.set_footer()
        em.timestamp = datetime.fromtimestamp(resp['t'])

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Stonks(bot))
