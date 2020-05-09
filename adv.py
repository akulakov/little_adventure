#!/usr/bin/env python
"""
bugs

TODO
    - update stairs on screen 2
    - fast move attacks 5x in one turn

races: Spheros, Rabbibunnies, Quetches, Grobos
"""
from curses import wrapper, newwin
import curses
import sys
from copy import copy, deepcopy
from time import sleep
from random import random, choice
from collections import defaultdict
from textwrap import wrap
import string

start_x_loc = 30
rock = '█'
blank = ' '
HEIGHT = 16
GROUND = HEIGHT-2   # ground level
LOAD_BOARD = 999
SLP = 0.01
SEQ_TYPES = (list, tuple)
debug_log = open('debug', 'w')
triggered_events = []
done_events = set()
boards = []
objects = {}
timers = []
map_to_loc = {}


class Blocks:
    platform = '▁'
    bell = '🔔'
    grill = '▒'
    rubbish = '♽'
    truck = '🚚'
    locker = '🔲'
    grn_heart = '💚'
    coin = '🌕'
    key = '🔑'
    door = '🚪'
    block1 = '▐'
    steps_r = '▞'
    steps_l = '▚'
    platform_top = '▔'
    ladder = '☰'
    honey = '🍯'
    shelves = '☷'
    chair = '⑁'
    fountain = '‿' # TODO find a new unicode; doesn't work
    small_table = '▿'
    table2 = '⍡'
    stool = '⍑'
    underline = '▁'
    cupboard = '⌸'
    sunflower = '🌻'
    magic_ball = '❂'
    crate1 = '◧'
    crate2 = '◨'
    crate3 = '◩'
    crate4 = '◪'
    smoke_pipe = '⧚'
    fireplace = '⩟'
    water = '⏖'
    elephant = '🐘'     # Grobo
    rabbit = '🐰'
    wine = '🍷'
    dock_boards = '⏔'
    ticket_seller = '⌂'
    ferry = '🚤'
    ferry_ticket = 't'
    soldier = '⍾'
    bars = '┇'
    tree1 = '🌲'
    tree2 = '🌳'
    books = '📚'
    open_book = '📖'
    guardrail_l = '╔'
    guardrail_r = '╕'
    guardrail_m = '╤'
    tulip = '🌷'
    monkey = '🐵'
    antitank = '⋇'
    red_circle = '🔴'
    # rock2 = '║'
    rock2 = '▧'
    rock3 = '▓'
    platform2 = '▭'
    angled1 = '╱'
    angled2 = '╲'
    picture = '🖼'
    hexagon = '⎔'
    car = '🚗'
    blue_round = '🔵' # unused
    bottle = '℧'
    box1 = '⊟'
    cactus = '🌵'
    lever = '⎆'
    statue = 'Ω'
    sharp_rock = '⩕'

    crates = (crate1, crate2, crate3, crate4)


class Stance:
    normal = 1
    fight = 2
    sneaky = 3
STANCES = {v:k for k,v in Stance.__dict__.items()}

class Type:
    platform_top = 2
    ladder = 3
    fountain = 4
    chair = 5
    door_top_block = 6
    container = 7
    door1 = 8
    crate = 9
    door2 = 10
    water = 11
    event_trigger = 12
    blocking = 13
    door3 = 14
    deadly = 15

BLOCKING = [rock, Type.door1, Type.door2, Type.door3, Blocks.block1, Blocks.steps_r, Blocks.steps_l, Type.platform_top,
            Type.door_top_block, Type.blocking]

class ID:
    platform1 = 1
    grill1 = 2
    alarm1 = 3
    grill2 = 5
    rubbish1 = 6
    truck1 = 7
    locker = 8
    coin = 9
    grn_heart = 10
    key1 = 11
    door1 = 12
    platform_top1 = 13
    jar_syrup = 14
    shelves = 15
    magic_ball = 16
    crate1 = 17
    door2 = 18
    grill3 = 19
    wine = 20
    key2 = 21
    door3 = 22
    key3 = 23
    grill4 = 24
    ticket_seller1 = 25
    ferry = 26
    ferry_ticket = 27
    grill5 = 28
    grill6 = 29
    bars1 = 30
    red_card = 31
    grill7 = 32
    sink = 33
    grill8 = 34
    drawing = 35
    car = 36
    empty_bottle = 37
    car2 = 38
    fuel = 39
    sailboat = 40
    lever1 = 41
    lever2 = 42
    statue = 43
    platform3 = 44
    lever3 = 45
    lever4 = 46
    lever5 = 47
    platform4 = 48
    platform5 = 49
    platform6 = 50
    book_of_bu = 51

    guard1 = 100
    technician1 = 101
    player = 102
    soldier1 = 103
    robobunny1 = 104
    shopkeeper1 = 105
    max_ = 106
    anthony = 107
    julien = 108
    soldier2 = 109
    guard2 = 110
    wally = 111
    chamonix = 112
    agen = 113
    agen2 = 114
    clermont_ferrand = 115
    brenne = 116
    trier = 117
    morvan = 118
    morvan2 = 119
    montbard = 120
    astronomer = 121
    groboclone1 = 122
    locksmith = 123
    maurice = 124
    clermont_ferrand2 = 125
    clermont_ferrand3 = 126
    aubigny = 127
    olivet = 128
    olivet2 = 129

    max1 = 200
    max2 = 201
    trick_guard = 202
    talk_to_brenne = 203
    water_supply = 204

    sea_level1 = 300
    landscape_level1 = 301
    water_tower_level = 302
    port_beluga_level = 303

    legend1 = 400
    fall = 401  # move that falls through to the map below


items_by_id = {v:k for k,v in ID.__dict__.items()}
descr_by_id = copy(items_by_id)
descr_by_id.update(
    {
     14: 'a jar of syrup',
     10: 'a green heart',
     11: 'a simple key',
     9 : 'kashes',
    }
)

conversations = {
    ID.robobunny1: ['I like to rummage through the rubbish pile.. this area is not closely watched! I hide in the garbage truck and come here when I can. You just have to be very DISCREET!'],
    ID.shopkeeper1: ['Twinsen!? I thought you were arrested?', 'They let me out early for good behaviour!', 'But.. nobody gets out of Citadel alive! I.. I.. have to call the guards.'],
    ID.max1: ['Have you seen a young girl being led by two clones?', 'I think I have seen her and I will tell you more if you buy me a drink.'],
    ID.max2: ["I've seen them near the port, it looked like they were getting away from the island, which is strange, because usually prisoners stay in the citadel", 'Thank you!'],
    ID.julien: ['Have you seen a young girl being led by two Groboclones?', 'Yes, they were here earlier today, they got on a speedboat and were off. Destination unknown.'],
    ID.soldier2: ['Wait! How did you get here, and who are you?',
                  ["I'm Twinsen, I'm escaping!", "Fixing the antenna.", "Santa Claus."]],
    ID.guard2: ['Hey! I think the stone is loose in my cell! I might escape..', "Hmm, that's odd, I remember checking the camera earlier.. I guess there's no harm in checking again!"],
    ID.chamonix: ['Have you seen a young girl being led by two Groboclones?', "I haven't seen them.. ", "Here's something strange: I found a page torn out of a book which said, 'pull the middle lever once first then pull the right lever once.' Must be some kind of puzzle.", "I'm really enjoying a book about all kinds of wonders, one of them being a Clear Water Lake in the Himalayi mountains!"],
    ID.agen: ["Did you know Dr. Funfrock installed his busts to protect and defend us? The ones that don't have pedestals are covering ancient undestructible seals that could put the entire system of governance in danger!"],
    ID.brenne: ["I've heard you fought some soldiers and clones, I guess I can trust you.. You should see my brother on the Proxima Island, I know that he made a fake red card. Just tell him the word 'Amos'. He lives in a red house, it's hard to miss."],

    ID.trier: ["Hi, are you the Brenne's brother?", "Yes", "I have a message for you, it's 'AMOS'.", "You don't have to shout, but that sounds right.", "Is there anything you would like from me?", "Yes, Brenne mentioned the Red Card.", "Ah, so you are curious about all the secret places and nice things hidden therein? Well some things may be not so nice, but I'm sure you'll take it in stride, and get out getting out's what's doc ordered! Here I am, blabbering like an old senile NPC while I'm sure you have quests to finish, to prove your mettle. Here you have it, the red card, good as new! Except it shouldn't look new, that would be suspicious, so I've aged it a bit."],

    ID.morvan: ["Hi, have you seen my friend being led by two Groboclones?", "No, but I'm not surprised at all. And I can only guess what will happen to me. What's the worst that can happen?",
                "<he almost seems to break down and is close to weeping but regains control>", "What will happen to you.. I wish I could tell you.. <his voice trails off>"],

    ID.morvan2: ["They will stalk my home first, just like a Grobo is already menacing Montbard's house."],

    ID.montbard: ["Thanks for for ridding me of this meddlesome.. <he shakes with anger and fear> .. meddlesome .. monster!",
                  "I don't know how I can ever repay you. If there's anything you want..",
                  "Yes, can you show me the path to the Astronomer's home?", "Just use the sink in the house with the flower on the roof",
                  "What?", "Don't worry about a thing, just do that and you will find the Astronomer.."
                 ],

    ID.agen2: ["Do you know anything interesting about any of the regulars here at the library?",
               "Not much, we are all boring folk! We read immersive fictional stories and try to imagine we are in the place of the here of the story, and then the dangers and triumphs of the story can make your heart beat so fast! But outside of books, all we do is but complain of petty small things, like Clermont and his water.."],

    ID.clermont_ferrand: ["I wish I was at Clear Water Lake, the lake water is so sweet. Why does our tap water have to taste so metallic? Even Citadel Island water is more palatable!",
                          "Ah, don't I know it! And I have no choice but drink tap water from this fountain!", "Why is that?",
                          "I wish I never went to my doctor - he is the one who told me I have to drink tap water!",
                          "If there's anything anyone could do, I would sure be very grateful!!"],

    ID.clermont_ferrand2: ['Let me try the water first...'],

    ID.clermont_ferrand3: ['Fantastic! It tastes like raspberries! I would have preferred a carrot flavor, but a promise is a promise.. follow me..'],

    ID.locksmith: ['Ahh! You know the secret passage! I know I can trust you...', 'I would like to see the Astronomer',
                   'Very well, I will open the door for you.'],

    ID.astronomer: ['Have you..', "I know that you are looking for your friend, but I haven't seen her. It's very odd that she was taken from Citadel island",
                    'I feel that Dr. Funfrock is afraid of something related to the Legend. If you find out what it is, you may be able to help your friend.', 'Go to port Beluga, and talk to my dear friend Maurice, he will help you get off the island.'
                   ],

    ID.legend1: ['The secret of the Prophecy, which is now often called simply The Legend, can be found somewhere in the White Leaf Desert.'],

    ID.olivet: ['Can you tell me anything about the Legend?', 'Yes, I do know some details that may interest you.. but I can only tell you in exchange for the book of knowledge that I am sorely missing. You can find the book of knowledge in the Temple of Bu. The entrance is right here....'],

    ID.olivet2: ['I now see that you are the chosen one. You can keep the Book of Bu. It will let you decipher runes and speak to the animals.', 'I do not know how you can defeat Dr. FunFrock, but I know that you must. I wish I could help you.', 'Something tells me your parents must have left a clue or a direction at your home to help you along. Perhaps it is a good time to return home.'],
}

