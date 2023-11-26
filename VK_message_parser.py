from LxmlSoup import LxmlSoup
from lxml import html
import os, glob, requests, shutil, urllib.parse, time
from threading import Thread, Lock
from natsort import natsorted 
from progress.bar import IncrementalBar
    
g_files_parsed = 0 
lock = Lock()

def download_images(files_in_folder, img_counter):
    global g_files_parsed
    for messages in files_in_folder:
        html_file =  html.tostring(html.parse(messages))
        soup = LxmlSoup(html_file)
        images = soup.find_all('a', class_='attachment__link')
        for i, link in enumerate(images):
            url = link.get("href")
            if (urllib.parse.unquote(url).find('impg') == -1):
                continue
            file_name = "folder_name/img_" + str(img_counter)
            res = requests.get(url, stream=True)
            with open(file_name,'wb') as f:
                shutil.copyfileobj(res.raw, f)
            img_counter+=1
        lock.acquire()
        g_files_parsed+=1
        lock.release()
            
folder_name = "folder_name/"
files_in_folder = natsorted(glob.glob(os.path.join(folder_name, '*.html')),reverse=True)

step = (int)(len(files_in_folder) / 16)
residue = (int)(len(files_in_folder) % 16)
temp = files_in_folder[step*2:step*2+step]
x = []
for i in range(16):
    if i == 0:
        x.append(Thread(target=download_images, args=(files_in_folder[step*i:step*i + step + residue],step * i * 50)))
    else:
        x.append(Thread(target=download_images, args=(files_in_folder[step*i:step*i+step],step*i*50)))
    x[i].start()

bar = IncrementalBar('Countdown', max = len(files_in_folder))

while g_files_parsed != len(files_in_folder):
    time.sleep(1)
    bar.index =g_files_parsed
    bar.update()

for i in range(16):
    x[i].join()