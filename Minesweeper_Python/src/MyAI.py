# ==============================CS-199==================================
# FILE:			MyAI.py
#
# AUTHOR: 		Cole Hajek
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
#				agent in this file. You will write the 'getAction' function,
#				the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
#
#				- DO NOT MAKE CHANGES TO THIS FILE.
# ==============================CS-199==================================
import copy
from AI import AI
from Action import Action
from collections import deque
from queue import Queue
class MyAI(AI):
	
	def __init__(self, rowD, colD, tMines, sX, sY):
		self.rowDimension = rowD
		self.actionCounter = 0
		self.colDimension = colD
		self.flagsLeft = tMines
		self.uncoveredTiles = set()
		self.uncoveredFrontier = set()
		self.coveredFrontier = set()
		self.threshold = 25
		self.curMineConfigurations = 0
		self.curX = sX
		self.curY = sY
		self.prevValue = -1
		self.minesToFlag = Queue()
		self.toUncoverQueue = Queue()
		self.board = [[self.Tile(x, y) for y in range(rowD)] for x in range(colD)]
			
			
	def getNeighbors(self, x, y):
		#returns an array of neighbors for tile with coordinates x,y in order left->right top->bottom
		neighbors = []
		for j in range(-1, 2):
			for i in range(-1, 2):
				if i == 0 and j == 0:
					continue  # Skip the current tile itself
				new_x = x + i
				new_y = y - j  
				#if the tile is on the edge of the board do not try to get neighbors that would be considered out of bounds
				if 0 <= new_x < self.colDimension and 0 <= new_y < self.rowDimension:
					neighbors.append(self.board[new_x][new_y])
		return neighbors
	
	def checkTile(self, x, y):
		self.uncoveredTiles.add(self.board[x][y])
		self.board[x][y].unchecked = False
		self.board[x][y].value = self.prevValue
		ct = 0
		for item in self.getNeighbors(x,y):
			if item.unchecked is True:
				ct +=1
		self.board[x][y].uncheckedNeighbors = ct
		self.checkNeighbors(x,y)

	def checkNeighbors(self,x,y):
		curTile = self.board[x][y]
		for neighbor in self.getNeighbors(x,y):
			if (neighbor.flagged is True) and (neighbor.unchecked is False) and curTile.value > 0:
				curTile.value -= 1

			neighbor.uncheckedNeighbors -= 1
			if (neighbor.uncheckedNeighbors == neighbor.value) and neighbor.value!=0:
				for n in self.getNeighbors(neighbor.x,neighbor.y):
					if n.unchecked and n.flagged is False:
						self.flag(n.x,n.y)
		
		#if the tile has no surrounding mines, add all its neighbors to self.toUncoverQueue
		if curTile.value == 0:								
			self.uncoverNeighbors(curTile.x,curTile.y)

		#if the number of covered tiles is == to t's value flag all t's covered neighbors
		if curTile.value == curTile.uncheckedNeighbors:		
			for neighbor in self.getNeighbors(x,y):
				if (neighbor.unchecked is True) and (neighbor.flagged is False):
					self.flag(neighbor.x,neighbor.y)		


	def flag(self,x,y):
		self.flagsLeft -= 1
		self.board[x][y].flagged = True
		self.minesToFlag.put(self.board[x][y])
		uncoveredNeighbors = []
		for neighbor in self.getNeighbors(x,y):
			if neighbor.unchecked == False:
				uncoveredNeighbors.append(neighbor)
		
		for n in uncoveredNeighbors:
			if n.value > 0:
				n.value -= 1
			if n.value == 0:
				self.uncoverNeighbors(n.x,n.y)


	#if the tile has value zero, add all its neighbors to the to the "toUncoverQueue"
	def uncoverNeighbors(self,x,y):				
		#if the tile value is zero make sure it's negihbors are uncovered
		for neighbor in self.getNeighbors(x,y):
			if neighbor.unchecked and neighbor.flagged is False:
				self.toUncoverQueue.put(self.board[neighbor.x][neighbor.y])
		return
	
	def updateFrontiers(self):
		newUncoveredFrontier = set()
		newCoveredFrontier = set()
		for tiles in self.uncoveredTiles:
			addToUncoveredFrontier = False

			for neighborTiles in self.getNeighbors(tiles.x,tiles.y):
				if neighborTiles.unchecked and neighborTiles.flagged is False:
					addToUncoveredFrontier = True
					if 0 <= neighborTiles.x < self.colDimension and 0<= neighborTiles.y < self.rowDimension:
						newCoveredFrontier.add(self.board[neighborTiles.x][neighborTiles.y])
			if addToUncoveredFrontier:
				newUncoveredFrontier.add(self.board[tiles.x][tiles.y])
		#sort the new frontiers and update the frontiers defined in the class
		#print("UC: ",len(self.uncoveredFrontier))
		#print("C: ",len(self.coveredFrontier))
		self.uncoveredFrontier = sorted(newUncoveredFrontier, key=lambda tile: (tile.x, tile.y))
		self.coveredFrontier = sorted(newCoveredFrontier, key=lambda tile: (tile.x, tile.y))
		

	def guess(self):
		self.updateFrontiers()
		if len(self.coveredFrontier) > self.threshold:
			self.coveredFrontier = self.getSmallCoveredFrontier(self.threshold)
			self.uncoveredFrontier = self.getSmallFrontierNeighbors(self.coveredFrontier)
		#get a smaller version of the frontiers to ensure that it doesnt take too long
		self.curMineConfigurations = 0

		#edge case
		#if there aren't any flags left then uncover all items in the coveredFrotier
		if self.flagsLeft==0:
			#print("here")
			for items in self.coveredFrontier:
				self.toUncoverQueue.put(self.board[items.x][items.y])
			return
		

		self.backtracking([],self.coveredFrontier.copy())
		print("Viable Mine Combinations:",self.curMineConfigurations)
		
		maxNeighbors = 0
		allZeros = True
		minProb = 1.0
		guessing = True
		
		#cover edge case
		if len(self.coveredFrontier) == 1:
			allZeros = False

		for item in self.coveredFrontier:
			chance = round(100*(item.total_1_count/self.curMineConfigurations), 2)
			print("Tile:", item.x+1,item.y+1, "Mine Probability: %", chance)

			if item.total_1_count !=0:
				allZeros = False

			
		#if no viable solutions were found given the heuristic constraints then use a rudimentary guessing algorithm
		if allZeros:
			self.basicGuess()
			return
		
		for items in self.coveredFrontier:
			item.mineProbability = item.total_1_count/self.curMineConfigurations
			if item.mineProbability <= minProb:
				minProb = item.mineProbability
			if items.total_1_count == 0:
				#print("Putting to uncover: ",items.x+1,items.y+1)
				guessing = False
				self.toUncoverQueue.put(self.board[items.x][items.y])
			
			if items.total_1_count==self.curMineConfigurations:
				#print("Putting to flag: ",items.x+1,items.y+1)
				guessing = False
				self.flag(items.x,items.y)
			
		if guessing is True:
			for items in self.coveredFrontier:
				if items.mineProbability==minProb:
					
					numberOfNeighbors = 0
					n = self.getNeighbors(items.x,items.y)

					for neighbor in n:
						if neighbor in self.uncoveredFrontier and neighbor.flagged is False:
							numberOfNeighbors +=1
					#print("item: ", items.x,items.y, "neighbors: ",numberOfNeighbors)
					if numberOfNeighbors >= maxNeighbors:
						bestGuess = items
						maxNeighbors = numberOfNeighbors

			print("likely guess: ", bestGuess.x+1, bestGuess.y+1)
			
			self.toUncoverQueue.put(self.board[bestGuess.x][bestGuess.y])
		
		for items in self.coveredFrontier:
			items.mineProbability = 0
			items.total_1_count = 0
		return


	def getSmallFrontierNeighbors(self,SCF):
		newUCF = set()
		for items in SCF:
			n = self.getNeighbors(items.x,items.y)
			for neighbors in n:
				if neighbors in self.uncoveredFrontier:
					newUCF.add(neighbors)
		return newUCF

	def getHeuristicFrontier(self):
		newSet = set()
		ct = 0
		for item in self.uncoveredFrontier:
			if ct>=self.threshold:
				break
			
	#get a portion of the uncovered frontier of tiles and use bfs to add neighboring tiles
	def getSmallCoveredFrontier(self,newFrontierSize):
		neighborCT = 0
		inCorner = 0
		startTile = next(iter(self.coveredFrontier))
		newSmallSet = set()
		for item in self.coveredFrontier:
			ct = 0
			for ncheck in self.getNeighbors(item.x,item.y):
				if ncheck.unchecked is True:
					ct +=1
			if ct > inCorner:
				item = startTile
		queue = [startTile]
		visited = set()
		visited.add(startTile)
		newSmallSet.add(startTile)

		while queue:
			if neighborCT > newFrontierSize:
				return newSmallSet
			vertex = queue.pop()
			n = self.getNeighbors(vertex.x,vertex.y)
			for neighbor in n:
				if neighbor not in visited:
					if neighbor in self.coveredFrontier:
						queue.append(neighbor)
						neighborCT += 1
						visited.add(neighbor)
						newSmallSet.add(neighbor)
		return newSmallSet


	def backtracking(self, flaggedMines, unassignedMines, memo=None):
		if memo is None:
			memo = {}
		
		flaggedMines = set(flaggedMines)
		unassignedMines = set(unassignedMines)  # Convert unassignedMines to a set
		flagged_mines_key = tuple(sorted((tile.x, tile.y) for tile in flaggedMines))
		memo_key = flagged_mines_key

		if memo_key in memo:
			return memo[memo_key]

		completion_status = self.checkCompletion(flaggedMines)
		if completion_status == "complete":
			self.curMineConfigurations += 1
			print("Viable Combination Found:", [(tile.x+1, tile.y+1) for tile in flaggedMines])
			for tile in flaggedMines:
				self.board[tile.x][tile.y].total_1_count += 1
			memo[memo_key] = "complete"
			return "complete"

		if completion_status == "failure":
			memo[memo_key] = "failure"
			return "failure"

		for value in unassignedMines:
			if value not in flaggedMines:
				new_flagged_mines = flaggedMines | {value}
				new_unassigned_mines = unassignedMines - {value}
				self.backtracking(new_flagged_mines, new_unassigned_mines, memo)


		memo[memo_key] = "failure"
		return "failure"

	def unflagPossibleMines(self,possibleMines):
		for item in possibleMines:
			self.board[item.x][item.y].mineFlag = False
	
	#recives a list of mines and checks weather the combination works within the constraints of the game
	#def validcombo(self,mines):
	
    # checkCompletion checks if the possible mine arrangement passes all constraints
    # complete = Uncovered tile values match mine arrangement
    # incomplete = Uncovered tile values is greater than the amount of mines (not enough mines)
    # failure = Number of mines exceeds at least one uncovered tile value
    # possibleMines is a list of all the flagged mines from backtracking
			
	def checkCompletion(self, possibleMines):
		status = "complete"
		if len(possibleMines) > self.flagsLeft:
			#print("More mines than flags in combo")
			return "failure"
		
		# Create a set of coordinates for mines for easy checking
		mine_coords = {(tile.x, tile.y) for tile in possibleMines}

		for item in self.uncoveredFrontier:
			if item.flagged:
				continue
			count = 0
			for item_neighbor in self.getNeighbors(item.x, item.y):
				if (item_neighbor.x, item_neighbor.y) in mine_coords:
					count += 1
			
			if count > item.value:
				#print(mine_coords, count, 'item coords,value', item.x, item.y, item.value,'failure')
				return "failure"
			
			if count != item.value:
				status = "incomplete"
		#print(status, mine_coords)
		return status

	#a very rudimentary guess that chooses the tile with the lowest sum of neighboring values.
	def basicGuess(self):
		print("BasicGuess")
		self.updateFrontiers()
		for items in self.coveredFrontier:
			tile = self.board[items.x][items.y]
			neighbors = self.getNeighbors(tile.x,tile.y)
			sum = 0
			if items.uncheckedNeighbors == 7:
				continue
			for n in neighbors:
				if n.unchecked is False and n.flagged is False and n.value>0:
					sum += n.value 
			items.pMine = sum

		minProb = float('inf')
		maxUncoveredNeighbors = 0
		minTile = self.uncoveredFrontier[0]
		for tile in self.coveredFrontier:
			if tile.pMine < minProb:
				minProb = tile.pMine
		
		#if there is a tie, prioritize the tile that has the most uncovered neighbors (reveals more info)
		for tile in self.coveredFrontier:
			if minProb == tile.pMine:
				if tile.uncheckedNeighbors >= maxUncoveredNeighbors:
					minTile = tile
		#print("basic guess coords: ",minTile.x,minTile.y)
		for tile in self.coveredFrontier:
			tile.pMine = 0
		
		self.toUncoverQueue.put(self.board[minTile.x][minTile.y])
		return 
	
	def getAction(self, number: int) -> "Action Object":
		self.prevValue = number

		self.checkTile(self.curX, self.curY)

		self.actionCounter += 1
		if self.actionCounter == (self.rowDimension * self.colDimension):
			return Action(AI.Action.LEAVE)
		
		while(1):
			# Process tiles suspected to be mines
			while not self.minesToFlag.empty():
				toFlag = self.minesToFlag.get()
				if toFlag not in self.uncoveredTiles:
					self.curX = toFlag.x
					self.curY = toFlag.y
					return Action(AI.Action.FLAG, toFlag.x, toFlag.y)

			# If there are no suspected mines, process tiles suspected to NOT be mines
			while not self.toUncoverQueue.empty():
				toUncover = self.toUncoverQueue.get()
				if toUncover not in self.uncoveredTiles:
					self.curX = toUncover.x
					self.curY = toUncover.y
					return Action(AI.Action.UNCOVER, toUncover.x, toUncover.y)
			# if we are out of tiles to process find the best guess
			self.guess()
			
	class Tile:
		def __init__(self, x, y):
			self.x = x
			self.y = y
			self.value = -10
			self.unchecked = True
			self.pMine = 1000
			
			self.uncheckedNeighbors = 8
			self.flagged = False
			
			## backtracking attributes ##

            # mineFlag marks possible mines for the backtracking solutions
			self.mineFlag = False
			
            # total_1_count : total amount that tile is a mine in all backtracking solutions
			self.mineProbability = 0.0
			self.total_1_count = 0
