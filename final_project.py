
from __future__ import print_function

from future import standard_library

standard_library.install_aliases()
from builtins import range
from builtins import object
import MalmoPython
import json
import logging
import os
import random
import sys
import time

if sys.version_info[0] == 2:
    import Tkinter as tk
else:
    import tkinter as tk


class TabQAgent(object):
    """Tabular Q-learning agent for discrete state/action spaces."""

    def __init__(self):

        self.epsilon = 0.05  # exploration rate
        self.alpha = 0.2     # learning rate
        self.gamma = 0.8  # reward discount factor

        self.logger = logging.getLogger(__name__)
        if False:  # True if you want to see more information
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self.logger.handlers = []
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        


        self.actions = ["movenorth 1", "movesouth 1", "movewest 1", "moveeast 1"]
        self.q_table = {}
        self.canvas = None
        self.root = None

    ### Change q_table to reflect what we have learnt.
    # Inputs: reward - int, current_state - coordinate tuple, prev_state - coordinate tuple, prev_a - int
    # Output: updated q_table
    def updateQTable(self, reward, current_state, prev_state, prev_a):
        self.q_table[prev_state][prev_a] = self.alpha * (reward + (self.gamma * max(self.q_table[current_state]))) + (1-self.alpha) * (self.q_table[prev_state][prev_a])
        return
    ### Change q_table to reflect what we have learnt upon reaching the terminal state.
    # Input: reward - int, prev_state - coordinate tuple, prev_a - int
    # Output: updated q_table
    def updateQTableFromTerminatingState(self, reward, prev_state, prev_a):
        if reward > 0:
            self.q_table[prev_state][prev_a] = 100
        
        if reward <= -100:
            self.q_table[prev_state][prev_a] = -100

        return


    def act(self, world_state, agent_host, current_r):
        obs_text = world_state.observations[-1].text
        obs = json.loads(obs_text)  # most recent observation
        self.logger.debug(obs)
        if not u'XPos' in obs or not u'ZPos' in obs:
            self.logger.error("Incomplete observation received: %s" % obs_text)
            return 0
        current_s = "%d:%d" % (int(obs[u'XPos']), int(obs[u'ZPos']))
        self.logger.debug("State: %s (x = %.2f, z = %.2f)" % (current_s, float(obs[u'XPos']), float(obs[u'ZPos'])))
        if current_s not in self.q_table:
            self.q_table[current_s] = ([0] * len(self.actions))

        # update Q values
        if self.prev_s is not None and self.prev_a is not None:
            self.updateQTable(current_r, current_s, self.prev_s, self.prev_a)

        self.drawQ(curr_x=int(obs[u'XPos']), curr_y=int(obs[u'ZPos']))



        def moveRight(ah):
            ah.sendCommand("strafe 1")
            time.sleep(0.05)


        def moveLeft(ah):
            ah.sendCommand("strafe -1")
            time.sleep(0.05)


        def moveStraight(ah):
            ah.sendCommand("move 1")
            time.sleep(0.05)


        def moveBack(ah):
            ah.sendCommand("move -1")
            time.sleep(0.05)


        def legal(x, y):
            LegalMoves = []
            if y < 13:
                LegalMoves.append("up")
            if y > 0:
                LegalMoves.append("down")
            if x < 5:
                LegalMoves.append("right")
            if x > 0:
                LegalMoves.append("left")
            return LegalMoves

        p = current_s.split(":")
        xp = int(p[0])
        yp = int(p[1])
        
        legal = legal(xp, yp)
    
        if random.random() <= self.epsilon:
            num = random.randint(0,3)
            if num == 0: # up
                moveStraight(agent_host)
                self.prev_a = 0
                self.prev_s = current_s
            if num == 1: # down
                moveBack(agent_host)
                self.prev_a = 1
                self.prev_s = current_s 
            if num == 2:# left
                moveLeft(agent_host)
                self.prev_a = 2
                self.prev_s = current_s 
            if num == 3: #right
                moveRight(agent_host)
                self.prev_a = 3
                self.prev_s = current_s  

        else:
            valC = max(self.q_table[current_s])
            spots = []
            for i in range(len(self.q_table[current_s])):
                if(self.q_table[current_s][i]==valC):
                    spots.append(i)

            randomMove = random.choice(spots)
            if randomMove == 0: # up
                moveStraight(agent_host)
                self.prev_a = 0
            if randomMove == 1: # down
                moveBack(agent_host)
                self.prev_a = 1
            if randomMove == 2:# left
                moveLeft(agent_host)
                self.prev_a = 2
            if randomMove == 3: #right
                moveRight(agent_host)
                self.prev_a = 3
            
            self.prev_s = current_s

        return current_r

    # do not change this function
    def run(self, agent_host):
        """run the agent on the world"""

        total_reward = 0

        self.prev_s = None
        self.prev_a = None

        is_first_action = True

        # TODO complete the main loop:
        world_state = agent_host.getWorldState()
        while world_state.is_mission_running:
            current_r = 0

            if is_first_action:
                # wait until have received a valid observation
                while True:
                    time.sleep(0.1)
                    world_state = agent_host.getWorldState()
                    for error in world_state.errors:
                        self.logger.error("Error: %s" % error.text)
                    for reward in world_state.rewards:
                        current_r += reward.getValue()
                    if world_state.is_mission_running and len(world_state.observations) > 0 and not \
                    world_state.observations[-1].text == "{}":
                        total_reward += self.act(world_state, agent_host, current_r)
                        break
                    if not world_state.is_mission_running:
                        break
                is_first_action = False
            else:
                # wait for non-zero reward
                while world_state.is_mission_running and current_r == 0:
                    time.sleep(0.1)
                    world_state = agent_host.getWorldState()
                    for error in world_state.errors:
                        self.logger.error("Error: %s" % error.text)
                    for reward in world_state.rewards:
                        current_r += reward.getValue()
                # allow time to stabilise after action
                while True:
                    time.sleep(0.1)
                    world_state = agent_host.getWorldState()
                    for error in world_state.errors:
                        self.logger.error("Error: %s" % error.text)
                    for reward in world_state.rewards:
                        current_r += reward.getValue()
                    if world_state.is_mission_running and len(world_state.observations) > 0 and not \
                    world_state.observations[-1].text == "{}":
                        total_reward += self.act(world_state, agent_host, current_r)
                        break
                    if not world_state.is_mission_running:
                        break


        # process final reward
        total_reward += current_r

        # update Q values


        agent_host.sendCommand("use 1")
        
        
        if self.prev_s is not None and self.prev_a is not None:
            self.updateQTableFromTerminatingState(current_r, self.prev_s, self.prev_a)

        # used to dynamically draw the QTable in a separate window
        self.drawQ()

        return total_reward

    # do not change this function
    def drawQ(self, curr_x=None, curr_y=None):
        scale = 50
        world_x = 6
        world_y = 14
        if self.canvas is None or self.root is None:
            self.root = tk.Tk()
            self.root.wm_title("Q-table")
            self.canvas = tk.Canvas(self.root, width=world_x * scale, height=world_y * scale, borderwidth=0,
                                    highlightthickness=0, bg="black")
            self.canvas.grid()
            self.root.update()
        self.canvas.delete("all")
        action_inset = 0.1
        action_radius = 0.1
        curr_radius = 0.2
        action_positions = [(0.5, action_inset), (0.5, 1 - action_inset), (action_inset, 0.5), (1 - action_inset, 0.5)]
        # (NSWE to match action order)
        min_value = -20
        max_value = 20
        for x in range(world_x):
            for y in range(world_y):
                s = "%d:%d" % (x, y)
                self.canvas.create_rectangle(x * scale, y * scale, (x + 1) * scale, (y + 1) * scale, outline="#fff",
                                             fill="#002")
                for action in range(4):
                    if not s in self.q_table:
                        continue
                    value = self.q_table[s][action]
                    
                    color = int(255 * (value - min_value) / (max_value - min_value))  # map value to 0-255
                    color = max(min(color, 255), 0)  # ensure within [0,255]
                    color_string = '#%02x%02x%02x' % (255 - color, color, 0)
                    self.canvas.create_oval((x + action_positions[action][0] - action_radius) * scale,
                                            (y + action_positions[action][1] - action_radius) * scale,
                                            (x + action_positions[action][0] + action_radius) * scale,
                                            (y + action_positions[action][1] + action_radius) * scale,
                                            outline=color_string, fill=color_string)
        if curr_x is not None and curr_y is not None:
            self.canvas.create_oval((curr_x + 0.5 - curr_radius) * scale,
                                    (curr_y + 0.5 - curr_radius) * scale,
                                    (curr_x + 0.5 + curr_radius) * scale,
                                    (curr_y + 0.5 + curr_radius) * scale,
                                    outline="#fff", fill="#fff")
        self.root.update()


