import datetime as dt


def year(request):
    now_str = dt.date.today().strftime('%Y')
    return {'year': int(now_str)}