def mkcell():
    return [blank]

def mkrow():
    return [mkcell() for _ in range(79)]


class Loc:
    def __init__(self, x, y):
        self.y, self.x = y, x

    def __iter__(self):
        yield self.x
        yield self.y

    def __getitem__(self, i):
        return (self.x, self.y)[i]

    def __repr__(self):
        return str((self.x, self.y))

    def __eq__(self, l):
        if isinstance(l, Loc):
            return (self.x, self.y) == (l.x, l.y)

    def mod(self, y, x):
        new = copy(self)
        new.y += y
        new.x += x
        return new

    def mod_r(self):
        return self.mod(0, 1)

    def mod_l(self):
        return self.mod(0, -1)

    def mod_d(self):
        return self.mod(1, 0)

    def mod_u(self):
        return self.mod(-1, 0)


class Board:
    def __init__(self, loc, _map):
        self.B = [mkrow() for _ in range(HEIGHT)]
        self.guards = []
        self.soldiers = []
        self.labels = []
        self.doors = []
        self.spawn_locations = {}
        self.trigger_locations = {}
        self.colors = []
        self.labels = []
        self.misc = []
        self.loc = loc
        self._map = _map
        self.state = 0
        map_to_loc[str(_map)] = loc, self

    def __repr__(self):
        return f'<B: {self._map}'

    def board_1(self):
        containers, crates, doors, specials = self.load_map(self._map)
        containers[3].add1(ID.key1)
        Item(self, Blocks.platform, 'mobile platform', specials[1], id=ID.platform1)
        g = Guard(self, specials[1], id=ID.guard1)
        self.guards = [g]
        Item(self, Blocks.grill, 'grill', specials[2], id=ID.grill1)
        p = Player(self, specials[3], id=ID.player)
        return p

    def board_2(self):
        """Technician, alarm."""
        containers, crates, doors, specials = self.load_map(self._map)
        Technician(self, specials[1], id=ID.technician1)
        Item(self, Blocks.bell, 'alarm bell', specials[2], id=ID.alarm1)
        doors[0].id = ID.door1

    def board_3(self):
        """Soldier, rubbish heap."""
        containers, crates, doors, specials = self.load_map(self._map)
        RoboBunny(self, specials[1], id=ID.robobunny1)
        Item(self, Blocks.grill, 'grill', specials[2], id=ID.grill2)
        s = Soldier(self, specials[3], id=ID.soldier1)
        self.soldiers.append(s)

    def board_4(self):
        self.labels.append((0,20, "𝓪𝓫𝓮 𝓸𝓵𝓭 𝓼𝓱𝓸𝓹𝓹𝓮"))    # Abe old shoppe
        containers, crates, doors, specials = self.load_map(self._map)
        Item(self, Blocks.platform_top, 'platform', specials[Blocks.platform_top], id=ID.platform_top1, type=Type.platform_top)
        ShopKeeper(self, specials[1], name='Abe', id=ID.shopkeeper1)
        jar = Item(None, Blocks.bottle, 'bottle of raspberry syrup', None, id=ID.jar_syrup)
        containers[3].inv[jar] = 1

    def board_5(self):
        self.labels.append((2,20, "𝓐𝓷𝓽𝓱𝓸𝓷𝔂 𝓫𝓪𝓻"))
        containers, crates, doors, specials = self.load_map(self._map)
        containers[2].add1(ID.key1)
        Grobo(self, specials[1], id=ID.max_, name='Max')
        RoboBunny(self, specials[2], id=ID.anthony, name='Anthony')

    def board_6(self):
        self.labels.append((2,20, "𝒯𝓌𝒾𝓃𝓈𝑒𝓃 𝐻𝑜𝓂𝑒"))
        containers, crates, doors, specials = self.load_map(self._map)
        mball = Item(None, Blocks.magic_ball, 'magic ball', None, id=ID.magic_ball)
        containers[0].inv[mball] = 1
        containers[0].add1(ID.key1)
        crates[5].id = ID.crate1
        TriggerEventLocation(self, specials[1], evt=MaxState1)
        Item(self, Blocks.grill, 'grill', specials[2], id=ID.grill4)

    def board_7(self):
        self.labels.append((10,5, "𝒯𝒽𝑒 𝐹𝑒𝓇𝓇𝓎"))
        containers, crates, doors, specials = self.load_map(self._map)
        julien, clone1 = specials[Blocks.elephant]
        key3 = Item(self, Blocks.key, 'key', id=ID.key3, put=0)
        clone1.inv[key3] = 1
        julien.id = ID.julien
        objects[julien.id] = julien
        doors[0].type = Type.door3
        Item(self, Blocks.grill, 'grill', specials[1], id=ID.grill4)
        Item(self, Blocks.ticket_seller, 'Ticket seller booth', specials[2], id=ID.ticket_seller1)
        # invisible, with ferry id to be able to take the ferry near this tile
        Item(self, '', '', specials[3], id=ID.ferry)

    def board_8(self):
        containers, crates, doors, specials = self.load_map(self._map)
        Item(self, Blocks.grill, 'grill', specials[1], id=ID.grill5)
        Item(self, Blocks.grill, 'grill', specials[2], id=ID.grill6)
        Item(self, Blocks.bars, 'jail bars', specials[5], id=ID.bars1, type=Type.blocking)
        Item(self, '', '', specials[8], id=ID.trick_guard)
        TriggerEventLocation(self, specials[7], evt=JailEvent)
        s = Soldier(self, specials[3], id=ID.soldier2)
        self.guards.append(s)
        self.spawn_locations[4] = specials[4]
        self.spawn_locations[6] = specials[6]
        self.spawn_locations[8] = specials[8]

    def board_9(self):
        # trees map
        self.load_map(self._map)

    def board_10(self):
        """Library"""
        containers, crates, doors, specials = self.load_map(self._map)
        Grobo(self, specials[1], id=ID.wally, name='Wally')
        RoboBunny(self, specials[2], id=ID.chamonix, name='Mr. Chamonix')
        Being(self, specials[3], id=ID.agen, name='Agen', char=Blocks.monkey)
        Being(self, specials[4], id=ID.clermont_ferrand, name='Clermont-Ferrand', char=Blocks.monkey)
        Item(self, Blocks.open_book, 'book', specials[5], id=ID.legend1)
        doors[0].type = Type.door3

    def board_11(self):
        self.load_map(self._map)

    def board_12(self):
        self.labels.append((3,47, "𝒯𝒽𝑒 𝒞𝒾𝓉𝒶𝒹𝑒𝓁"))
        specials = self.load_map(self._map)[3]
        RoboBunny(self, specials[1], id=ID.brenne, name='Brenne')
        Item(self, '', '', specials[1].mod(0,-2), id=ID.talk_to_brenne)

    def board_top1(self):
        self.labels.append((0,2, "𝒜𝓈𝓉𝓇𝑜𝓃𝑜𝓂𝑒𝓇"))
        self.labels.append((0,20, "𝐿𝑜𝒸𝓀𝓈𝓂𝒾𝓉𝒽"))
        containers, crates, doors, specials = self.load_map(self._map)
        doors[1].type = Type.door3

        Being(self, specials[1], id=ID.montbard, name='Montbard', char=Blocks.monkey)
        Being(self, specials[2], id=ID.morvan, name='du Morvan', char=Blocks.monkey)
        Being(self, specials[3], id=ID.astronomer, name='The Astronomer', char=Blocks.monkey)
        Being(self, specials[4], id=ID.groboclone1, name='Groboclone', char=Blocks.elephant)
        Being(self, specials[7], id=ID.locksmith, name='Locksmith', char=Blocks.elephant)
        Being(self, specials[9], id=ID.aubigny, name='Aubigny', char=Blocks.rabbit)

        Item(self, Blocks.fountain, 'sink', specials[5], id=ID.sink)
        Item(self, Blocks.hexagon, 'A Drawing with a romantic view and a horse galloping at full speed across the plain', specials[6], id=ID.drawing)
        Item(self, Blocks.grill, 'grill', specials[8], id=ID.grill7)

    def board_top2(self): self.load_map(self._map)

    def board_top3(self):
        self.colors = [(Loc(50,11), 1)]     # window
        containers, crates, doors, specials = self.load_map(self._map)
        Item(self, Blocks.car, 'Car', specials[1], id=ID.car)

    def board_beluga(self):
        self.colors = [(Loc(41,6), 1)]     # window
        containers, crates, doors, specials = self.load_map(self._map)
        Item(self, Blocks.ferry, 'Sailboat', specials[1], id=ID.sailboat)

    # -- White Leaf Desert --------------------------------------------------------------------------

    def board_desert1(self):
        lrange = lambda *x: list(range(*x))
        for x in [8,15] + lrange(23,27) + lrange(35,79):
            self.colors.append((Loc(x,GROUND+1), 2))
        containers, crates, doors, specials = self.load_map(self._map)
        Item(self, Blocks.ferry, 'Sailboat', specials[1], id=ID.sailboat)

    def board_desert2(self):
        lrange = lambda *x: list(range(*x))
        for x in [8,15] + lrange(23,27) + lrange(35,60):
            self.colors.append((Loc(x,GROUND+1), 2))
        specials = self.load_map(self._map)[3]
        Being(self, specials[1], id=ID.olivet, name='Olivet', char=Blocks.rabbit)

    def board_des_und(self):
        containers, crates, doors, specials = self.load_map(self._map)
        doors[0].type = Type.door3
        doors[1].type = Type.door3

        Item(self, Blocks.lever, 'lever', specials[1], id=ID.lever1)
        Item(self, Blocks.lever, 'lever', specials[2], id=ID.lever2)
        Item(self, Blocks.statue, 'statue', specials[3], id=ID.statue)
        Item(self, Blocks.platform_top, 'platform', specials[4], id=ID.platform3, type=Type.blocking)

    def board_des_und2(self):
        containers, crates, doors, specials = self.load_map(self._map)
        Item(self, Blocks.lever, 'lever', specials[1], id=ID.lever3)
        Item(self, Blocks.lever, 'lever', specials[2], id=ID.lever4)
        Item(self, Blocks.lever, 'lever', specials[3], id=ID.lever5)

        Item(self, Blocks.platform_top, 'platform', specials[4], id=ID.platform4, type=Type.blocking)
        Item(self, Blocks.platform_top, 'platform', specials[5], id=ID.platform5, type=Type.blocking)
        Item(self, Blocks.platform_top, 'platform', specials[6], id=ID.platform6, type=Type.blocking)
        Item(self, Blocks.open_book, 'Book of Bu', specials[7], id=ID.book_of_bu)
        TriggerEventLocation(self, specials[8], evt=LeaveBu)

    # -----------------------------------------------------------------------------------------------
    def board_und1(self):
        containers, crates, doors, specials = self.load_map(self._map)
        Item(self, Blocks.grill, 'grill', specials[1], id=ID.grill3)

    def board_sea1(self):
        specials = self.load_map(self._map)[3]
        Item(self, Blocks.ferry, 'ferry', specials[1], id=ID.ferry)

    def board_landscape1(self):
        self.load_map(self._map)

    def board_wtower(self):
        specials = self.load_map(self._map)[3]
        for loc in self.locs_rectangle(Loc(32,13), Loc(37,14)):
            self.colors.append((loc,1))
        Item(self, '', '', specials[1], id=ID.water_supply)

    def load_map(self, map_num, for_editor=0):
        _map = open(f'maps/{map_num}.map').readlines()
        crates = []
        containers = []
        self.doors = doors = []
        self.specials = specials = defaultdict(list)
        BL=Blocks

        for y in range(16):
            for x in range(79):
                char = _map[y][x]
                loc = Loc(x,y)
                if char != blank:
                    if char==rock:
                        self.put(rock, loc)
                    elif char==Blocks.ladder:
                        Item(self, Blocks.ladder, 'ladder', loc, type=Type.ladder)

                    elif char==Blocks.door:
                        d = Item(self, Blocks.door, 'door', loc, type=Type.door1)
                        doors.append(d)

                    elif char=='D':
                        d = Item(self, Blocks.door, 'steel door', loc, type=Type.door2)
                        doors.append(d)

                    elif char=='g':
                        Item(self, Blocks.grn_heart, 'grn_heart', loc, id=ID.grn_heart)

                    elif char==Blocks.locker or char=='o':
                        l = Locker(self, loc)
                        containers.append(l)

                    elif char==Blocks.cupboard or char=='c':
                        c = Cupboard(self, loc)
                        containers.append(c)

                    elif char in Blocks.crates or char=='C':
                        c = Item(self, choice(Blocks.crates), 'crate', loc)
                        crates.append(c)

                    elif char=='s':
                        Item(self, Blocks.sunflower, 'sunflower', loc)

                    elif char==Blocks.sharp_rock:
                        Item(self, Blocks.sharp_rock, 'sharp_rock', loc, type=Type.deadly)

                    elif char==Blocks.rock3:
                        Item(self, Blocks.rock3, 'rock', loc, type=Type.blocking)

                    elif char==Blocks.block1:
                        Item(self, Blocks.block1, 'block', loc, type=Type.door_top_block)

                    elif char==Blocks.smoke_pipe:
                        Item(self, Blocks.smoke_pipe, 'smoke pipe', loc, type=Type.ladder)

                    elif char==Blocks.cactus:
                        Item(self, Blocks.cactus, 'cactus', loc)

                    elif char==Blocks.fireplace:
                        Item(self, Blocks.fireplace, 'fireplace', loc)

                    elif char==Blocks.water:
                        Item(self, Blocks.water, 'water', loc, type=Type.water)

                    elif char==Blocks.stool:
                        Item(self, Blocks.stool, 'bar stool', loc)

                    elif char==Blocks.tulip:
                        Item(self, Blocks.tulip, 'tulip', loc)

                    elif char==Blocks.antitank:
                        Item(self, Blocks.antitank, 'antitank hedgehog obstacle', loc)

                    elif char==Blocks.fountain:
                        Item(self, Blocks.fountain, 'water fountain basin', loc)

                    elif char==Blocks.dock_boards:
                        Item(self, Blocks.dock_boards, 'dock boards', loc, type=Type.blocking)

                    elif char==Blocks.grill:
                        Item(self, Blocks.grill, 'barred window', loc)

                    elif char==Blocks.rubbish:
                        Item(self, Blocks.rubbish, 'rubbish', loc, id=ID.rubbish1)

                    elif char in (BL.books, BL.open_book):
                        Item(self, char, 'books', loc)

                    elif char in (Blocks.tree1, Blocks.tree2):
                        Item(self, char, 'tree', loc)

                    elif char in (BL.guardrail_l, BL.guardrail_r, BL.guardrail_m):
                        Item(self, char, 'guardrail', loc)

                    elif char==Blocks.shelves:
                        s = Item(self, Blocks.shelves, 'shelves', loc, type=Type.container)
                        containers.append(s)

                    elif char==Blocks.ferry:
                        Item(self, Blocks.ferry, 'ferry', loc, id=ID.ferry)

                    elif char==Blocks.bars:
                        Item(self, Blocks.bars, 'jail bars', loc, type=Type.blocking)

                    elif char in (BL.angled1, BL.angled2):
                        Item(self, char, '', loc, type=Type.blocking)

                    elif char==Blocks.angled1:
                        Item(self, Blocks.angled1, '', loc, type=Type.blocking)

                    elif char==Blocks.rock2:
                        Item(self, char, '', loc)

                    elif char==Blocks.platform_top:
                        specials[Blocks.platform_top] = loc
                        if for_editor:
                            self.put(Blocks.platform_top, loc)

                    elif char==Blocks.steps_l:
                        self.put(Blocks.steps_l, loc)

                    elif char==Blocks.platform2:
                        Item(self, Blocks.platform2, '', loc, type=Type.blocking)

                    elif char==Blocks.steps_r:
                        self.put(Blocks.steps_r, loc)

                    elif char==Blocks.elephant:
                        g = Grobo(self, loc)
                        specials[Blocks.elephant].append(g)

                    elif char==Blocks.soldier:
                        s = Soldier(self, loc)
                        self.soldiers.append(s)

                    elif char in '0123456789':
                        specials[int(char)] = loc
                        if for_editor:
                            self.put(char, loc)
        return containers, crates, doors, specials

    def make_steps(self, start, mod, to_height, char=Blocks.steps_r):
        n = start.y - to_height
        newx = None
        for x in range(n):
            row = self.B[start.y-x]
            newx = start.x+(mod*x)
            row[newx].append(char)
        return Loc(newx, n+2)

    def locs_rectangle(self, a, b):
        for y in range(a.y, b.y+1):
            for x in range(a.x, b.x+1):
                yield Loc(x,y)

    def rectangle(self, a, b, exc=None):
        row = self.B[a.y]
        for cell in row[a.x:b.x+1]:
            cell.append(rock)
        row = self.B[b.y]
        for cell in row[a.x:b.x+1]:
            cell.append(rock)
        for y in range(a.y+1, b.y):
            self.put(rock, Loc(a.x, y))
        for y in range(a.y+1, b.y):
            self.put(rock, Loc(b.x, y))
        exc = exc or []
        for loc in exc:
            self.remove(rock, loc)

    def __getitem__(self, loc):
        return self.B[loc.y][loc.x][-1]

    def __iter__(self):
        for y, row in enumerate(self.B):
            for x, cell in enumerate(row):
                yield Loc(x,y), cell

    def get_all(self, loc):
        return [n for n in self.B[loc.y][loc.x] if n!=blank]

    def get_all_obj(self, loc):
        return [n for n in self.B[loc.y][loc.x] if not isinstance(n, str)]

    def get_top_obj(self, loc):
        return last(self.get_all_obj(loc))

    def get_ids(self, loc):
        if isinstance(loc, Loc):
            loc = [loc]
        lst = []
        for l in loc:
            lst.extend(ids(self.get_all(l)))
        return lst

    def get_types(self, loc):
        return types(self.get_all(loc))

    def draw(self, win):
        for y, row in enumerate(self.B):
            for x, cell in enumerate(row):
                # tricky bug: if an 'invisible' item put somewhere, then a being moves on top of it, it's drawn, but
                # when it's moved out, the invisible item is drawn, but being an empty string, it doesn't draw over the
                # being's char, so the 'image' of the being remains there, even after being moved away.
                cell = [c for c in cell if str(c)]
                win.addstr(y,x, str(last(cell)))
        for y,x,txt in self.labels:
            win.addstr(y,x,txt)
        for loc, col in self.colors:
            win.addstr(loc.y, loc.x, str(self[loc]), curses.color_pair(col))
        win.refresh()
        if Windows.win2:
            Windows.win2.addstr(0,74, str(self._map))

    def put(self, obj, loc=None):
        loc = loc or obj.loc
        if not isinstance(obj,str):
            obj.B = self
            obj.loc = loc
        try: self.B[loc.y][loc.x].append(obj)
        except Exception as e:
            sys.stdout.write(str(loc))
            raise

    def remove(self, obj, loc=None):
        loc = loc or obj.loc
        self.B[loc.y][loc.x].remove(obj)

    def is_blocked(self, loc):
        for x in self.get_all(loc):
            if x in BLOCKING or getattr(x, 'type', None) in BLOCKING:
                return True
        return False

    def is_being(self, loc):
        for x in self.get_all(loc):
            if getattr(x, 'is_being', 0):
                return x
        return False

    def avail(self, loc):
        return not self.is_blocked(loc)

    def display(self, txt):
        w = max(len(l) for l in txt) + 1
        win = newwin(len(txt)+2, w+2, 5, 5)
        for y, ln in enumerate(txt):
            win.addstr(y+1,0, ' ' + ln)
        win.getkey()
        del win

