import time
from dateutil.relativedelta import relativedelta
from datetime import datetime, timezone

def getUrl(words):
    first = words.index("'")+1
    end = words.index("'", first)
    return words[slice(first, end)]


def untilNow(ts):
    # 設定utc時區
    past_utc = datetime.utcfromtimestamp(ts).replace(tzinfo=timezone.utc)
    now_utc = datetime.now(tz=timezone.utc)

    # 設定utc+8時區
    # utf8 = timezone(timedelta(hours=8))
    # past_utc8 = past_utc.astimezone(utf8)
    # now_utc8 = now_utc.astimezone(utf8)

    until_now = relativedelta(now_utc, past_utc)

    years = until_now.years
    months = until_now.months
    days = until_now.days
    hours = until_now.hours
    minutes = until_now.minutes

    if years == 0:
        if months == 0:
            if days == 0:
                if hours == 0:
                    return (str(minutes) + "分鐘前")
                else:
                    return (str(hours) + "小時前")
            else:
                return (str(days) + "天前")
        else:
            return (str(months) + "個月前")
    else:
        return (str(years) + "年前")


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