if sys.version_info[0] == 2:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately
else:
    import functools

    print = functools.partial(print, flush=True)

agent = TabQAgent()
agent_host = MalmoPython.AgentHost()
try:
    agent_host.parse(sys.argv)
except RuntimeError as e:
    print('ERROR:', e)
    print(agent_host.getUsage())
    exit(1)

# -- set up the mission -- #

mission_file = './final.xml'
with open(mission_file, 'r') as f:
    print("Loading mission from %s" % mission_file)
    mission_xml = f.read()
    my_mission = MalmoPython.MissionSpec(mission_xml, True)

# add some random holes in the ground to spice things up


for x in range(5, 12):
    my_mission.drawBlock(x, 61, 5, "ice")
    my_mission.drawBlock(x, 61, 11, "ice")
    my_mission.drawBlock(x, 66, 9, "ice")
    my_mission.drawBlock(x, 66, 15, "ice")


my_mission.drawBlock(8, 66, 9, "air")
my_mission.drawBlock(8, 66, 5, "air")
my_mission.drawBlock(7, 67, 10, "ice")
my_mission.drawBlock(9, 67, 10, "ice")  

for z in range(5, 12):
    my_mission.drawBlock(5, 61, z, "ice")
    my_mission.drawBlock(11, 61, z, "ice")
    