def chk_oob(loc, y=0, x=0):
    return 0 <= loc.y+y <= HEIGHT-1 and 0 <= loc.x+x <= 78

def chk_b_oob(loc, y=0, x=0):
    h = len(boards)
    w = len(boards[1])
    newx, newy = loc.x+x, loc.y+y
    return 0 <= newy <= h-1 and 0 <= newx <= w-1 and boards[newy][newx]

def ids(lst):
    return [x.id for x in lst if not isinstance(x, str)]

def types(lst):
    return [x.type for x in lst if not isinstance(x, str)]


class Mixin1:
    is_player = 0

    def tele(self, loc):
        self.B.remove(self)
        self.put(loc)

    def put(self, loc):
        self.loc = loc
        self.B.put(self)
        if self.is_player and ID.platform1 in self.B.get_ids(loc):
            triggered_events.append(PlatformEvent1)

    def has(self, id):
        return self.inv[objects[id]]

    def remove1(self, id):
        self.inv[objects[id]] -= 1

    def add1(self, id):
        self.inv[objects[id]] += 1


class Item(Mixin1):
    state = 0
    def __init__(self, B, char, name, loc=None, put=True, id=None, type=None):
        self.B, self.char, self.name, self.loc, self.id, self.type = B, char, name, loc, id, type
        self.inv = defaultdict(int)
        if id:
            objects[id] = self
        if B and put:
            B.put(self)

    def __repr__(self):
        return self.char

    def __hash__(self):
        return self.id

    def move(self, dir):
        m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0))[dir]
        new = self.loc.mod(*m)
        self.B.remove(self)
        self.loc = new
        self.B.put(self)


