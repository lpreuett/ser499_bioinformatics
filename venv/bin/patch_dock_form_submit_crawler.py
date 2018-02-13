import scrapy


class BioSpider(scrapy.Spider):
    name = "bio_spider"
    start_urls = [ 'http://bioinfo3d.cs.tau.ac.il/PatchDock/index.html' ]

    def parse(self, response):

        if hasattr(self, 'receptor'):
            print('receptor: {}'.format(self.receptor))
        else:
            print('Usage: -a receptor -a ligand')
            return

        if hasattr(self, 'ligand'):
            print('ligand: {}'.format(self.ligand))
        else:
            print('Usage: -a receptor -a ligand')
            return

        return scrapy.FormRequest.from_response(
            response,
            formdata={ 'receptor' : self.receptor, 'ligand' : self.ligand, 'email' : 'ser499webscraper@gmail.com' },
            callback=self.after_patchdock_submit
        )

    def after_patchdock_submit(self, arg1):
        return