import random
import sys
import mdp
import environment
import util
import optparse
import time
from physicalMachine import *

class BaePlatform(mdp.MarkovDecisionProcess):
  """
    BaePlatform
  """
  def __init__(self, pm):
    # layout
    #if type(grid) == type([]): grid = makeGrid(grid)
    #self.grid = grid
    
    # parameters
    self.livingReward = 0.0
    self.numinteration = 16
    self.currentnum = 0
    self.pm = pm
       
  def doAction(self, state, action):
    print "mem,cpu"
    print self.pm.mem,self.pm.cpu
    plController = PlatformController()
    if action == 'nop':
      return state
    if action == 'inch':
      for id in self.pm.instances.keys():
	ins =  self.pm.instances[id]
	if ins.isFailed():
	  plController.add(ins)
      return self.pm.getState()
    if action == 'incv':
      for id in self.pm.instances.keys():
	ins =  self.pm.instances[id]
	if ins.isFailed():
	  self.pm.enlargeInstance(id, ins.mem)
      return self.pm.getState()
    if action == 'decv':
      for id in self.pm.instances.keys():
	ins =  self.pm.instances[id]
	if not ins.isFailed() and ins.mem >= 1:
	  self.pm.shrinkInstance(id, ins.mem/2)
      return self.pm.getState()
    if action == 'dech':
      for id in self.pm.instances.keys():
	ins =  self.pm.instances[id]
	if not ins.isFailed() and ins.cpu < 20:
	  plController.dec(id)
      return self.pm.getState()
    if action == 'move':
      #plController.move
      return self.pm.getState()

  def setNoise(self, numinteration):
    """
    The probability of moving in an unintended direction.
    """
    self.numinteration = numinteration
        
                                    
  def getPossibleActions(self, state):
    """
    Returns list of valid actions for 'state'.
    
    Note that you can request moves into walls and
    that "exit" states transition to the terminal
    state under the special action "done".
    """
    #if state == self.grid.terminalState:
     # return ()
    ucpu,umem,nvins = state
    ops = ['nop','move','dech','decv','inch','incv']
    if ucpu == 2:
      ops.remove('dech')
      ops.remove('decv')
    if umem == 2:
      ops.remove('incv')
    if ucpu == 0:
      ops.remove('inch')
      if 'incv' in ops: ops.remove('incv')
    if nvins > 0:
      if 'dech' in ops: ops.remove('dech')
      if 'decv' in ops: ops.remove('decv')
    return ops
    
  def getStates(self):
    """
    Return list of all states.
    """
    # The true terminal state.
    states = []
    for x in range(3):
      for y in range(3):
        for z in range(4):
          state = (x,y,z)
          states.append(state)
    return states
        
  def getReward(self, state, action, nextState):
    """
    Get reward for state, action, nextState transition.
    
    Note that the reward depends only on the state being
    departed (as in the R+N book examples, which more or
    less use this convention).
    """
    ucpu,umem,nvins = state
    nucpu,numem,nnvins = nextState
    reward = (nvins - nnvins) * 5
    if nucpu == 1 and ucpu != 1: 
      reward += 1
    if numem == 1 and umem != 1: 
      reward += 1
    if ucpu == 1 and nucpu != 1: 
      reward -= 1
    if umem == 1 and numem != 1: 
      reward -= 1
    
    return reward
        
  def getState(self):
    # TO DO: get state from monitor
    state = self.pm.getState()
    return state
  
  def isTerminal(self):
    return self.numinteration == self.currentnum
       