class TriggerEventLocation(Item):
    """Location that triggers an event."""
    def __init__(self, B, loc, evt, id=None):
        super().__init__(B, '', '', loc, id=id, type=Type.event_trigger)
        self.evt = evt

class Locker(Item):
    def __init__(self, B, loc):
        super().__init__(B, Blocks.locker, 'locker', loc, id=ID.locker, type=Type.container)
        if random()>.6:
            self.add1(ID.coin)
        elif random()>.6:
            self.add1(ID.grn_heart)

class Cupboard(Item):
    def __init__(self, B, loc):
        super().__init__(B, Blocks.cupboard, 'cupboard', loc, type=Type.container)
        # ugly: this doesn't work in the map editor because `objects` dict doesn't have these items
        try:
            if random()>.5:
                self.add1(ID.coin)
            elif random()>.7:
                self.add1(ID.grn_heart)
        except: pass

class MagicBall(Item):
    def __init__(self, B, loc):
        super().__init__(B, Blocks.magic_ball, 'magic_ball', loc, id=ID.magic_ball)

class Being(Mixin1):
    stance = Stance.normal
    health = None
    is_being = 1
    is_player = 0
    hostile = 0
    type = None
    char = None

    def __init__(self, B, loc=None, put=True, id=None, name=None, state=0, hostile=False, health=None, char='?'):
        self.B, self.id, self.loc, self.name, self.state, self.hostile  = \
                B, id, loc, name, state, hostile

        self.health = self.health or health or 5
        self.char = self.char or char
        self.inv = defaultdict(int)
        if Misc.is_game: # not editor
            self.add1(ID.key1)
            self.inv[objects[ID.fuel]] = 10
        j=Item(None, Blocks.bottle, 'jar of syrup', None, id=ID.jar_syrup)
        self.inv[j] = 1
        self.kashes = 54
        if id:
            objects[id] = self
        if put:
            B.put(self)

    def __str__(self):
        return self.char

    def move_to_board(self, b_loc, loc, B=None):
        if self in self.B.get_all(self.loc):
            self.B.remove(self)
        B = B or boards[b_loc.y][b_loc.x]
        self.loc = loc
        B.put(self)
        self.B = B

        # update references in `objects` in case there was a game load from a save
        for loc, cell in B:
            for obj in B.get_all_obj(loc):
                if obj.id in objects:
                    objects[obj.id] = obj
        return B

    @property
    def fight_stance(self):
        return self.stance==Stance.fight

    @property
    def sneaky_stance(self):
        return self.stance==Stance.sneaky

    def talk(self, being, dialog=None, yesno=False):
        being = objects.get(being) or being
        loc = being.loc
        if isinstance(dialog, str):
            dialog = [dialog]
        dialog = dialog or conversations[being.id]
        x = min(loc.x, 60)
        multichoice = 0
        for txt in dialog:
            lst = []
            if isinstance(txt, (list,tuple)):
                multichoice = len(txt)
                for n, t in enumerate(txt):
                    lst.append(f'{n+1}) {t}')
                txt = '\n'.join(lst)
            x = min(40, x)
            w = 78 - x
            lines = (len(txt) // w) + 4
            txt = wrap(txt, w)
            txt = '\n'.join(txt)
            offset_y = lines if loc.y<8 else -lines

            y = max(0, loc.y+offset_y)
            win = newwin(lines+2, w+2, y, x)
            win.addstr(1,1, txt + (' [Y/N]' if yesno else ''))
            if yesno:
                # TODO in some one-time dialogs, may need to detect 'no' explicitly
                k = win.getkey()
                del win
                return k in 'Yy'
            elif multichoice:
                for _ in range(2):
                    k = win.getkey()
                    try:
                        k=int(k)
                    except ValueError:
                        k = 0
                    if k in range(1, multichoice+1):
                        del win
                        return k
            win.getkey()
            del win
            self.B.draw(Windows.win)
            Windows.win2.clear()
            Windows.win2.refresh()

    def _move(self, dir, fly=False):
        m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0))[dir]
        if chk_oob(self.loc, *m):
            return True, self.loc.mod(*m)
        else:
            if self.is_player and chk_b_oob(self.B.loc, *m):
                return LOAD_BOARD, self.B.loc.mod(*m)
        return 0, 0

    def move(self, dir, fly=False):
        B = self.B
        rv = self._move(dir, fly)
        if rv and (rv[0] == LOAD_BOARD):
            return rv
        new = rv[1]
        if new and isinstance(B[new], Being):
            being = B[new]
            if self.fight_stance or self.hostile:
                self.attack(being)
            elif being.id == ID.robobunny1:
                self.talk(being)
            else:
                self.switch_places()    # TODO support direction
            return True, True

        # TODO This is a little messy, doors are by type and keys are by ID
        if new and Type.door1 in B.get_types(new) and self.has(ID.key1):
            d = B[new]
            if d.id == ID.door1:
                triggered_events.append(AlarmEvent1)
            B.remove(B[new])    # TODO will not work if something is on top of door
            self.remove1(ID.key1)
            Windows.win2.addstr(2,0, 'You open the door with your key')
            return None, None

        if new and Type.door3 in B.get_types(new) and self.has(ID.key3):
            B.remove(B[new])    # TODO will not work if something is on top of door
            self.remove1(ID.key3)
            Windows.win2.addstr(2,0, 'You open the door with your key')
            return None, None

        if new and B.is_blocked(new):
            new = new.mod(-1,0)
            if B.is_blocked(new):
                new = None
                if self.fight_stance:
                    Windows.win2.addstr(1, 0, 'BANG')
                    triggered_events.append(GuardAttackEvent1)

        if new:
            statue = objects.get(ID.statue)
            if ID.grill5 in B.get_ids(new):
                new = new.mod(0,-3)
                Windows.win2.addstr(1, 0, 'You climb through the window covered by a grill and escape to a small nook under the stairs')
            if ID.grill6 in B.get_ids(new):
                SoldierEvent2(B).go()
                return None, None

            if B.loc and B.loc.x==3 and new==Loc(23,8):   # TODO use trigger event location
                triggered_events.append(ShopKeeperEvent1)

            new = self.fall(new)
            if new[0] == LOAD_BOARD or new[0] is None:
                return new
            pick_up = [ID.key1, ID.key2, ID.key3, ID.magic_ball]
            B.remove(self)
            self.loc = new

            if self.is_player:
                top_obj = B.get_top_obj(new)
                items = B.get_all_obj(new)
                if top_obj and top_obj.type == Type.event_trigger:
                    triggered_events.append(top_obj.evt)
                for x in reversed(items):
                    if x.id == ID.coin:
                        self.kashes += 1
                    elif x.id == ID.grn_heart:
                        self.health = min(15, self.health+1)
                        B.remove(x)
                    elif x.id in pick_up:
                        self.inv[x] += 1
                        B.remove(x)
                names = [i.name for i in B.get_all_obj(new) if i.name]
                plural = len(names)>1
                names = ', '.join(names)
                if names:
                    a = ':' if plural else ' a'
                    Windows.win2.addstr(2,0, f'You see{a} {names}')

            # this needs to be after previous block because the block looks at `top_obj` which would always be the being
            # instead of an event trigger item
            self.put(new)
            if statue:
                if statue.state:
                    statue.move(dir)
                if statue.loc == B.specials[6]:
                    triggered_events.append(StatueInPlace)

            grills = set((ID.grill1, ID.grill2))
            if self.sneaky_stance:
                if (grills & set(B.get_ids(self.loc))):
                    triggered_events.append(ClimbThroughGrillEvent1)
                if ID.grill3 in B.get_ids(self.loc):
                    ClimbThroughGrillEvent2.new = new
                    triggered_events.append(ClimbThroughGrillEvent2)
                if ID.grill4 in B.get_ids(self.loc):
                    ClimbThroughGrillEvent3.new = new
                    triggered_events.append(ClimbThroughGrillEvent3)

            Windows.win2.refresh()
            return True, True
        return None, None

    def fall(self, new):
        fly=False
        B=self.B
        objs = [o.type for o in B.get_all_obj(new)]
        if not fly and not Type.ladder in objs:
            new2 = new
            while 1:
                # TODO: these may overdraw non-blocking items; it's an ugly hack but creates a nice fall animation
                # for now
                Windows.win.addstr(self.loc.y, self.loc.x, ' ')
                Windows.win.addstr(new2.y, new2.x, ' ')
                new2 = new2.mod(1,0)
                if chk_oob(new2) is False:
                    self.loc = new
                    return LOAD_BOARD, ID.fall

                if getattr(B[new2], 'type', None) == Type.water:
                    triggered_events.append(DieEvent)
                    Windows.win2.addstr(1, 0, 'You fall into the water and drown...')
                    return None, None

                if getattr(B[new2], 'type', None) == Type.deadly:
                    triggered_events.append(DieEvent)
                    status('You fall down onto sharp rocks and die of sustained wounds...')
                    return None, None

                if chk_oob(new2) and B.avail(new2) and not Type.ladder in B.get_types(new2):
                    # ugly hack for the fall animation
                    Windows.win.addstr(new2.y, new2.x, str(self))
                    sleep(0.05)
                    Windows.win.refresh()
                    new = new2
                else:
                    break
        return new

    def attack(self, obj):
        if abs(self.loc.x - obj.loc.x) <= 1 and \
           abs(self.loc.y - obj.loc.y) <= 1:
                self.hit(obj)
        else:
            if self.loc.x < obj.loc.x:
                self.move('l')
            else:
                self.move('h')

    def hit(self, obj):
        if obj.health:
            obj.health -= 1
            Windows.win2.addstr(1, 0, f'{self} hits {obj} for 1pt')
            if obj.is_being:
                obj.hostile = 1
            if obj.health <=0:
                self.B.remove(obj)
                if random()>0.6:
                    Item(self.B, Blocks.coin, 'one kash', obj.loc, id=ID.coin)
                elif random()>0.6:
                    Item(self.B, Blocks.grn_heart, 'heart', obj.loc, id=ID.grn_heart)
                for it, qty in obj.inv.items():
                    # TODO note item will not have a `loc` (ok for now)
                    it.loc = obj.loc
                    self.B.put(it, obj.loc)

    def switch_places(self):
        B = self.B
        r,l = self.loc.mod_r(), self.loc.mod_l()
        ro = lo = None
        if chk_oob(r): ro = B[r]
        if chk_oob(l): lo = B[l]

        if isinstance(ro, Being):
            B.remove(ro)
            B.remove(self)
            loc = self.loc
            self.put(r)
            ro.put(loc)
            Windows.win2.addstr(1, 0, f'{self} moved past {ro.name}')
        elif isinstance(lo, Being):
            B.remove(lo)
            B.remove(self)
            loc = self.loc
            self.put(l)
            lo.put(loc)
            Windows.win2.addstr(1, 0, f'{self} moved past {lo}')

    def action(self):
        B=self.B
        c = last( [x for x in B.get_all(self.loc) if x.type==Type.container] )
        objs = B.get_all_obj(self.loc)

        r,l = self.loc.mod_r(), self.loc.mod_l()
        rd, ld = r.mod_d(), l.mod_d()
        locs = [self.loc]
        morvan = objects.get(ID.morvan)
        montbard = objects.get(ID.montbard)
        locksmith = objects.get(ID.locksmith)
        maurice = objects.get(ID.maurice)
        clermont_ferrand = objects.get(ID.clermont_ferrand)
        aubigny = objects.get(ID.aubigny)
        olivet = objects.get(ID.olivet)
        statue = objects.get(ID.statue)
        lever3 = objects.get(ID.lever3)
        lever4 = objects.get(ID.lever4)
        lever5 = objects.get(ID.lever5)
        platform4 = objects.get(ID.platform4)
        platform5 = objects.get(ID.platform5)
        platform6 = objects.get(ID.platform6)
        book_of_bu = objects.get(ID.book_of_bu)

        if chk_oob(r): locs.append(r)
        if chk_oob(l): locs.append(l)
        if chk_oob(rd): locs.append(rd)
        if chk_oob(ld): locs.append(ld)

        def is_near(id):
            return getattr(ID, id) in B.get_ids(locs)

        if c:
            items = {k:v for k,v in c.inv.items() if v}
            lst = []
            for x in items:
                if x.id==ID.coin:
                    self.kashes+=1
                else:
                    self.inv[x] += c.inv[x]
                c.inv[x] = 0
                lst.append(str(x))
            Windows.win2.addstr(2,0, 'You found {}'.format(', '.join(lst)))
            if not items:
                Windows.win2.addstr(2,0, f'{c.name} is empty')
        elif len(objs)>1 and objs[-2].id == ID.crate1:
            objs[-2].move('l')
            Item(B, Blocks.grill, 'grill', self.loc, id=ID.grill3)

        elif ID.anthony in B.get_ids(locs):
            BuyADrinkAnthony(B).go()

        elif ID.trick_guard in B.get_ids(locs):
            self.talk(objects[ID.guard2])
            B.remove(objects[ID.bars1])
            objects[ID.guard2].move('l')

        elif ID.talk_to_brenne in B.get_ids(locs):
            self.talk(objects[ID.brenne])

        elif ID.max_ in B.get_ids(locs):
            MaxQuest().go(self)

        elif ID.chamonix in B.get_ids(locs):
            self.talk(objects[ID.chamonix])

        elif is_near('clermont_ferrand') and clermont_ferrand.state==1:
            self.talk(objects[ID.clermont_ferrand])

        elif is_near('clermont_ferrand') and clermont_ferrand.state==2:
            self.talk(objects[ID.clermont_ferrand])
            triggered_events.append(ClermontTriesWater)
            clermont_ferrand.state = 3

        elif ID.morvan in B.get_ids(locs) and morvan.state==0:
            self.talk(morvan)
            morvan.state = 1
        elif ID.morvan in B.get_ids(locs) and morvan.state==1:
            self.talk(morvan, conversations[ID.morvan2])

        elif ID.montbard in B.get_ids(locs) and objects[ID.groboclone1].dead:
            self.talk(montbard)
            montbard.state = 1  # allow sink to be used

        elif ID.locksmith in B.get_ids(locs) and locksmith.state==1:
            self.talk(locksmith)
            B.remove(B.doors[1])

        elif ID.grill8 in B.get_ids(locs):
            self.tele(objects[ID.grill7].loc)
            Windows.win2.addstr(2,0, "You use the secret passage and find yourself in the locksmith's house")
            locksmith.state = 1

        elif ID.sink in B.get_ids(locs) and montbard.state==1:
            dr = objects[ID.drawing]
            loc = dr.loc
            dr.move('h')
            Item(B, Blocks.grill, 'grill', loc, id=ID.grill8)

        elif ID.astronomer in B.get_ids(locs):
            self.talk(ID.astronomer)
            maurice.state = 1

        elif is_near('legend1'):
            self.talk(self, conversations[ID.legend1])

        elif is_near('sailboat'):
            dests = [('White Leaf Desert', 'desert1'), ('Port Beluga', 'beluga')]
            dest = dests[0] if B._map == 'beluga' else dests[1]
            y = self.talk(self, f'Would you like to use the sailboat for 10 kashes, to go to {dest[0]}?', yesno=1)
            if y:
                if self.kashes>=10:
                    self.kashes-=10
                    triggered_events.append((TravelBySailboat, dict(dest=dest[1])))
                else:
                    status("Looks like you don't have enough kashes!")

        elif is_near('aubigny'):
            y = self.talk(aubigny, 'Would you like to buy some fuel for 5 kashes?', yesno=1)
            if y:
                if self.kashes>=5:
                    self.inv[objects[ID.fuel]] += 5
                    self.kashes -= 5
                else:
                    status("Looks like you don't have enough kashes!")

        elif is_near('olivet'):
            self.talk(olivet, conversations[ID.olivet2 if self.inv[book_of_bu] else ID.olivet])

        elif is_near('book_of_bu'):
            self.inv[book_of_bu] = 1
            B.remove(book_of_bu)
            status('You have found the Book of Bu.')
            # status('You have found the Book of Bu. It gives you the power to decipher the runes and speak to the animals.')

        elif is_near('lever1'):
            B.remove(B.doors[1])

        elif is_near('lever2'):
            triggered_events.append(MovePlatform3Event)

        elif is_near('lever3'):
            if lever3.state==0 and lever5.state==0 and lever4.state==1:
                dir = 'k' if platform6.loc.y>5 else 'j'
                platform4.move(dir)
                platform6.move(dir)
                platform6.move(dir)
                platform6.move(dir)

        elif is_near('lever4'):
            if lever3.state==0 and lever5.state==0 and lever4.state==0:
                lever4.state = 1
                dir = 'k' if platform5.loc.y>5 else 'j'
                platform5.move(dir)
                platform5.move(dir)

        elif is_near('lever5'):
            dir = 'k' if platform4.loc.y>5 else 'j'
            platform4.move(dir)
            platform4.move(dir)
            lever4.state=1

        elif is_near('statue'):
            if not statue.state:
                status('You prepare to move the statue')
            else:
                status('You leave the statue in place')
            statue.state = not statue.state

        elif is_near('car'):
            # if maurice and maurice.state == 1:
            if 1:     # TODO use the commented line above
                if B._map == 'top3':
                    choices = ['Water Tower', 'Port Beluga']
                elif B._map == 'wtower':
                    choices = ['Old town', 'Port Beluga']
                elif B._map == 'beluga':
                    choices = ['Old town', 'Water Tower']
            else:
                if B._map == 'top3': choices = ['Water Tower']
                elif B._map == 'wtower': choices = ['Old town']
            ch = self.talk(ID.car, ['Where would you like to go?', choices])
            if ch:
                ch = choices[ch-1]
                desc_to_map = {'Water Tower': 'wtower', 'Port Beluga': 'beluga', 'Old town': 'top3'}
                ch = desc_to_map[ch]
                if self.has(ID.fuel):
                    triggered_events.append((TravelByCarEvent, dict(dest=ch)))
                    self.remove1(ID.fuel)
                else:
                    status("It looks like you don't have any petrol!")

        elif ID.agen in B.get_ids(locs):
            agen = objects[ID.agen]
            if agen.state == 0:
                self.talk(objects[ID.agen])
                agen.state = 1
            elif agen.state == 1:
                self.talk(objects[ID.agen], conversations[ID.agen2])
                objects[ID.clermont_ferrand].state = 1

        elif ID.ticket_seller1 in B.get_ids(locs):
            seller = objects[ID.ticket_seller1]
            y = self.talk(seller, 'Would you like to buy a ferry ticket?', yesno=1)
            if y:
                self.talk(seller, 'Here is your ticket... Wait a second... Alarm! The prisoner escaped!!')
                c = Clone(B, self.loc.mod(0,1), hostile=1, health=20)
                B.guards.append(c)
        elif ID.julien in B.get_ids(locs):
            self.talk(objects[ID.julien])
            y = self.talk(objects[ID.julien], 'You may be able to find out more on Principal Island. I wanted to use this ferry ticket myself but I can guess I can sell it to you for some 10 kashes and buy some candy..', yesno=1)
            if y:
                if self.kashes>=10:
                    self.add1(ID.ferry_ticket)
                    self.kashes -= 10
        elif ID.ferry in B.get_ids(locs) and self.has(ID.ferry_ticket):
            triggered_events.append(TravelToPrincipalIslandEvent)
        else:
            loc = self.loc.mod(1,0)
            x = B[loc] # TODO won't work if something is in the platform tile
            if x and getattr(x,'id',None)==ID.platform_top1:
                PlatformEvent2(B).go()

    def use(self):
        B=self.B
        win = newwin(len(self.inv), 40, 2, 10)
        ascii_letters = string.ascii_letters
        for n, (item,qty) in enumerate(self.inv.items()):
            win.addstr(n,0, f'{ascii_letters[n]}) {item.name:4} - {qty}')
        ch = win.getkey()
        item = None
        if ch in ascii_letters:
            try:
                item = list(self.inv.keys())[string.ascii_letters.index(ch)]
            except IndexError:
                pass
        locs = [self.loc]
        def is_near(id):
            return getattr(ID, id) in B.get_ids(locs)

        if is_near('water_supply') and item.id == ID.jar_syrup:
            status('You add raspberry syrup to the water supply')
            self.inv[item] -=1
            empty_bottle = Item(None, Blocks.bottle, 'empty bottle', None, id=ID.empty_bottle)
            self.inv[empty_bottle] += 1
            # a little hacky, would be better to add a water supply obj and update its state
            objects[ID.clermont_ferrand].state = 2
        else:
            status('Nothing happens')

    def get_top_item(self):
        x = self.B[self.loc]
        return None if x==blank else x

    @property
    def alive(self):
        return self.health>0

    @property
    def dead(self):
        return not self.alive

