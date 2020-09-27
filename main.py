import requests, bs4, random, time, json, os, discord, asyncio
from os import path
from dotenv import load_dotenv
from discord.ext import commands, tasks


# global url for azlyrics
azlyrics = "https://www.azlyrics.com"

# our list of artists we want to lookup
artists = {
    "A Perfect Circle":"/p/perfect.html",
    "Tool":"/t/tool.html",
    "Deftones":"/d/deftones.html",
    "Puscifer":"/p/puscifer.html",
    "Lady Gaga":"/l/ladygaga.html"
}

artistLibrary = {}
g_randomArtist = ""
g_randomSong = ""
g_randomlyric = ""
debug = True

#-------------------------------------------------------------------
# main method
#-------------------------------------------------------------------

def main():
    startup()
    
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    DESCRIPTION = "A bot to send random lyrics to Thomas"
    CUWA = os.getenv('CUWA')
    CUWA_GENERAL = os.getenv('CUWA_GENERAL')
    bot = commands.Bot(command_prefix='!')

    #getSpecificSongLyric("/lyrics/tool/nema.html")
    #getSpecificSongLyric("/lyrics/tool/prisonsex.html")
    #getSpecificSongLyric("/lyrics/deftones/myownsummershoveit.html")
    #getSpecificSongLyric("/lyrics/tool/schism.html")
    #getSpecificSongLyric("/lyrics/puscifer/asingularity.html")
    #getSpecificSongLyric("/lyrics/perfectcircle/vanishing.html")

    
    @bot.event 
    async def on_ready():
        bg_sendRandomLyric.start()
        print('LyricBot has connected.')
     
    @tasks.loop(hours=6)
    async def bg_sendRandomLyric():
        cuwa_general_channel = bot.get_channel(int(CUWA_GENERAL))
        gotLyric = False
        while not gotLyric:
            if getLyric():
                gotLyric = True
        await cuwa_general_channel.send(g_randomlyric)
    
    @bot.command(name='lastsong', help="Responds with the artist & song name of the last lyric I sent")
    async def last_song(ctx):
        lastSong = "Previous Lyric Info:" + "\n" + "Artist: " + g_randomArtist + "\n" + "Song: " + g_randomSong + "\n" + "The lyric: " + g_randomlyric
        await ctx.send(lastSong)
    
    @bot.command(name='artists', help="Responds with the current list of artists I draw from")
    async def bot_artists(ctx):
        artistString = "Current list of artists:" + "\n"
        numArtists = len(artists)
        for artist in artists.keys():
            artistString += artist
            artistString += "\n"
        await ctx.send(artistString)
    
    @bot.command(name='lyricnow', help="Just for you, I will reply with a random lyric right now <3")
    async def lyric_now(ctx):
        message = "Your instant lyric:" + "\n"
        gotLyric = False
        while not gotLyric:
            if getLyric():
                gotLyric = True
        message += g_randomlyric
        await ctx.send(message)
    
    bot.run(TOKEN)
    
    """
    attempts = 0
    fails = 0
    goodAttempts = 0
    
    while goodAttempts < 10:
        attempts += 1
        print("-------------------------------------")
        print("Attempt #:", attempts)
        print("Successes:",goodAttempts)
        print("Fails:", fails)
       
        if getLyric():
            goodAttempts+=1
        else:
            fails+= 1
            print("Empty song!")
            
        time.sleep(3)
        
    print(goodAttempts,  "successful attempts!")
    """
    if debug:
        print("end of main")

# =================== END main() =============================



#-------------------------------------------------------------------
# startup()
# 
# Start by checking for json file. If not, build our library.
# Then verify the json file has data for artists in our artist list
# If not (say we add an artist to the list but hasnt updated in json yet)
# go get data for it and call buildArtistSongDict
#-------------------------------------------------------------------

def startup():
    newArtist = False
    global artistLibrary
    
    # check to see if json file exists (if not, its probably a first run)
    # if not, build out artist library from scratch
    if not os.path.isfile('songs.json'):
        if debug:
            print("no json file found! querying all artists from artist list")
        for artist in artists:
            artistLibrary[artist] = buildArtistSongDict(artist, artists[artist])
    
        # write to json file
        if debug:
            print("dumping to json file")
        with open('songs.json', 'w', encoding='utf-8') as f:
            json.dump(artistLibrary, f, ensure_ascii=False, indent=4)
            f.close()
        if debug:
            print("done dumping to json file")
            
    # else file DOES exist
    else:
        # open existing json file and parse to dict
        with open('songs.json', encoding = 'utf-8') as f:
            if debug:
                print("loading in json file")
                print("converting to dict")
            artistLibrary = json.load(f)
            f.close()
    
        # verify our list of artists match what we just loaded in
        if debug:
            print("checking for artists in json file")
        for artist in artists:
            if not artist in artistLibrary:
                if debug:
                    print(artist, " not in json file!")
                artistLibrary[artist] = buildArtistSongDict(artist, artists[artist])
                newArtist = True
        
        # if a new artist was added to the dict, save it to the json file
        if newArtist:
            if debug:
                print("dumping to json file")
                
            with open('songs.json', 'w', encoding='utf-8') as f:
                json.dump(artistLibrary, f, ensure_ascii=False, indent=4)
                f.close()
            if debug:
                print("done dumping to json file")
        
        else:
            if debug:
                print("json file matches our current list of artists")
    if debug:
        print("end startup")
        
