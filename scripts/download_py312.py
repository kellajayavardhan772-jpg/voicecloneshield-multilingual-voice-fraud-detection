import urllib.request
url = 'https://www.python.org/ftp/python/3.12.6/python-3.12.6-amd64.exe'
out = r'c:\Desktop\IBM intern project\python-3.12.6-amd64.exe'
print('Downloading', url)
urllib.request.urlretrieve(url, out)
print('Saved to', out)