class Quest:
    pass

class MaxQuest(Quest):
    def go(self, player):
        max_ = objects[ID.max_]
        if max_.state==1:
            player.talk(max_, conversations[ID.max1])
            max_.state=2
        elif max_.state==2 and player.has(ID.wine):
            y = player.talk(max_, 'Give wine to Max?', yesno=1)
            if y:
                player.remove1(ID.wine)
                max_.state = 3
        elif max_.state==3:
            player.talk(max_, conversations[ID.max2])
            max_.state=4

def first(x):
    return x[0] if x else None
def last(x):
    return x[-1] if x else None

def pdb(*arg):
    curses.nocbreak()
    Windows.win.keypad(0)
    curses.echo()
    curses.endwin()
    import pdb; pdb.set_trace()

class Event:
    def __init__(self, B, **kwargs):
        self.B = B
        self.player = objects[ID.player]
        self.kwargs = kwargs

    def animate_arc(self, item, to_loc, height=1, carry_item=None):
        B=self.B
        for _ in range(height):
            self.animate(item, 'k', n=height, carry_item=carry_item)
        a,b = item.loc, to_loc
        dir = 'h' if a.x>b.x else 'l'
        self.animate(item, dir, n=abs(a.x-b.x), carry_item=carry_item)
        for _ in range(height):
            self.animate(item, 'j', n=height, carry_item=carry_item)

    def animate(self, item, dir, B=None, n=999, carry_item=None):
        B = B or self.B
        for _ in range(n):
            item.move(dir)
            if carry_item:
                carry_item.move(dir)
            B.draw(Windows.win)
            sleep(SLP*4)
            if item.loc.x in (0, 78):
                B.remove(item)
                if carry_item:
                    B.remove(carry_item)
                return

