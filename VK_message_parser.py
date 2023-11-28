import lxml.etree as etree
import os, glob, requests, shutil, urllib.parse, time
from threading import Thread, Lock
from progress.bar import IncrementalBar
import re

g_files_parsed = 0 
lock = Lock()

months = { "янв": "1",
           "фев": "2",
           "мар": "3",
           "апр": "4",
           "мая": "5",
           "июн": "6",
           "июл": "7",
           "авг": "8",
           "сен": "9",
           "окт": "10",
           "ноя": "11",
           "дек": "12"}

def parse_time_str(time_stamp):
    scarp, date = time_stamp[0].split(',')
    for rus_month, eng_month in months.items():
        if rus_month in date:
            break
    date_numbers = list(map(int, re.findall('\d+', date)))
    time_stamp_str_name = str(date_numbers[1]) + "_" + eng_month + "_" + str(date_numbers[0]) + "_"
    for i in range(2,len(date_numbers),1):
        time_stamp_str_name = time_stamp_str_name + "_" + str(date_numbers[i])
    return time_stamp_str_name

def download_images(files_in_folder, files_numbers):
    global g_files_parsed
    for messages in files_in_folder:
        with open(messages, "r", encoding="windows-1251") as f:
            html_file = f.read()
        tree = etree.HTML(html_file)
        for block in tree.xpath("//div[@class='item']"):
            try:
                if block.xpath(".//div[@class='attachment__description']")[0].text == "Фотография":
                    base_time_stamp_str_name = parse_time_str(block.xpath(".//div[@class='message__header']/text()"))
                    images_block = block.xpath(".//a[@class='attachment__link']")
                    image_number_in_block = 0
                    for images in images_block:
                        time_stamp_str_name = base_time_stamp_str_name
                        if len(images_block) > 1:
                            image_number_in_block += 1
                            time_stamp_str_name = time_stamp_str_name + "_" + str(image_number_in_block)
                        time_stamp_str_name = os.getcwd() + "/folder_images/" + time_stamp_str_name + ".jpg"
                        r = requests.get(images.text, stream=True)
                        r.raw.decode_content = True
                        with open(time_stamp_str_name,'wb') as img_f:
                            shutil.copyfileobj(r.raw, img_f)
            except IndexError:
                continue
        
        lock.acquire()
        g_files_parsed += 1
        lock.release()
        
folder_name = os.getcwd() + "/folder/"
files_in_folder = sorted(glob.glob(os.path.join(folder_name, '*.html')), reverse=True)


step = (int)(len(files_in_folder) / 16)
residue = (int)(len(files_in_folder) % 16)
x = []
for i in range(16):
    if i == 0:
        x.append(Thread(target=download_images, args=(files_in_folder[0 : step + residue],step + residue)))
    else:
        x.append(Thread(target=download_images, args=(files_in_folder[step * i + residue : step * i + step + residue],step + residue)))
    x[i].start()

bar = IncrementalBar('Parsed files', max = len(files_in_folder))

while g_files_parsed != len(files_in_folder):
    time.sleep(1)
    bar.index =g_files_parsed
    bar.update()

for i in range(16):
    x[i].join()