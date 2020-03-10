from crawlers.a1machinery import crawl_a1machinery as _crawl_a1machinery
from crawlers.ceqinc import crawl_ceqinc as _crawl_ceqinc
from crawlers.forklift_websites import find_new_forklift_websites as _find_new_forklift_websites
from crawlers.gregorypoolelift import crawl_gregorypoolelift as _crawl_gregorypoolelift
from crawlers.manuvic import crawl_manuvic as _crawl_manuvic
from crawlers.smforklift import crawl_smforklift as _crawl_smforklift
from crawlers.southeastforklifts import crawl_southeastforklifts as _crawl_southeastforklifts
from crawlers.valleesaintsauveur import crawl_valleesaintsauveur as _crawl_valleesaintsauveur
from crawlers.chariotelevateurhardy import crawl_chariotelevateurhardy as _crawl_chariotelevateurhardy
from crawlers.ldlqc import crawl_ldlqc as _crawl_ldlqc
from crawlers.achatusag import crawl_achatusag as _crawl_achatusag
from crawlers.equipementsmonteregie import crawl_equipementsmonteregie as _crawl_equipementsmonteregie
from crawlers.multichariots import crawl_multichariots as _crawl_multichariots
from crawlers.machinerieplante import crawl_machinerieplante as _crawl_machinerieplante
from crawlers.equipementse3 import crawl_equipementse3 as _crawl_equipementse3
from crawlers.nfelifts import crawl_nfelifts as _crawl_nfelifts
from crawlers.michiganwholesaleequipment import crawl_michiganwholesaleequipment as _crawl_michiganwholesaleequipment
from crawlers.tmhnc import crawl_tmhnc as _crawl_tmhnc
from crawlers.komatsuforklift import crawl_komatsuforklift as _crawl_komatsuforklift
from crawlers.canadacrown import crawl_canadacrown as _crawl_canadacrown
from crawlers.paindustrial import crawl_paindustrial as _crawl_paindustrial
from crawlers.greysonequipment import crawl_greysonequipment as _crawl_greysonequipment
from crawlers.liftnorthamerica import crawl_liftnorthamerica as _crawl_liftnorthamerica

# If you want to add new crawler - please add the corresponding file to crawlers directory and use already defined
# functions in utils package. Place here only functions that call function from crawlers package.


def find_new_forklift_websites(request):
    return _find_new_forklift_websites(request)


def crawl_manuvic(request):
    return _crawl_manuvic(request)


def crawl_valleesaintsauveur(request):
    return _crawl_valleesaintsauveur(request)


def crawl_smforklift(request):
    return _crawl_smforklift(request)


def crawl_a1machinery(request):
    return _crawl_a1machinery(request)


def crawl_ceqinc(request):
    return _crawl_ceqinc(request)


def crawl_gregorypoolelift(request):
    return _crawl_gregorypoolelift(request)


def crawl_southeastforklifts(request):
    return _crawl_southeastforklifts(request)


def crawl_chariotelevateurhardy(request):
    return _crawl_chariotelevateurhardy(request)


def crawl_ldlqc(request):
    return _crawl_ldlqc(request)


def crawl_achatusag(request):
    return _crawl_achatusag(request)


def crawl_equipementsmonteregie(request):
    return _crawl_equipementsmonteregie(request)


def crawl_multichariots(request):
    return _crawl_multichariots(request)


def crawl_machinerieplante(request):
    return _crawl_machinerieplante(request)


def crawl_equipementse3(request):
    return _crawl_equipementse3(request)


def crawl_nfelifts(request):
    return _crawl_nfelifts(request)


def crawl_michiganwholesaleequipment(request):
    return _crawl_michiganwholesaleequipment(request)


def crawl_tmhnc(request):
    return _crawl_tmhnc(request)


def crawl_komatsuforklift(request):
    return _crawl_komatsuforklift(request)


def crawl_canadacrown(request):
    return _crawl_canadacrown(request)


def crawl_paindustrial(request):
    return _crawl_paindustrial(request)


def crawl_greysonequipment(request):
    return _crawl_greysonequipment(request)


def crawl_liftnorthamerica(request):
    return _crawl_liftnorthamerica(request)