class BaeplatformEnvironment(environment.Environment):
    
  def __init__(self, baePlatform):
    self.baeplatform = baePlatform
    self.reset()
            
  def getCurrentState(self):
    return self.state
        
  def getPossibleActions(self, state):        
    return self.baeplatform.getPossibleActions(state)
        
  def doAction(self, action):
    state = self.getCurrentState()
    # TO DO: execute the action and get nextState
    nextState = self.baeplatform.doAction(state, action)
    reward = self.baeplatform.getReward(state, action, nextState)
    self.baeplatform.currentnum += 1
    self.state = nextState
    return (nextState, reward)
        
  def reset(self):
    self.baeplatform.currentnum = 0
    self.state = self.baeplatform.getState()
  
  def isTerminal(self):
    return self.baeplatform.isTerminal()

def printString(x): print x

def getUserAction(state, actionFunction):
  """
  Get an action from the user (rather than the agent).
  
  Used for debugging and lecture demos.
  """
  import graphicsUtils
  action = None
  while True:
    keys = graphicsUtils.wait_for_keys()
    if 'Up' in keys: action = 'north'
    if 'Down' in keys: action = 'south'
    if 'Left' in keys: action = 'west'
    if 'Right' in keys: action = 'east'
    if 'q' in keys: sys.exit(0)
    if action == None: continue
    break
  actions = actionFunction(state)
  if action not in actions:
    action = actions[0]
  return action

def runEpisode(agent, environment, discount, decision, display, message, pause, episode, rates, offset):
  returns = 0
  totalDiscount = 1.0
  environment.reset()
  if 'startEpisode' in dir(agent): agent.startEpisode()
  message("BEGINNING EPISODE: "+str(episode)+"\n")
  pm = environment.baeplatform.pm
  while True:

    # DISPLAY CURRENT STATE
    state = environment.getCurrentState()
    pause()
    
    # END IF IN A TERMINAL STATE
    if environment.isTerminal():
      message("EPISODE "+str(episode)+" COMPLETE: RETURN WAS "+str(returns)+"\n")
      return returns, offset
    #print rates[offset%len(rates)]
    pm.readFromFile()
    for id in pm.instances.keys():
      ins = pm.instances[id]
      ins.setByReqrate(rates[offset%len(rates)])
    offset += 1
    # GET ACTION (USUALLY FROM AGENT)
    action = decision(state)
    if action == None:
      raise 'Error: Agent returned None action'
    
    # EXECUTE ACTION
    nextState, reward = environment.doAction(action)
    message("Started in state: "+str(state)+
            "\nTook action: "+str(action)+
            "\nEnded in state: "+str(nextState)+
            "\nGot reward: "+str(reward)+"\n")    
    # UPDATE LEARNER
    if 'observeTransition' in dir(agent):
        agent.observeTransition(state, action, nextState, reward)
    
    returns += reward * totalDiscount
    totalDiscount *= discount
    pm.writeToFile()

  if 'stopEpisode' in dir(agent):
    agent.stopEpisode()

