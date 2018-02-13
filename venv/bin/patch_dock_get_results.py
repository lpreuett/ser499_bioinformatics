import scrapy
import sys

class BioSpider(scrapy.Spider):

    def __init__(self, *a, **kw):
        # get start URL
        url = kw.pop('link', [])

        if url:
            #print('link: {}'.format(url))
            self.start_urls = [url]
        else:
            # exit if no start url
            print('Usage: -a link')
            sys.exit(1)

        self.logger.info(self.start_urls)
        super(BioSpider, self).__init__(*a, **kw)



    name = "bio_spider"
    #start_urls = [ self.link ]

    def parse(self, response):


        score = int(response.xpath('//table[4]/tr[2]/td[2]/text()').extract()[0])
        print('Patch Dock Score: {}'.format(score))
