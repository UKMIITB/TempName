import re
import os
from datetime import datetime

import stylecloud
from stop_words import get_stop_words
from wordcloud import STOPWORDS

fileName = 'MachauWingiesChatData.txt'


def getDateTimeNameMessage(line):
    '''This function takes a line as input parameter
    and returns a tuple in the following order
    (date, time, name, message)
    date as datetime type
    time in hh:mm am/pm format as string type'''

    date = re.search("[0-9]{2}/[0-9]{2}/[0-9]{4}", line)
    time = re.search("[0-9]+:[0-9]{2}\s[ap]m", line)
    name = re.search("\s-\s(.*?):", line)
    message = re.search("\s-\s.*:\s(.+)", line)

    if date is not None and time is not None and name is not None and message is not None:   # This line contains a new data
        date = datetime.strptime(date.group(0), '%d/%m/%Y')
        time = time.group(0)
        name = name.group(1)
        message = message.group(1)

    # Someone left a group message
    elif date is not None and time is not None and (name is None or message is None):
        date = None
        time = None
        name = None
        message = None

    else:                           # This only contains message, continuation of previous message
        date = None
        time = None
        name = None
        message = line

    return (date, time, name, message)


def getSimplifiedChatData(filename):
    '''This function takes filename as input parameter
    and returns a list of all chat data
    with each value being a tuple in the order
    (date, time, name, message)

    This function merges large messages which come in new line in chat data text file'''

    chatDataTxt = open(filename, 'r', encoding="utf8")  # opened as read only
    chatDataList = []                 # to store and return the simplified data

    for eachLine in chatDataTxt:
        dateTimeNameMsgTuple = getDateTimeNameMessage(eachLine)

        if dateTimeNameMsgTuple[0] is not None:          # New data found
            chatDataList.append(dateTimeNameMsgTuple)

        # Message is None i.e someone left a group. Skip this data
        elif dateTimeNameMsgTuple[-1] is None:
            pass

        else:                                            # message continues from previous data
            newMsgForPreviousData = chatDataList[-1][-1] + \
                dateTimeNameMsgTuple[-1]
            dateForPreviousData = chatDataList[-1][0]
            timeForPreviousData = chatDataList[-1][1]
            nameForPreviousData = chatDataList[-1][2]

            chatDataList[-1] = (dateForPreviousData, timeForPreviousData,
                                nameForPreviousData, newMsgForPreviousData)

    return chatDataList


def getAllParticipantsName(filename, includeCompleteName=False):
    '''This function returns a list of names of all the group participants
    Requirement is that they should have posted atleast a single message
    Name returned is the name saved in persons whose data has been shared

    Pass the filename to this function
    Optionally it accepts includeCompleteName parameter which if true returns complete name
    else just first name is included'''

    allChatDataSimplified = getSimplifiedChatData(
        filename)  # Getting simplified data
    allChatParticipants = set()  # varible of set type to store all participants name

    for eachChatData in allChatDataSimplified:
        name = eachChatData[2]

        if includeCompleteName:  # full name is required
            pass
        else:  # only first name is required
            name = name.split()[0]

        allChatParticipants.add(name)

    return list(allChatParticipants)


def GetBasicStats(chatDataList):
    ''' Input: list output from getSimplifiedChatData function
        Output: tuples of general stats (number of messages, Chat duration, total number of characters in
                message(including spaces), total number of words, total number of media content) 
    '''

    nMsg = len(chatDataList)
    ChatDuration = (chatDataList[-1][0] - chatDataList[0][0]).days + 1

    nCharacters = 0  # including spaces
    nWords = 0
    nMedia = 0

    for item in chatDataList:
        nCharacters = nCharacters + len(item[3])
        nWords = nWords + len(item[3].split())
        if item[3] == "<Media omitted>":
            nMedia = nMedia + 1

    return (nMsg, ChatDuration, nCharacters, nWords, nMedia)