def parseOptions():
    optParser = optparse.OptionParser()
    optParser.add_option('-d', '--discount',action='store',
                         type='float',dest='discount',default=0.9,
                         help='Discount on future (default %default)')
    optParser.add_option('-r', '--livingReward',action='store',
                         type='float',dest='livingReward',default=0.0,
                         metavar="R", help='Reward for living for a time step (default %default)')
    optParser.add_option('-n', '--noise',action='store',
                         type='float',dest='noise',default=0.2,
                         metavar="P", help='How often action results in ' +
                         'unintended direction (default %default)' )
    optParser.add_option('-e', '--epsilon',action='store',
                         type='float',dest='epsilon',default=0.3,
                         metavar="E", help='Chance of taking a random action in q-learning (default %default)')
    optParser.add_option('-l', '--learningRate',action='store',
                         type='float',dest='learningRate',default=0.5,
                         metavar="P", help='TD learning rate (default %default)' )
    optParser.add_option('-i', '--iterations',action='store',
                         type='int',dest='iters',default=10,
                         metavar="K", help='Number of rounds of value iteration (default %default)')
    optParser.add_option('-k', '--episodes',action='store',
                         type='int',dest='episodes',default=1,
                         metavar="K", help='Number of epsiodes of the MDP to run (default %default)')
    optParser.add_option('-g', '--grid',action='store',
                         metavar="G", type='string',dest='grid',default="BookGrid",
                         help='Grid to use (case sensitive; options are BookGrid, BridgeGrid, CliffGrid, MazeGrid, default %default)' )
    optParser.add_option('-w', '--windowSize', metavar="X", type='int',dest='gridSize',default=150,
                         help='Request a window width of X pixels *per grid cell* (default %default)')
    optParser.add_option('-a', '--agent',action='store', metavar="A",
                         type='string',dest='agent',default="random",
                         help='Agent type (options are \'random\', \'value\' and \'q\', default %default)')
    optParser.add_option('-t', '--text',action='store_true',
                         dest='textDisplay',default=False,
                         help='Use text-only ASCII display')
    optParser.add_option('-p', '--pause',action='store_true',
                         dest='pause',default=False,
                         help='Pause GUI after each time step when running the MDP')
    optParser.add_option('-q', '--quiet',action='store_true',
                         dest='quiet',default=False,
                         help='Skip display of any learning episodes')
    optParser.add_option('-s', '--speed',action='store', metavar="S", type=float,
                         dest='speed',default=1.0,
                         help='Speed of animation, S > 1.0 is faster, 0.0 < S < 1.0 is slower (default %default)')
    optParser.add_option('-m', '--manual',action='store_true',
                         dest='manual',default=False,
                         help='Manually control agent')
    optParser.add_option('-v', '--valueSteps',action='store_true' ,default=False,
                         help='Display each step of value iteration')

    opts, args = optParser.parse_args()
    
    if opts.manual and opts.agent != 'q':
      print '## Disabling Agents in Manual Mode (-m) ##'
      opts.agent = None

    # MANAGE CONFLICTS
    if opts.textDisplay or opts.quiet:
    # if opts.quiet:      
      opts.pause = False
      # opts.manual = False
      
    if opts.manual:
      opts.pause = True
      
    return opts

def run(env, s, episodes, a, discount, decisionCallback, displayCallback, messageCallback, pauseCallback):
  s.aquire()  
  if episodes > 0:
    print
    print "RUNNING", opts.episodes, "EPISODES"
    print
  infile = open('infile')
  rates = []
  offset = 0
  for line in infile:
    rates.append(int(line))
  returns = 0
  for episode in range(1, episodes+1):
    tmpre, offset = runEpisode(a, env, discount, decisionCallback, displayCallback, messageCallback, pauseCallback, episode, rates, offset)
    returns += tmpre 
  if episodes > 0:
    print
    print "AVERAGE RETURNS FROM START STATE: "+str((returns+0.0) / episodes)
    print 
    print
    
    display.displayQValues(a, message = "Q-VALUES AFTER "+str(episodes)+" EPISODES")
    display.pause()
    display.displayValues(a, message = "VALUES AFTER "+str(episodes)+" EPISODES")
    display.pause()
  s.release()  
  