class JailEvent(Event):
    once = False
    def go(self):
        player = objects[ID.player]
        if player.state==1:
            B=self.B
            player.tele(B.spawn_locations[8])
            c=Clone(B, B.spawn_locations[4])
            B.soldiers.append(c)
            Guard(B, B.spawn_locations[6], id=ID.guard2)
            Windows.win2.addstr(2,0, 'Suddenly a Groboclone appears and leads you away...')
            # TODO: this is an ugly hack, instead an event should only be triggered when player is in state=1, and make
            # this a once=True event
            JailEvent.once = True

def status(msg):
    Windows.win2.addstr(2,0,msg)

class TravelByCarEvent(Event):
    once = False
    def go(self):
        dest = self.kwargs.get('dest')
        B = self.B
        car = objects[ID.car]
        B.remove(self.player)
        self.animate(car, 'h')

        # switch to landscape map
        B = objects[ID.landscape_level1]
        self.B = B
        B.put(car, Loc(77,GROUND))
        self.animate(car, 'h')

        if dest == 'wtower':
            status('You have driven the car to the Water tower')
            B = self.player.move_to_board(None, Loc(7, GROUND), B=objects[ID.water_tower_level])
            B.put(car, Loc(6,GROUND))
        elif dest == 'top3':
            status('You have driven the car to the Empty Manor')
            B = self.player.move_to_board(Loc(7,0), Loc(7, GROUND))
            B.put(car, Loc(6,GROUND))
        elif dest == 'beluga':
            status('You have driven the car to Port Beluga')
            B = self.player.move_to_board(None, Loc(7, GROUND), B=objects[ID.port_beluga_level])
            B.put(car, Loc(6,GROUND))
        return B

class ClermontTriesWater(Event):
    once=1
    def go(self):
        clermont = objects[ID.clermont_ferrand]
        clermont.move('h')
        status('Clermont tries a bit of water from the from the fountain')
        status('Clermont tries a bit more of the water')
        self.player.talk(clermont, conversations[ID.clermont_ferrand3])
        clermont.tele(Loc(61,4))
        self.player.tele(Loc(59,5))
        self.B.remove(self.B.doors[0])
        status('Clermont opens the door')

class TravelToPrincipalIslandEvent(Event):
    once=True
    def go(self):
        player = objects[ID.player]
        player.remove1(ID.ferry_ticket)
        B = objects[ID.sea_level1]
        f = objects[ID.ferry]
        self.animate(f, 'h', B=B)
        status('You have taken the ferry to Principal island.')
        return player.move_to_board( Loc(7, self.B.loc.y), Loc(7, GROUND) )

class MovePlatform3Event(Event):
    once=False
    def go(self):
        B = self.B
        p = objects[ID.platform3]
        a,b = B.specials[4], B.specials[5]
        i = B[p.loc.mod_u()]
        if i==p or i is blank: i=None
        self.animate_arc(p, to_loc=(a if p.loc==b else b), carry_item=i)

class StatueInPlace(Event):
    once=True
    def go(self):
        self.B.remove(self.B.doors[0])

class LeaveBu(Event):
    once=False
    def go(self):
        return self.player.move_to_board( Loc(1, self.B.loc.y-1), Loc(7, GROUND) )

class TravelBySailboat(Event):
    once = False
    def go(self):
        dest = self.kwargs.get('dest')
        player = objects[ID.player]
        B = objects[ID.sea_level1]
        s = objects[ID.sailboat]
        B.put(s, Loc(78,GROUND))
        self.animate(s, 'h', B=B)
        status('The sailboat took you to ' + ('the White Leaf Desert' if dest=='desert1' else 'Port Beluga'))
        if dest == 'desert1':
            return player.move_to_board( Loc(0, 0), Loc(7, GROUND) )
        elif dest == 'beluga':
            return player.move_to_board(None, Loc(7, GROUND), B=objects[ID.port_beluga_level])

class GuardAttackEvent1(Event):
    once=True
    def go(self):
        guard = objects[ID.guard1]
        if self.done: return
        guard.hostile = 1
        B = self.B
        mode = 1
        x, y = guard.loc
        platform = objects[ID.platform1]

        for _ in range(55):
            if mode==1:
                if y>=HEIGHT-10:
                    platform.move('k')
                    guard.move('k', fly=1)
                    y = guard.loc.y
                else:
                    mode = 2
            elif mode==2:
                if x>=3:
                    platform.move('h')
                    guard.move('h', fly=1)
                    x = guard.loc.x
                else:
                    mode = 3
            elif mode==3:
                if y<GROUND:
                    platform.move('j')
                    guard.move('j', fly=1)
                    y = guard.loc.y
                else:
                    mode = 4
            elif mode==4:
                break
            B.draw(Windows.win)
            sleep(SLP)
        self.done = True

class PlatformEvent1(Event):
    once=True
    def go(self):
        debug('PlatformEvent1 start')
        if self.done: return
        player = objects[ID.player]
        B = self.B
        mode = 1
        x, y = player.loc
        platform = objects[ID.platform1]

        debug('y', y)
        for _ in range(35):
            debug('y', y, 'mode', mode, 'height-10', HEIGHT-10)
            if mode==1:
                if y>=(HEIGHT-10):
                    platform.move('k')
                    player.move('k', fly=1)
                    y = player.loc.y
                else:
                    mode = 2

            elif mode==2:
                if x<15:
                    platform.move('l')
                    player.move('l', fly=1)
                    x = player.loc.x
                else:
                    mode = 3
            elif mode==3:
                if y<GROUND:
                    platform.move('j')
                    player.move('j', fly=1)
                    y = player.loc.y
                else:
                    mode = 4

            elif mode==4:
                break
            B.draw(Windows.win)
            sleep(SLP)
        self.done = True

class ClimbThroughGrillEvent1(Event):
    once = False
    def go(self):
        player = objects[ID.player]
        bi = self.B.loc.x
        loc = Loc(25 if bi==0 else 36, GROUND)
        b_loc = Loc(2 if bi==0 else 0, self.B.loc.y)
        Windows.win2.addstr(2,0, 'You climb through the grill into a space that opens into an open area outside the building')
        return player.move_to_board(b_loc, loc)

class ClimbThroughGrillEvent2(Event):
    once = False
    def go(self):
        player = objects[ID.player]
        x, y = self.B.loc
        if x==5:
            y-=1
        else:
            y+=1
        x = 0 if x==5 else 5
        b_loc = Loc(x, y)
        Windows.win2.addstr(2,0, 'You climb through the grill ' +
                            ('into a strange underground area' if x==5 else 'back into your home'))
        return player.move_to_board(b_loc, Loc(62,10))

