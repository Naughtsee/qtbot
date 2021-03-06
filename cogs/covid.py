import discord

from discord.ext import commands
from urllib.parse import quote_plus
from dateutil.parser import isoparse
from utils import aiohttp_wrap as aw


class Covid(commands.Cog):
    COLOR = discord.Color.red()
    URL = "https://api.covidtracking.com/v1"

    @commands.command(name="covid", aliases=["c19", "rona", "corona"])
    async def _covid(self, ctx, *, state: str = None):
        """Get current US covid statistics, optionally passing a 2-letter state code"""
        if state is not None:
            if len(state) != 2:
                await ctx.message.add_reaction("❌")
                return await ctx.send("Use 2-letter state identifiers", delete_after=10)

        if state is None:
            location = "the US"
            data = (
                await aw.aio_get_json(
                    ctx.bot.aio_session, f"{self.URL}/us/current.json"
                )
            )[0]
        else:
            location = state.upper()
            data = await aw.aio_get_json(
                ctx.bot.aio_session, f"{self.URL}/states/{state.lower()}/current.json"
            )

        if "error" in data:
            if data["error"]:
                await ctx.message.add_reaction("❌")
                return await ctx.send(
                    "Something went wrong with the covid API :(", delete_after=10
                )

        em = discord.Embed()
        em.color = self.COLOR
        em.set_author(
            name=f"Current Covid statistics in {location}",
            icon_url="https://i.imgur.com/9ka5fCC.png",
            url=f"https://google.com/search?q={quote_plus('covid cases in ' + location)}",
        )
        em.timestamp = isoparse(
            data["lastModified"] if "lastModified" in data else data["dateModified"]
        )

        em.add_field(name="📈 New cases today", value=f"{data['positiveIncrease']:,}")
        em.add_field(name="☠️ Deaths today", value=f"{data['deathIncrease']:,}")
        em.add_field(name="⚰️ Total Deaths", value=f"{data['death']:,}", inline=False)

        if "dataQualityGrade" in data:
            em.add_field(name="📝 Data quality", value=data["dataQualityGrade"] or "n/a")

        em.set_footer(text="Last updated")

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Covid(bot))
