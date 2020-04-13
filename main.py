from gtts import gTTS
from playsound import playsound
from pydub import AudioSegment
from pydub.playback import play
from bs4 import BeautifulSoup as bs
import requests, json, os, sys, concurrent.futures, threading, time
from multiprocessing import Process, Lock
from conf import Conf
from os import listdir
from os.path import isfile, join


hnUrl = 'https://news.ycombinator.com/'
smryUrl = 'https://api.smmry.com/&SM_API_KEY={}&SM_URL='.format(Conf().key)
audioDir = 'audio/'
fileName = 'out'
fileExt = '.mp3'
fileOut = audioDir+fileName
articles = {}
threadCount = 2
files = {}
sys.setrecursionlimit(25000)

data = requests.get(hnUrl).text
soup = bs(data, features='html.parser')
stories = soup.find_all('a', {'class': 'storylink'})


def returnArticle(title, counter):
    artUrl = title['href']
    articleReq = requests.get(smryUrl + artUrl)
    articleJson = json.loads(articleReq.text)

    if articleReq.status_code == 200:
        try:
            articleContent = articleJson['sm_api_content']
            content = "Article {}. Title: {}. Summary. {}".format(counter, title.text, articleContent)
            print(content)
        except KeyError:
            print("[!] SMMRY Error: {}".format(articleJson['sm_api_error']))
            content = "Article {} could not be retrieved".format(counter)
    else:
        print("[!} Request Error: Status {}".format(articleReq.status_code))
        content = "Article {} could not be retrieved".format(counter)
    articles[counter] = content
    print("\t[+] Article successfully retrieved")


def createAudioFile(content, counter):
    print("\t[+] Sending article {} to Google Translate API".format(counter))
    tts = gTTS(content)
    file = fileOut + str(counter) + fileExt

    files[counter] = file
    print("\t[+] Writing to {}".format(file))
    tts.save(file)

def playAudioFile(lock,):
    lock.acquire()

    def checkAudioFile():
        print("[*] Attempting to play")

        while not any(isfile(join(audioDir, i)) for i in listdir(audioDir)):
            print("[-] Files not yet available")
            time.sleep(5)

        if any(isfile(join(audioDir, i)) for i in listdir(audioDir)):
            print("[*] Files available")
            time.sleep(3)

            try:
                myKey = list(files.copy().keys())[0]
                path = files.copy()[myKey]

                try:
                    print("[+] Playing {}".format(path))
                    audio = AudioSegment.from_mp3(path)
                    play(audio)
                except OSError:
                    print("[-] File not yet available")
                    checkAudioFile()

                try:
                    files.pop(myKey)
                except KeyError as ke:
                    print(ke, files)

                os.remove(path)
                lock.release()

            except IndexError:
                print("[-] Key not yet available")
                checkAudioFile()

    print("[-] End of function")
    checkAudioFile()


def chunks(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))

counter = 0

if __name__ == "__main__":

    if any(isfile(join(audioDir, i)) for i in listdir(audioDir)):
        print("[-] Removing old files")
        for i in listdir(audioDir):
            os.remove(audioDir+i)

    lock = threading.Lock()

    for story in stories:

        counter += 1
        artCount = counter

        getArticle = threading.Thread(target=returnArticle, args=(story, artCount))
        getArticle.start()
        getArticle.join()

        myArt = list(articles.copy().keys())[0]
        art = articles.copy()[myArt]
        getFile = threading.Thread(target=createAudioFile, args=(art, artCount))
        getFile.start()
        articles.pop(myArt)

        getAudio = threading.Thread(target=playAudioFile, args=(lock,))
        getAudio.start()
