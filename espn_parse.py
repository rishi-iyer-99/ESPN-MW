import requests
from bs4 import BeautifulSoup
import math
import re

#Some Constants/Initial Variables
CORRECT = "#icon__form__check"

this_link = "https://www.espn.com/nfl/picks/_/seasontype/2/week/1"

#Get the soup for page 
def get_soup(link):
	page = requests.get(link)
	soup = BeautifulSoup(page.text, 'html.parser')
	return soup

#Get the table that contains relevant information
def get_table(soup):
	table = soup.find("div", {"class": "Table__Scroller"})
	return table


#Get the names of all the experts
def get_experts(table):
	header = table.find("tr", {"class": "Table__TR Table__even"})
	header = header.findAll('th')
	names = []
	for th in header:
		names.append(th.find_all("div")[-1].getText())
	return names


#Get all the matchups
def get_matchups(soup):
	table = soup.find("table", {"class": "Table Table--align-center Table--fixed Table--fixed-left"})
	body = table.find("tbody", {"class": "Table__TBODY"})
	items = body.findAll("a", {"class": "AnchorLink"})
	matchups=[]
	for i in items:
		matchups.append(i.getText())
	return matchups

#Get all the games
def get_games(table):
	games = table.find("tbody", {"class": "Table__TBODY"})
	games = games.findAll("tr")
	return games[:-1]

#Given a game, get each expert's predictions
def get_predictions(game,names):
	predictions = game.findAll("img")
	predictions = [p['src'] for p in predictions]
	for i in range(len(predictions)):
		s = predictions[i]
		result = re.search('teamlogos/nfl/500/(.*).png', s)
		predictions[i]=result.group(1).upper()
	expert_predictions = {}
	for i in range(len(names)):
		expert_predictions[names[i]]=predictions[i]
	return expert_predictions

#Choose prediction that has higher sum of weights
def draw(expert_predictions, weights):
	weighted_predictions = {}
	for expert in expert_predictions:
		pred = expert_predictions.get(expert)
		weight = weights.get(expert)
		if pred not in weighted_predictions:
			weighted_predictions[pred] = weight
		else:
			weighted_predictions[pred] += weight
	return max(weighted_predictions, key=weighted_predictions.get)

#Determine whether each expert was right or wrong for the game's prediction
def get_losses(game):
	predictions = game.findAll("div", {"class": "PassFailWrapper__Badge"})
	losses = []
	# print(predictions)
	for p in predictions:
		predicted_winner = p.find("img")
		is_correct = p.find("use")['xlink:href']
		if is_correct==CORRECT:
			losses.append(0)
		else:
			losses.append(1)
	return losses

#Determine if algorithm prediction was correct
def is_correct(losses):
	if len(losses)==0:
		return "WINNER NOT KNOWN"
	return sum(losses)==0

#Update weights based on losses
def update_weights(losses,names,weights,epsilon):
	if len(losses)==0:
		return
	daily_loss = {}
	for i in range(len(names)):
		daily_loss[names[i]]=losses[i]
	for expert in weights:
		weights[expert] = weights[expert] * (1-epsilon)**(daily_loss[expert])


def process(link):
	soup = get_soup(link)
	table = get_table(soup)
	names = get_experts(table)
	matchups = get_matchups(soup)
	games = get_games(table)

	#Initialize dictionary of expert weights
	weights = {}
	for name in names:
		weights[name]=1

	#set epsilon value
	T = 256 #Number of Games in NFL regular season
	n = len(names) #nNumber of experts
	epsilon = math.sqrt(math.log(n)/T)

	for i in range(len(matchups)):
		print("GAME: ",matchups[i])
		game = games[i]
		predictions = get_predictions(game,names)
		print("OUR PREDICTION: ", draw(predictions, weights))
		losses = get_losses(game)
		print ("CORRECT?: ", is_correct(losses))
		update_weights(losses,names,weights,epsilon)
		print("UPDATED WEIGHTS: ", weights)

process(this_link)





