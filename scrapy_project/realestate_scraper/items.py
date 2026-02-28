import scrapy


class RealEstateItem(scrapy.Item):
    """Item definition for real estate agency data"""
    Name = scrapy.Field()
    Email = scrapy.Field()
    Phone = scrapy.Field()
    Location = scrapy.Field()
    Last_Contacted = scrapy.Field()
    Status = scrapy.Field()
    Social_Media = scrapy.Field()
    Joined = scrapy.Field()
    Address = scrapy.Field()
    Rating = scrapy.Field()
    Reviews = scrapy.Field()
    Category = scrapy.Field()
    Website = scrapy.Field()
