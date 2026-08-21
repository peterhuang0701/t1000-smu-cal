# 版本號單一來源: 發版時改這裡, GUI標題/log/CI artifact都會跟著變
# 慣例: 主版本.次版本.修訂 (功能大改.加功能.修bug)
__version__ = '1.2.0'

GITHUB_REPO = 'peterhuang0701/t1000-smu-cal'
RELEASE_PAGE = 'https://github.com/{}/releases/latest'.format(GITHUB_REPO)
_LATEST_API = 'https://api.github.com/repos/{}/releases/latest'.format(GITHUB_REPO)


def check_latest(timeout=5):
    # 到GitHub查最新Release版本, 回傳 (最新版號, 是否比目前新)
    # 連不上網路/GitHub時丟例外, 由呼叫端決定怎麼顯示
    import json
    import urllib.request
    req = urllib.request.Request(_LATEST_API,
                                 headers={'User-Agent': 'SMU-Cal-Tool'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        tag = json.load(r).get('tag_name', '').lstrip('v')

    def key(s):
        return [int(x) for x in s.split('.')]
    try:
        newer = key(tag) > key(__version__)
    except ValueError:
        newer = (tag != __version__)
    return tag, newer