def GetDetailedStats(chatDataList):
    '''
    Input: list output from getSimplifiedChatData function
    Output: tuple (AvgMsgPerDay, AvgCharPerMsg, AvgCharPerDay, LenLongestMsg, AvgWordsPerMsg, AvgWordsPerDay, AvgMediaPerDay)
    '''

    (nMsg, ChatDuration, nCharacters, nWords, nMedia) = GetBasicStats(chatDataList)

    AvgMsgPerDay = int(nMsg/ChatDuration)
    AvgCharPerMsg = int(nCharacters/nMsg)
    AvgCharPerDay = int(AvgMsgPerDay*AvgCharPerMsg)
    AvgWordsPerMsg = int(nWords/nMsg)
    AvgWordsPerDay = int(AvgWordsPerMsg*AvgMsgPerDay)
    AvgMediaPerDay = int(nMedia/ChatDuration)

    LenLongestMsg = 0
    for item in chatDataList:
        LenLongestMsg = max(LenLongestMsg, len(item[3]))

    return (AvgMsgPerDay, AvgCharPerMsg, AvgCharPerDay, LenLongestMsg, AvgWordsPerMsg, AvgWordsPerDay, AvgMediaPerDay)


def extractDomainName(line):
    '''This function extracts and returns domain name of url 
    from the given sentence passed as parameter
    If no url is present, it returns None'''

    # if url is present, extracting till first '/' after https
    link = re.search("https://(.+?)/", line)

    if link is None:
        return None

    link = link.group(1)

    linkWords = link.split('.')

    if len(linkWords) > 2:  # first word mostly like is www
        return linkWords[1]
    else:
        return linkWords[0]  # first word itself is the domain name


def GetIndividualDataDistribution(chatDataList):
    '''
    Input: list output from getSimplifiedChatData function
    output: Dictionary[First Name as key]: ChatData for that Individual
    '''
    MembersData = {}

    for item in chatDataList:
        firstName = item[2].split()[0]
        if firstName not in MembersData:
            MembersData[firstName] = []

        MembersData[firstName].append(item)

    return MembersData


def getIndividualStats(chatDataList):
    '''
    Input: list output from getSimplifiedChatData function
    Output: Dictionary[First Name as key]: Detailed Stats of chat for that Individual
    '''

    MembersData = GetIndividualDataDistribution(chatDataList)

    IndividualStats = {}

    for keys in MembersData.keys():
        IndividualStats[keys] = GetDetailedStats(MembersData[keys])

    return IndividualStats


def getDayWiseDataDistribution(chatDataList):
    '''
    Input: list output from getSimplifiedChatData function
    Output: Dictionary[Date in datetime as key]: ChatData for that Date
    '''

    DayWiseDistribution = {}

    for item in chatDataList:
        if item[0] not in DayWiseDistribution:
            DayWiseDistribution[item[0]] = []

        DayWiseDistribution[item[0]].append(item)

    return DayWiseDistribution


def getDayWiseStats(chatDataList):
    '''
    Input: list output from getSimplifiedChatData function
    Output: Dictionary[Date in datetime type as key]: Detailed Stats of chat for that Date
    '''
    DayWiseDistribution = getDayWiseDataDistribution(chatDataList)

    DayWiseStats = {}

    for key in DayWiseDistribution.keys():
        DayWiseStats[key] = GetDetailedStats(DayWiseDistribution[key])

    return DayWiseStats


def getDayWisePersonWiseDistribution(chatDataList):
    '''
    Input: list output from getSimplifiedChatData function
    Output: Dictionary[Date in datetime type as key]: Dictionary[First Name as key]: ChatData for that Individual that day
    '''

    DayWiseDistribution = getDayWiseDataDistribution(chatDataList)

    DayMemberDistribution = {}

    for key in DayWiseDistribution.keys():
        DayMemberDistribution[key] = GetIndividualDataDistribution(
            DayWiseDistribution[key])

    return DayMemberDistribution