class ClimbThroughGrillEvent3(Event):
    once = False
    def go(self):
        player = objects[ID.player]
        bi = self.B.loc.x
        x = 6 if bi==5 else 5
        b_loc = Loc(x, self.B.loc.y)
        Windows.win2.addstr(2,0, 'You climb through the grill into ' +
                            ('the port area' if bi==5 else 'back to the shore near your home'))
        if player.state == 0:
            player.state = 1
        elif player.state == 1:
            player.state = 2
        return player.move_to_board(b_loc, Loc(72, GROUND))

class AlarmEvent1(Event):
    once=True
    def go(self):
        if self.done: return
        tech = objects[ID.technician1]
        x, y = tech.loc

        for _ in range(35):
            tech.move('l')
            if ID.alarm1 in self.B.get_ids(tech.loc):
                Windows.win2.addstr(2,0, '!ALARM!')
                return Saves().load('start')
            self.B.draw(Windows.win)
            sleep(0.1)

class GarbageTruckEvent(Event):
    once=True
    def go(self):
        B=self.B
        if self.done: return
        t = Item(B, Blocks.truck, 'Garbage truck', Loc(78, GROUND))
        dir = 'h'
        pl = objects[ID.player]
        for _ in range(75):
            t.move(dir)
            if t.loc == pl.loc:
                dir = 'l'
                B.remove(pl)
                Windows.win2.addstr(2,0, 'The truck suddenly picks you up along with the rubbish!')
            if t.loc.x==78:
                B.remove(t)
                B.draw(Windows.win)
                break
            B.draw(Windows.win)
            sleep(SLP)
        return pl.move_to_board(Loc(3, B.loc.y), Loc(0,GROUND))

class PlatformEvent2(Event):
    once=True
    def go(self):
        B = self.B
        p = objects[ID.platform_top1]
        pl = objects[ID.player]
        dir = 'j' if pl.loc.y == GROUND-4 else 'k'
        for _ in range(45):
            p.move(dir)
            pl.move(dir, fly=1)
            if pl.loc.y in (GROUND, GROUND-4):
                break
            B.draw(Windows.win)
            sleep(0.2)

class ShopKeeperEvent1(Event):
    once=True
    def go(self):
        pl = objects[ID.player]
        shk = objects[ID.shopkeeper1]
        pl.talk(shk)
        timers.append(Timer(10, ShopKeeperAlarmEvent))

class ShopKeeperAlarmEvent(Event):
    once=True
    def go(self):
        shk = objects[ID.shopkeeper1]
        if shk.health > 0:
            return Saves().load('start')

class DieEvent(Event):
    once=False
    def go(self):
        return Saves().load('start')

class MagicBallEvent(Event):
    once=False
    def go(self, player, last_dir):
        B = self.B
        mb = Item(self.B, Blocks.magic_ball, '', player.loc)
        dir = last_dir
        for n in range(45):
            mb.move(dir)
            be = B.is_being(mb.loc)
            if be and be is not player:
                player.hit(be)
                dir = rev_dir(dir)
            elif B.is_blocked(mb.loc):
                dir = rev_dir(dir)
            elif n == 5 and dir==last_dir:
                dir = rev_dir(dir)
            if mb.loc == player.loc:
                break
            B.draw(Windows.win)
            sleep(0.15)
        B.remove(mb)

class BuyADrinkAnthony(Event):
    once=True
    def go(self):
        pl = objects[ID.player]
        yes = pl.talk(objects[ID.anthony], 'Would you like to buy a drink for two kashes?', yesno=1)
        if yes:
            if pl.kashes>=2:
                pl.kashes -= 2
                pl.add1(ID.wine)
                Windows.win2.addstr(2,0, 'You bought a glass of wine.')
            else:
                Windows.win2.addstr(2,0, "OH NO! You don't have enough kashes.. ..")

class MaxState1(Event):
    once=True
    def go(self):
        objects[ID.max_].state = 1


class SoldierEvent2(Event):
    once=False
    def go(self):
        s = objects[ID.soldier2]
        pl = objects[ID.player]
        pl.tele(pl.loc.mod(0,-3))
        self.B.draw(Windows.win)
        Windows.win2.addstr(1, 0, 'You climb through the window covered by a grill and escape to the open area')
        pl.state = 1
        if s.state == 0:
            ch = pl.talk(s)
            if ch==1:
                s.hostile = 1
            else:
                s.state = 1

def rev_dir(dir):
    return dict(h='l',l='h',j='k',k='j')[dir]

class Timer:
    def __init__(self, turns, evt):
        self.turns, self.evt = turns, evt

class Player(Being):
    char = '🙍'
    health = 50
    is_player = 1
    stance = Stance.sneaky

class Guard(Being):
    char = 'g'
    health = 3

class Soldier(Being):
    health = 20
    char = Blocks.soldier

class Technician(Being):
    char = 't'

class RoboBunny(Being):
    char = Blocks.rabbit

class Clone(Being):
    char = Blocks.elephant

class ShopKeeper(Being):
    char = '🙇'

class Grobo(Being):
    char = Blocks.elephant

class NPCs:
    pass
class OtherBeings:
    pass
class Windows:
    win = win2 = None
class Misc:
    pass

class Saves:
    saves = {}
    loaded = 0

    def save(self, name, cur_brd):
        s = {}
        s['boards'] = deepcopy(boards)
        s['beings'] = deepcopy(OtherBeings)
        s['cur_brd'] = cur_brd
        player = objects[ID.player]
        s['player'] = deepcopy(objects[ID.player])
        s['objects'] = deepcopy(objects)
        bl = cur_brd
        B = boards[bl.y][bl.x]
        print("B.get_all(player.loc)", B.get_all(player.loc))
        print("in save s['player'].loc", s['player'].loc)
        self.saves[name] = s

    def load(self, name):
        s = self.saves[name]
        boards[:] = s['boards']
        global objects
        objects = s['objects']
        loc = s['player'].loc
        print("load, player loc", loc)
        bl = s['cur_brd']
        B = boards[bl.y][bl.x]
        print("B.get_all(loc)", B.get_all(loc))
        player = B[loc]
        player.B = B
        objects[ID.player] = player
        return player, B

def dist(a,b):
    return max(abs(a.loc.x - b.loc.x),
               abs(a.loc.y - b.loc.y))

