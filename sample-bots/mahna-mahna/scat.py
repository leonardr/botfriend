from olipy.markov import MarkovGenerator
import re
import random

class ScatGenerator(MarkovGenerator):

    # My transcription of Mahna Mahna's scat.
    MAHNA_MAHNA_SCAT = """Mahna mahna mahna ma nanamanah miti mitiah mah ma 
Mahna muh muh nuh nah nuh nuh nuh
Ina nina nina nah nih bah nuh nah
Eehna ehh
Mahna ma nuh nuh nah nih muh
Mahna ma nih nuh nah nih muh
Mahna muh mih nah nah
Mihna mihna nunuh a nah nih nuh
Eeh neh neh mah neeh nah neh
Mmm mmm
Mihna nihna nih ah a muh i muh
Ehn eehn ah a mehn en ah
Nih ah neh ah 
Nap map banna bah
Nap map bunna buh
ahnaBah nuh nah nuh
Burih
Mah mahna mahna mahna mah mahn mah
Mahn mahn mahn mahna mahn mah
Imi mahn mahn wah wahm manah
Bibi bee dee deet
Mahna man mah mahn
Mah nih nah ma
Mahna mah nih nah nih ha niha nam
Yahma man manyahnimah man
Bibahna bahna yip bip behne ya mahna
Mahnehma mahnema
Mah yip mah 
Yihmahna meh meh mah yibi dibi yih yih
Yip yeep yi yeep biti biti beep
Mihni 
Baba bee bah bip beeby
Beeh bip bibi
Deet dah deety ditty dah
Bip bih bahda bah
Yeep yah nah nih nah
Yeep bah bap bih bah""".split("\n")
    
    VOWELS = re.compile("([aeiouy]+)")

    def tokenize(self, s):
        # Split on vowels
        return self.VOWELS.split(s.lower())

    def __init__(self, lines=None, order=1, max=40):
        lines = lines or self.MAHNA_MAHNA_SCAT
        super(ScatGenerator, self).__init__(order, max)
        for i in lines:
            self.add(i.strip())

    def _scat(self):
        product = ""
        for i in self.generate():
            if ' ' in i and random.randint(0,2) == 1:
                i = i.replace(" ", "-")
            product += i
        if product.endswith("-"):
            product = product[:-1]
        return product

    def scat(self, length):
        scat = self._scat()
        while len(scat) < length:
            scat = self._scat()
        while len(scat) > length and ' ' in scat:
            scat = scat[:scat.rindex(' ')]
        return scat
    
if __name__ == '__main__':
    ge = ScatGenerator()
    print ge.scat(50)
