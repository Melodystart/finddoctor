from function import getUrl
from function import untilNow
import time


def test_getUrl():
    assert getUrl("javascript:CreateWindow('https://www.vghtpe.gov.tw/Docpersnr.action?tno=DOC3697E');") == 'https://www.vghtpe.gov.tw/Docpersnr.action?tno=DOC3697E'
    assert getUrl("javascript:CreateWindow('https://www.vghtpe.gov.tw/Docpersnr.action?tno=DOC3707G');") == 'https://www.vghtpe.gov.tw/Docpersnr.action?tno=DOC3707G'


def test_untilNow():
    fivedayts = time.time() + 5*24*60*60
    ninemonthts = time.time() + 9.3*31*24*60*60
    twoyearts = time.time() + 2*366*24*60*60
    untilNow(fivedayts) == "5天前"
    untilNow(ninemonthts) == "9個月前"
    untilNow(twoyearts) == "2年前"
