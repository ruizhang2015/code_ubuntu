import mdp, util
import time
from learningAgents import ValueEstimationAgent

class ValueIterationAgent(ValueEstimationAgent):
  """
      * Please read learningAgents.py before reading this.*

      A ValueIterationAgent takes a Markov decision process
      (see mdp.py) on initialization and runs value iteration
      for a given number of iterations using the supplied
      discount factor.
  """
  def __init__(self, mdp, discount = 0.9, iterations = 100):
    """
      Your value iteration agent should take an mdp on
      construction, run the indicated number of iterations
      and then act according to the resulting policy.
    
      Some useful mdp methods you will use:
          mdp.getStates()
          mdp.getPossibleActions(state)
          mdp.getTransitionStatesAndProbs(state, action)
          mdp.getReward(state, action, nextState)
    """
    self.mdp = mdp
    self.discount = discount
    self.iterations = iterations
    #self.values = util.Counter() # A Counter is a dict with default 0
    "*** YOUR CODE HERE ***"
    self.qvalues = util.Counter()

    tmp_values = util.Counter()
    states = mdp.getStates()
    for i in range(self.iterations + 1):            # qvalues add one interation than values
        self.values = util.Counter.copy(tmp_values)
        for state in states:
            actions = mdp.getPossibleActions(state)
            if (not actions):
                tmp_values[state] = 0
            else:
                tmp_values[state] = -100
            for action in actions:
                value = 0
                #print mdp.getTransitionStatesAndProbs(state,action),state
                for nextstate, prob in mdp.getTransitionStatesAndProbs(state, action):
                    value += 1.0 * prob * (mdp.getReward(state, action, nextstate) + discount * self.values[nextstate])
                if (tmp_values[state] < value):
                    tmp_values[state] = value
                self.qvalues[state, action] = value
        #print self.values
        #print self.qvalues
        #print
    #time.sleep(60)
  def getValue(self, state):
    """
      Return the value of the state (computed in __init__).
    """
    return self.values[state]


  def getQValue(self, state, action):
    """
      The q-value of the state action pair
      (after the indicated number of value iteration
      passes).  Note that value iteration does not
      necessarily create this quantity and you may have
      to derive it on the fly.
    """
    "*** YOUR CODE HERE ***"
    return self.qvalues[state, action]

  def getPolicy(self, state):
    """
      The policy is the best action in the given state
      according to the values computed by value iteration.
      You may break ties any way you see fit.  Note that if
      there are no legal actions, which is the case at the
      terminal state, you should return None.
    """
    "*** YOUR CODE HERE ***"
    actions = self.mdp.getPossibleActions(state)
    if (not actions):
        return None
    maxqvalue = -1000
    for action in actions:
        if (maxqvalue < self.qvalues[state, action]):
            maxqvalue = self.qvalues[state, action]
            optac = action
    return optac

  def getAction(self, state):
    "Returns the policy at the state (no exploration)."
    return self.getPolicy(state)
  