# =================== END startup() =============================

#-------------------------------------------------------------------
# buildArtistSongDict(String artistName, String artistDir)
#
# Given an artist and its azlyric url, build a dict that contains all the
# artist's songs and return it
# 
#-------------------------------------------------------------------

def buildArtistSongDict(artistName, artistDir):
    thisArtistSongs = {}
    if debug:
        print("starting build for ", artistName)
    # go to artist azlyrics page
    artistUrl = azlyrics + artistDir
    artistPage = requests.get(artistUrl)

    # check to make sure we arrived
    if artistPage.status_code == 200:
        
        # keep this so we can use code 200 to continue print(artistUrl.status_code)

        # souping the artist page
        soup = bs4.BeautifulSoup(artistPage.text, "html.parser")
        
        # selecting the div that contains links to songs
        songsDiv = soup.select("#listAlbum")
        
        # create list of song links
        allSongs = songsDiv[0].find_all("a")

        # loop through allSongs and add each song to the dict
        for songLink in allSongs:
            title = songLink.string
            link = songLink.get("href")
            thisArtistSongs[title] = link
            
           # print(title)
           # print(link)
           # print("\n")
        return thisArtistSongs
    
    else:
        print("HTML CODE: " + artistPage.status_code)
        print("Trying to access url: " + artistUrl)
# =================== END buildArtistSongDict() =============================    
    

#-------------------------------------------------------------------
# getLyric()
# function to randomly select an artist from a predefined set of artists,
# load a dictionary of the songs for that artist, randomly choose a song,
# grab the lyrics from that song, and randomly select a line from that song to send to Tom.
#-------------------------------------------------------------------

def getLyric():

    global g_randomlyric, g_randomArtist, g_randomSong
    # ------------------ requesting a song and get lyrics ----------------
    # select a random artist from our defined list of artists. just in case our json file contains an artist
    # we dont want to use right now.
    randomArtist = random.choice(list(artists))
    g_randomArtist = randomArtist
    
    randomSong = random.choice(list(artistLibrary[randomArtist].keys()))
    g_randomSong = randomSong

    # create full url
    songhref = (artistLibrary[randomArtist][randomSong])[2:]
    songUrl = (azlyrics + songhref)
    
    if debug:
        print("-----------------------------------------------")
        print("Artist:", randomArtist)
        print("Song:", randomSong)
        print(songUrl)


    lyricsPage = requests.get(songUrl)
    lyricsPage = bs4.BeautifulSoup(lyricsPage.text, "html.parser")
    lyrics = lyricsPage.select(".col-xs-12.col-lg-8.text-center")
    lyrics = lyrics[0].select("div:nth-of-type(5)")

    lyrics = lyrics[0].get_text()
    
    # split the string and filter it
    cleanLyrics = lyrics.split("\n",-1)
    cleanLyrics = list(filter(None, cleanLyrics))
    
    i = 0
    for line in cleanLyrics:
        cleanLyrics[i] = line.rstrip()
        if not cleanLyrics[i]:
            #print("deleting:" + repr(cleanLyrics[i]))
            del cleanLyrics[i]
        i += 1
    
    if debug:
        print("length: ", len(cleanLyrics))
    # make sure we dont have an empty string
    if cleanLyrics:
        
        """
        if debug:
            i = 0
            for line in cleanLyrics:
                print(i, line)
                i += 1
        """
        randomLine = random.choice(list(cleanLyrics))
        g_randomlyric = randomLine
        
        print(randomLine)
        return True
         
    else:
        if debug:
            print("we found an empty song")
        return False
    

# =================== END getLyric() =============================  



#-------------------------------------------------------------------
# getSpecificSongLyric(String song)
# randomly select a line from a given song's azlyric url
# 
# 
#-------------------------------------------------------------------
def getSpecificSongLyric(givenUrl):

    # create full url
    songUrl = (azlyrics + givenUrl)
    
    if debug:
        print(songUrl)


    lyricsPage = requests.get(songUrl)
    lyricsPage = bs4.BeautifulSoup(lyricsPage.text, "html.parser")
    lyrics = lyricsPage.select(".col-xs-12.col-lg-8.text-center")
    lyrics = lyrics[0].select("div:nth-of-type(5)")


    lyrics = lyrics[0].get_text()

    
    # split the string and filter it
    cleanLyrics = lyrics.split("\n",-1)
    cleanLyrics = list(filter(None, cleanLyrics))
    
    i = 0
    for line in cleanLyrics:
        cleanLyrics[i] = line.rstrip()
        if not cleanLyrics[i]:
            #print("deleting:" + repr(cleanLyrics[i]))
            del cleanLyrics[i]
        i += 1
    
    if debug:
        print("length: ", len(cleanLyrics))
    # make sure we dont have an empty string
    if cleanLyrics:      
        """
        if debug:
            i = 0
            for line in cleanLyrics:
                #print(i, repr(line))
                print(i, line)
                i += 1
        """
        
        randomLine = random.choice(list(cleanLyrics))
        
        print(randomLine)
        return True
         
    else:
        if debug:
            print("we found an empty song")
        return False
    

# =================== END getSpecificSongLyric() ============================= 


#-------------------------------------------------------------------
#-------------------------------------------------------------------
#-------------------------------------------------------------------    


main()


    