if __name__ == '__main__':
  
  import multiprocessing
  import baeplatform
  opts = parseOptions()
  env = []
  for x in range(3):
    pm = PhysicalMachine(x)
    for i in range(50):
      ins = Instance(i)
      pm.addInstance(ins)
    pm.writeToFile()
    mdp = baeplatform.BaePlatform(pm)
    env.append(baeplatform.BaeplatformEnvironment(mdp))

  ###########################
  # GET THE DISPLAY ADAPTER
  ###########################
  import textGridworldDisplay
  display = textGridworldDisplay.TextGridworldDisplay(mdp)
  '''
  if not opts.textDisplay:
    import graphicsGridworldDisplay
    display = graphicsGridworldDisplay.GraphicsGridworldDisplay(mdp, opts.gridSize, opts.speed)
  display.start()
  '''
  ###########################
  # GET THE AGENT
  ###########################

  import valueIterationAgents, qlearningAgents
  a = None
  if opts.agent == 'value':
    a = valueIterationAgents.ValueIterationAgent(mdp, opts.discount, opts.iters)
  elif opts.agent == 'q':
    #env.getPossibleActions, opts.discount, opts.learningRate, opts.epsilon
    #simulationFn = lambda agent, state: simulation.GridworldSimulation(agent,state,mdp)
    #gridWorldEnv = GridworldEnvironment(mdp)
    actionFn = lambda state: mdp.getPossibleActions(state)
    qLearnOpts = {'gamma': opts.discount, 
                  'alpha': opts.learningRate, 
                  'epsilon': opts.epsilon,
                  'actionFn': actionFn}
    a = qlearningAgents.QLearningAgent(**qLearnOpts)
  elif opts.agent == 'random':
    # # No reason to use the random agent without episodes
    if opts.episodes == 0:
      opts.episodes = 10
    class RandomAgent:
      def getAction(self, state):
        return random.choice(mdp.getPossibleActions(state))
      def getValue(self, state):
        return 0.0
      def getQValue(self, state, action):
        return 0.0
      def getPolicy(self, state):
        "NOTE: 'random' is a special policy value; don't use it in your code."
        return 'random'
      def update(self, state, action, nextState, reward):
        pass      
    a = RandomAgent()
  else:
    if not opts.manual: raise 'Unknown agent type: '+opts.agent
    
    
  ###########################
  # RUN EPISODES
  ###########################
  # DISPLAY Q/V VALUES BEFORE SIMULATION OF EPISODES
  if not opts.manual and opts.agent == 'value':
    if opts.valueSteps:
      for i in range(opts.iters):
        tempAgent = valueIterationAgents.ValueIterationAgent(mdp, opts.discount, i)
        display.displayValues(tempAgent, message = "VALUES AFTER "+str(i)+" ITERATIONS")
        display.pause()        
    
    display.displayValues(a, message = "VALUES AFTER "+str(opts.iters)+" ITERATIONS")
    display.pause()
    display.displayQValues(a, message = "Q-VALUES AFTER "+str(opts.iters)+" ITERATIONS")
    display.pause()
    
  

  # FIGURE OUT WHAT TO DISPLAY EACH TIME STEP (IF ANYTHING)
  displayCallback = lambda x: None
  if not opts.quiet:
    if opts.manual and opts.agent == None: 
      displayCallback = lambda state: display.displayNullValues(state)
    else:
      if opts.agent == 'random': displayCallback = lambda state: display.displayValues(a, state, "CURRENT VALUES")
      if opts.agent == 'value': displayCallback = lambda state: display.displayValues(a, state, "CURRENT VALUES")
      if opts.agent == 'q': displayCallback = lambda state: display.displayQValues(a, state, "CURRENT Q-VALUES")

  messageCallback = lambda x: printString(x)
  if opts.quiet:
    messageCallback = lambda x: None

  # FIGURE OUT WHETHER TO WAIT FOR A KEY PRESS AFTER EACH TIME STEP
  pauseCallback = lambda : None
  if opts.pause:
    pauseCallback = lambda : display.pause()

  # FIGURE OUT WHETHER THE USER WANTS MANUAL CONTROL (FOR DEBUGGING AND DEMOS)  
  if opts.manual:
    decisionCallback = lambda state : getUserAction(state, mdp.getPossibleActions)
  else:
    decisionCallback = a.getAction  
    
  # RUN EPISODES
  s = multiprocessing.Semaphore(len(env))
  execution_queue = []
  for i in range(len(env)):
    p = multiprocessing.Process(target=run, args=(env[i],s,opts.episodes, a, opts.discount, decisionCallback, displayCallback, messageCallback, pauseCallback))
    p.start()
    execution_queue.append(p)
  for p in execution_queue:
    p.join()

  
