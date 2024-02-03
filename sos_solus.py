import undetected_chromedriver as webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from PIL import Image
from random import seed
from random import randint
import numpy as np
import time
import base64
import io
import os
import glob
import requests

######## Paramètres à changer #########
Adresse = "my@email.com"
Password = "password"
login=True

contesttimehours=4 #Durée de l'épreuve en heures
#######################################

baseadd="https://www.doc-solus.fr/prepa/sci/adc/bin/view.corrige.html?q="
savefile='contests2.txt'
data_width=20
pixeldim=50
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
sleeptimesec=2.5

wkdir="/Users/marcfusch/Documents/git/Doc-solus"
os.walk(wkdir)

seed(1)
chrome_options=webdriver.ChromeOptions()
chrome_options.add_argument("enable-automation")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--dns-prefetch-disable")
chrome_options.add_argument("--disable-gpu")
driver = webdriver.Chrome(use_subprocess=True,options=chrome_options, enable_cdp_events=True, headless=False)

def connection():   
    driver.get("https://www.doc-solus.fr/bin/users/connexion.html")
    driver.find_element(By.ID, "focus").send_keys(Adresse)
    driver.find_element(By.NAME,"passwd").send_keys(Password)
    driver.find_element(By.NAME,"save").click()
    print("Connecté")
    
def checkconnection():
    if  login==True:
        try:
            con=driver.find_elements(By.XPATH,'/html/body/div/ul/li[5]/a')
            el=con[0].get_attribute("href").split('/')[-1]
            if el == "connexion.html":
                print("Compte déconnecté: connexion")
                connection()
                return(False)
            elif el == "mon-compte.html":
                return(True)
            else:
                print("Erreur de connexion")
                return(False)
        except:
            driver.refresh()
            time.sleep(sleeptimesec)
            checkconnection()
            pass

def checktime():
    lctime=(int(time.strftime("%H",time.localtime())))
    if lctime >=7 and lctime <=22:
        pass
    else:
        print("Programm is running outside working hours. Quitting...")
        exit()

def getsubject(name):
    if not os.path.isfile(wkdir+'/output/pdf/'+name+'_enonce.pdf'):
        print("Grabbing subject: "+name)       
        result=driver.find_elements(By.XPATH,'html/body/div[2]/section/section/a')[0].get_attribute("href")
        fileName = wkdir+'/output/pdf/'+name+'_enonce.pdf'
        r = requests.get(result, stream=True,headers=headers)
        with open(fileName, 'wb') as f:
            for chunk in r.iter_content():
                f.write(chunk)         
    else:
        print("Subject for "+name+" already exists")

def page(link,contest):
    #Renvoie la liste des liens des différentes pages du corrigé du sujet donné en input + télécharge le sujet
    driver.get(link)
    getsubject(contest)
    lp = []
    resultat = driver.find_elements(By.XPATH,"/html/body/div[2]/section[1]/span/a")
    for element in resultat:
        try :
            lp.append(element.get_attribute("href"))
        except:
            pass
    return(lp)
    


def generation(url):
    #Takes doc-solus search url and saves all contests urls present in the page under 'contests.txt'
    driver.get(url)
    urls = driver.find_elements(By.XPATH,"/html/body/div[2]/ul/li/a")
    urlss=[]
    for element in urls:
        try :
            urlss.append(element.get_attribute("href").split('=')[1])
        except:
            pass
    
    with open(wkdir+"/"+savefile, 'w') as fp:
        for item in urlss:
            fp.write("%s\n" % item)
        fp.close()
    print(str(len(urlss))+' urls have been saved')

def sortKeyFunc(s):
    return int(os.path.basename(s)[:-4])

def generatepdf(name):
    if not os.path.isfile(wkdir+'/output/pdf/'+name+'_corr.pdf'):
        print("Generating pdf...")
        images = [ Image.open(files) for files in sorted(glob.glob(wkdir+'/output/'+name+'/*.png'),key=sortKeyFunc)]
        pdf_path = wkdir+'/output/pdf/'+name+'_corr.pdf'
    
        images[0].save(
            pdf_path, "PDF" ,resolution=100.0, save_all=True, append_images=images[1:]
        )
    else:
        print("Pdf for "+name+" already exists")


def capture_base64(contest,question,direc):
    full = driver.find_elements(By.XPATH,"/html/body/div[2]/center/div/div/table/tbody/tr/td/img")
    bruh=[]
    for element in full:
        try :
            bruh.append(element.get_attribute("src"))
        except:
            pass
    try:
        for i in range(0,len(bruh)//data_width):
            for j in range(0,data_width):
                ex=bruh[i*data_width+j]
                llist=ex.split(',')
                base64_decoded = base64.b64decode(llist[1])
                image = Image.open(io.BytesIO(base64_decoded))
                image=image.convert('L')
                if j==0:
                    image_np = np.array(image)
                else:
                    image_np=np.append(image_np,np.array(image),axis=1)
            if i==0:   
                ligne=image_np
            else:
                ligne=np.append(ligne,image_np,axis=0)
    except:
        return(False)
    try:        
        imm=Image.fromarray(ligne)
        imm.save(direc+"/"+str(question)+".png")
        print(str(question)+" saved")
        return(True)
    except:
        print("Error during image saving: Retrying")
        driver.refresh()
        return(False)


def scanner(contest):
    checktime()
    checkconnection()

    link=baseadd+contest
    lp = page(link,contest)

    newdir=wkdir+"/output/"+contest
    if not os.path.exists(newdir):
        try:
            os.mkdir(newdir)
        except:
            pass
    
    waittime=int((contesttimehours*3600)/len(lp))
    print("Questions: "+str(len(lp)))
    print("Median waiting time between scraping is: "+str(waittime)+'s')
    errors=0
    for question in range(len(lp)):
        checktime()
        if errors>=3:
            return(True)
        if os.path.isfile(newdir+"/"+str(question)+".png"):
            print(str(question)+" exists: Skipping")
        else: 
            lien=lp[question]
            driver.get(lien)
            if  not checkconnection():
                time.sleep(sleeptimesec)
                driver.get(lien)

            result=False
            attempts=0
            while (not result) and (attempts<3):
                time.sleep(sleeptimesec)
                result=capture_base64(contest,question,newdir)
                time.sleep(sleeptimesec)
                attempts+=1
            if attempts<3:
                errors=0
            if attempts>=3:
                print("Failed to scrap current page: skipping...")
                errors+=1
            time.sleep(waittime+randint(-waittime//2, +waittime//2))

def main():
    driver.get('https://www.doc-solus.fr')
    cfile= open(wkdir+"/"+savefile, 'r')
    ll=cfile.readlines()
    print(str(len(ll))+' contests were loaded')
    for contest in ll:
        contest=contest.replace(' ','').replace('\n','')
        print("Scrapping: "+contest) 
        out=scanner(contest)
        if out==True:
            print("Protection detected, aborting.")
            return(False)
        generatepdf(contest)
        time.sleep(sleeptimesec)



#generatepdf('MP_PHYSIQUE_MINES_2_2018')

#generation('https://www.doc-solus.fr/main.html?words=&filiere=PSI&matiere=Mati%E8re&concours=Mines&annee=Ann%E9e')

main()