def main(stdscr):
    Misc.is_game = 1
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_WHITE)
    begin_x = 0; begin_y = 0; width = 80
    win = Windows.win = newwin(HEIGHT, width, begin_y, begin_x)
    begin_x = 0; begin_y = 16; height = 6; width = 80
    win2 = Windows.win2 = newwin(height, width, begin_y, begin_x)

    # generatable items
    coin = Item(None, Blocks.coin, 'coin', None, id=ID.coin)
    grn_heart = Item(None, Blocks.grn_heart, 'heart', None, id=ID.grn_heart)
    key1 = Item(None, Blocks.key, 'key', None, id=ID.key1)
    fuel = Item(None, Blocks.box1, 'fuel', None, id=ID.fuel)
    objects[ID.fuel] = fuel
    objects[ID.coin] = coin
    objects[ID.grn_heart] = grn_heart
    objects[ID.key1] = key1

    MAIN_Y = 3
    B = b1 = Board(Loc(0,MAIN_Y), 1)
    b2 = Board(Loc(1,MAIN_Y), 2)
    b3 = Board(Loc(2,MAIN_Y), 3)
    b4 = Board(Loc(3,MAIN_Y), 4)
    b5 = Board(Loc(4,MAIN_Y), 5)
    b6 = Board(Loc(5,MAIN_Y), 6)
    b7 = Board(Loc(6,MAIN_Y), 7)
    b8 = Board(Loc(7,MAIN_Y), 8)
    b9 = Board(Loc(8,MAIN_Y), 9)

    und1 = Board(None, 'und1')
    sea1 = Board(None, 'sea1')
    objects[ID.sea_level1] = sea1
    landscape1 = Board(None, 'landscape1')
    landscape1.board_landscape1()
    wtower = Board(None, 'wtower')
    objects[ID.landscape_level1] = landscape1
    objects[ID.water_tower_level] = wtower
    beluga = Board(None, 'beluga')
    beluga.board_beluga()
    objects[ID.port_beluga_level] = beluga

    player = b1.board_1()
    b2.board_2()
    b3.board_3()
    b4.board_4()
    b5.board_5()
    b6.board_6()
    b7.board_7()
    b8.board_8()

    und1.board_und1()
    sea1.board_sea1()
    wtower.board_wtower()

    b9 = Board(Loc(8,MAIN_Y), 9)
    b9.board_9()
    b10 = Board(Loc(9,MAIN_Y), 10)
    b10.board_10()
    b11 = Board(Loc(10,MAIN_Y), 11)
    b11.board_11()
    b12 = Board(Loc(11,MAIN_Y), 12)
    b12.board_12()

    top1 = Board(Loc(9,MAIN_Y-1), 'top1')
    top1.board_top1()

    top2 = Board(Loc(8,MAIN_Y-1), 'top2')
    top2.board_top2()
    top3 = Board(Loc(7,MAIN_Y-1), 'top3')
    top3.board_top3()

    desert1 = Board(Loc(0,MAIN_Y-3), 'desert1')
    desert1.board_desert1()

    desert2 = Board(Loc(1,MAIN_Y-3), 'desert2')
    desert2.board_desert2()
    des_und = Board(Loc(1,MAIN_Y-2), 'des_und')
    des_und.board_des_und()
    des_und2 = Board(Loc(0,MAIN_Y-2), 'des_und2')
    des_und2.board_des_und2()

    boards[:] = (
         [desert1,desert2,None,None, None,None,None,None, None,None, None, None],

         [des_und2,des_und,None,None, None,None,None,None, None,None, None, None],

         [None,None,None,None, None,None,None,top3, top2,top1, None, None],
         [b1, b2,   b3, b4,    b5, b6,   b7, b8,    b9, b10, b11, b12],
         [None,None,None,None, None,None,None,None, None,None, None, None])

    stdscr.clear()
    B.draw(win)

    win2.addstr(0, 0, '-'*80)
    win2.refresh()

    Saves().save('start', B.loc)
    last_cmd = None
    wait_count = 0
    last_dir = 'l'

    while 1:
        k = win.getkey()
        win2.clear()
        win2.addstr(1,0, ' '*78)
        win2.addstr(2,0,k)
        if k=='q':
            return
        elif k=='f':
            player.stance = Stance.fight
            win2.addstr(1, 0, 'stance: fight')
        elif k=='n':
            player.stance = Stance.normal
            win2.addstr(1, 0, 'stance: normal')

        elif k in 'hjklHL':
            last_dir = k
            if k in 'HL':
                k = k.lower()
                for _ in range(5):
                    rv = player.move(k)
                    if rv[0] == LOAD_BOARD:
                        break
            else:
                rv = player.move(k)
            if rv[0] == LOAD_BOARD:
                loc = rv[1]
                if loc==ID.fall:
                    # a bit ugly, handle fall as explicit 'move' down
                    k = 'j'
                    loc = B.loc.mod(1,0)
                x, y = player.loc
                if k=='l': x = 0
                if k=='h': x = 78
                if k=='k': y = 15
                if k=='j': y = 0

                # ugly but....
                p_loc = Loc(x, y)
                B = player.move_to_board(loc, p_loc)
                B.remove(player)
                player.loc = player.fall(player.loc)
                B.put(player)

        elif k == '.':
            if last_cmd=='.':
                wait_count += 1
            if wait_count >= 5 and ID.rubbish1 in B.get_ids(player.loc):
                triggered_events.append(GarbageTruckEvent)
            debug(str(triggered_events))
        elif k == 's':
            player.switch_places()
        elif k == 'S':
            player.stance = Stance.sneaky
            win2.addstr(1, 0, 'stance: sneaky')
        elif k == 'v':
            status(str(player.loc))
            # player, B = Saves().load('start')
            # objects[ID.player] = player
        elif k == ' ':
            player.action()
        elif k == '4':
            mp = ''
            while 1:
                mp += win.getkey()
                status(mp)
                Windows.win2.refresh()
                if mp in map_to_loc:
                    loc,b = map_to_loc[mp]
                    B = player.move_to_board(loc, Loc(7, GROUND), B=b)
                    if B._map=='des_und': player.tele(Loc(7,7))
                    if B._map=='des_und2': player.tele(Loc(70,7))
                if not any(m.startswith(mp) for m in map_to_loc):
                    break
        elif k == '5':
            k = win.getkey()
            k+= win.getkey()
            print(B.B[int(k)])
            status(f'printed row {k} to debug')
        elif k == '6':
            B = player.move_to_board( Loc(1,0), Loc(35, GROUND) )
        elif k == '7':
            B = player.move_to_board( Loc(6,MAIN_Y), Loc(72, GROUND) )
        elif k == '8':
            B = player.move_to_board( Loc(7,MAIN_Y), Loc(7, GROUND) )
        elif k == '9':
            B = player.move_to_board( Loc(9,MAIN_Y), Loc(59, 5) )

        elif k == '0':
            B = player.move_to_board( Loc(0,0), Loc(7, GROUND) )
        # -----------------------------------------------------------------------------------------------

        elif k == 'u':
            player.use()

        elif k == 'U':
            B = player.move_to_board( None, Loc(35, 10) , B=und1)
        elif k == 'E':
            B.display(str(B.get_all(player.loc)))
        elif k == 'm':
            if player.has(ID.magic_ball):
                MagicBallEvent(B).go(player, last_dir)
        elif k == 'i':
            txt = []
            for item, n in player.inv.items():
                txt.append(f'{item.name} {n}')
            B.display(txt)

        if k != '.':
            wait_count = 0
        last_cmd = k

        B.guards = [g for g in B.guards if g.health>0]
        B.soldiers = [g for g in B.soldiers if g.health>0]
        for g in B.guards:
            if g.hostile:
                g.attack(player)
        for s in B.soldiers:
            if s.hostile or dist(s, player) <= (1 if player.sneaky_stance else 5):
                s.hostile = 1
                s.attack(player)

        if player.health <= 0:
            win2.addstr(1, 0, f'Hmm.. it looks like you lost the game!')
            player, B = Saves().load('start')

        for evt in triggered_events:
            kwargs = {}
            if isinstance(evt, SEQ_TYPES):
                evt, kwargs = evt
            if evt in done_events and evt.once:
                continue
            rv = evt(B, **kwargs).go()
            if isinstance(rv, Board):
                B = rv
            try:
                player, B = rv
            except Exception as e:
                print("e", e)
                pass
            done_events.add(evt)

        triggered_events.clear()
        for t in timers:
            t.turns -= 1
            if not t.turns:
                triggered_events.append(t.evt)
        timers[:] = [t for t in timers if t.turns>0]
        B.draw(win)
        key = '[key]' if player.has(ID.key1) else ''
        win2.addstr(0,0, f'[{STANCES[player.stance]}] [H{player.health}] [{player.kashes} Kashes] {key}')
        win2.refresh()


def debug(*args):
    debug_log.write(str(args) + '\n')
    debug_log.flush()
print=debug

def editor(stdscr, _map):
    Misc.is_game = 0
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_WHITE)
    begin_x = 0; begin_y = 0; width = 80
    win = newwin(HEIGHT, width, begin_y, begin_x)
    curses.curs_set(True)
    loc = Loc(40, 8)
    brush = None
    written = 0
    B = Board(Loc(0,0), _map)
    import os
    fname = f'maps/{_map}.map'
    if not os.path.exists(fname):
        with open(fname, 'w') as fp:
            for _ in range(HEIGHT):
                fp.write(blank*78 + '\n')
    B.load_map(_map, 1)
    B.draw(win)

    while 1:
        k = win.getkey()
        if k=='Q': return
        elif k in 'hjklyubnHL':
            n = 1
            if k in 'HL':
                n = 5
            m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0), y=(-1,-1), u=(-1,1), b=(1,-1), n=(1,1), H=(0,-1), L=(0,1))[k]

            for _ in range(n):
                if brush:
                    B.B[loc.y][loc.x] = [brush]
                if chk_oob(loc.mod(*m)):
                    loc = loc.mod(*m)

        elif k == ' ':
            brush = None
        elif k == 'e':
            brush = ' '
        elif k == 'r':
            brush = rock
        elif k == 's':
            B.put(Blocks.steps_r, loc)
            brush = Blocks.steps_r
        elif k == '/':
            B.put(Blocks.angled1, loc)
            brush = Blocks.angled1
        elif k == '\\':
            B.put(Blocks.angled2, loc)
            brush = Blocks.angled2
        elif k == 'S':
            B.put(Blocks.steps_l, loc)
            brush = Blocks.steps_l
        elif k == 'M':
            B.put(Blocks.smoke_pipe, loc)
        elif k == 'd':
            B.put(Blocks.door, loc)
        elif k in '0123456789':
            B.put(k, loc)
        elif k == 'w':
            B.put(Blocks.water, loc)
        elif k == 't':
            B.put(Blocks.stool, loc)
        elif k == 'a':
            B.put(Blocks.ladder, loc)
        elif k == 'c':
            B.put(Blocks.cupboard, loc)
        elif k == 'B':
            B.put(Blocks.dock_boards, loc)
        elif k == 'p':
            B.put(Blocks.platform_top, loc)
        elif k == 'g':
            B.put(Blocks.grill, loc)
        elif k == 'F':
            B.put(Blocks.ferry, loc)
        elif k == 'A':
            B.put(Blocks.bars, loc)
        elif k == 'R':
            B.put(Blocks.rubbish, loc)

        elif k == 'G':
            B.put(Blocks.elephant, loc)
        elif k == 'r':
            B.put(Blocks.rabbit, loc)
        elif k == 'O':
            B.put(Blocks.soldier, loc)

        elif k == 'T':
            B.put(choice((Blocks.tree1, Blocks.tree2)), loc)
        elif k == 'z':
            B.put(Blocks.guardrail_m, loc)
            brush = Blocks.guardrail_m
        elif k == 'x':
            B.put(Blocks.rock2, loc)
            brush = Blocks.rock2
        elif k == 'X':
            B.put(Blocks.shelves, loc)
        elif k == 'C':
            B.put(Blocks.cactus, loc)

        elif k == 'o':
            cmds = 'gm gl gr l b ob f'.split()
            cmd = ''
            BL=Blocks
            while 1:
                cmd += win.getkey()
                if   cmd == 'gm': B.put(BL.guardrail_m, loc)
                elif cmd == 'gl': B.put(BL.guardrail_l, loc)
                elif cmd == 'gr': B.put(BL.guardrail_r, loc)

                elif cmd == 'l':  B.put(BL.locker, loc)
                elif cmd == 'b':  B.put(BL.books, loc)
                elif cmd == 'ob': B.put(BL.open_book, loc)
                elif cmd == 't':  B.put(BL.tulip, loc)
                elif cmd == 'f':  B.put(BL.fountain, loc)
                elif cmd == 'a':  B.put(BL.antitank, loc)
                elif cmd == 'p':  B.put(BL.platform2, loc)

                elif cmd == 'oc':  B.put(BL.car, loc)

                elif cmd == 'm': B.put(BL.monkey, loc)
                elif cmd == 'v': B.put(BL.lever, loc)
                elif cmd == 's': B.put(BL.sharp_rock, loc)
                elif cmd == 'r': B.put(BL.rock3, loc)
                elif cmd == 'd': B.put(BL.hexagon, loc)     # drawing

                elif any(c.startswith(cmd) for c in cmds):
                    continue
                break

        elif k in 'E':
            win.addstr(2,2, 'Are you sure you want to clear the map? [Y/N]')
            y = win.getkey()
            if y=='Y':
                for row in B.B:
                    for cell in row:
                        cell[:] = [blank]
                B.B[-1][-1].append('_')
        elif k in 'f':
            B.put(Blocks.shelves, loc)
        elif k == 'W':
            with open(f'maps/{_map}.map', 'w') as fp:
                for row in B.B:
                    for cell in row:
                        fp.write(str(cell[-1]))
                    fp.write('\n')
            written=1
        B.draw(win)
        if brush==blank:
            tool = 'eraser'
        elif brush==rock:
            tool = 'rock'
        elif not brush:
            tool = ''
        else:
            tool = brush
        win.addstr(1,73, tool)
        win.addstr(0, 0 if loc.x>40 else 70,
                   str(loc))
        if written:
            win.addstr(2,65, 'map written')
            written=0
        win.move(loc.y, loc.x)


if __name__ == "__main__":
    argv = sys.argv[1:]
    if first(argv) == 'ed':
        wrapper(editor, argv[1])
    else:
        wrapper(main)