def getDayWisePersonWiseStats(chatDataList):
    '''
    Input: List output from getSimplifiedChatData function
    Output: Dictionary[Date in datetime type as key]: Dictionary[First Name as key]: DetailedStats for that Individual that day
    '''

    DayWiseDistribution = getDayWiseDataDistribution(chatDataList)

    DayMemberStats = {}

    for key in DayWiseDistribution.keys():
        DayMemberStats[key] = getIndividualStats(DayWiseDistribution[key])

    return DayMemberStats


def getAllLinksStat(allChatDataSimplified):
    '''Input: output from getSimplifiedChatData
    Output: returns a map with domain name as key & count as its value'''

    allLinksStat = {}  # variable to store all links count

    for eachChatData in allChatDataSimplified:
        message = eachChatData[3]

        domainName = extractDomainName(message)

        if domainName is not None:
            if domainName in allLinksStat:
                allLinksStat[domainName] = allLinksStat[domainName] + 1
            else:
                allLinksStat[domainName] = 1

    return allLinksStat


def getMentionNumber(message):
    '''Input: message
    Output: list of number which was mentioned
    If no mentions, then list is empty'''

    mentions = re.findall("@[0-9]{2}([0-9]{10})", message)
    return mentions


def getMentionStat(chatDataList):
    '''Input: output of getSimplifiedChatData function
    Output: dictionary with key -> person's name
    value -> dictionary with number as key, count as value'''

    mentionStat = {}

    for eachChatData in chatDataList:

        name = eachChatData[2].split()[0]
        message = eachChatData[-1]

        if name not in mentionStat:
            mentionStat[name] = {}

        mentions = getMentionNumber(message)

        if len(mentions) != 0:
            for eachMention in mentions:
                if eachMention not in mentionStat[name]:
                    mentionStat[name][eachMention] = 1
                else:
                    mentionStat[name][eachMention] = mentionStat[name][eachMention] + 1

    return mentionStat


def getStopWordList():
    '''This function returns a list of StopWords as list to be used in wordcloud making'''
    stopWords = get_stop_words('english')
    stopWordFile = open('StopWords.txt', 'r')

    while True:
        line = stopWordFile.readline()

        if not line:
            break

        line = line.strip()
        line = re.sub("\n", "", line)
        stopWords.append(line)

    stopWords = list(set(stopWords))
    stopWords.extend(list(set(STOPWORDS)))

    return stopWords


def getWordCloud(chatDataList, filename, stopWordList):
    '''Input: chatDataList and filename for output image, 
    Output: adds a png file by the name filenameWordCloud in source directory'''

    file = open('tempData.txt', 'w')

    for eachChatData in chatDataList:

        message = eachChatData[-1]
        messageList = message.split()
        messageList = [word for word in messageList if len(word) > 3]

        message = " ".join(messageList)+" "
        file.write(message)

    file.close()

    stylecloud.gen_stylecloud(file_path='tempData.txt', icon_name='fas fa-bread-slice',
                              output_name=filename+'WordCloud.png', custom_stopwords=stopWordList, collocations=True,
                              size=(2048, 2048))

    # deleting the temp file
    if os.path.exists("tempData.txt"):
        os.remove("tempData.txt")


def getAllWordCloud(chatDataList):
    '''Input: output of getSimplifiedChatData function
    Output: adds a png file for all members by their first name & group data in the source directory
    fileName format -> nameWordCloud.png, groupWordCloud.png

    This is a time intensive function. May take upto several minutes for each participants'''

    stopWordList = getStopWordList()

    # Generating group data's word cloud
    getWordCloud(chatDataList, 'group', stopWordList)

    individualChatDataList = GetIndividualDataDistribution(chatDataList)

    for individualParticipant in individualChatDataList:  # Word cloud for individual participants
        getWordCloud(
            individualChatDataList[individualParticipant], individualParticipant, stopWordList)