for z in range(10, 15):
    my_mission.drawBlock(5, 66, z, "ice")
    my_mission.drawBlock(11, 66, z, "ice")

'''
    for z in range(4, 12):
        if (x < 5)
            my_mission.drawBlock(x, 61, z, "water")
'''


max_retries = 3

num_repeats = 150

cumulative_rewards = []

'''
val = input("Input: ")

if (val == "Yes"):
    print("Hello")
'''


for i in range(num_repeats):

    print()
    print('Repeat %d of %d' % (i + 1, num_repeats))

    my_mission_record = MalmoPython.MissionRecordSpec()

    for retry in range(max_retries):
        try:
            agent_host.startMission(my_mission, my_mission_record)
            break
        except RuntimeError as e:
            if retry == max_retries - 1:
                print("Error starting mission:", e)
                exit(1)
            else:
                time.sleep(2.5)

    print("Waiting for the mission to start", end=' ')
    world_state = agent_host.getWorldState()
    while not world_state.has_mission_begun:
        print(".", end="")
        time.sleep(0.1)
        world_state = agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:", error.text)
    print()

    # -- run the agent in the world -- #
    cumulative_reward = agent.run(agent_host)
    print('Cumulative reward: %d' % cumulative_reward)
    cumulative_rewards += [cumulative_reward]

    # -- clean up -- #
    time.sleep(0.5)  # (let the Mod reset)

print("Done.")

print()
print("Cumulative rewards for all %d runs:" % num_repeats)
print(cumulative_rewards)


