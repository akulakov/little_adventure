#!/usr/bin/env python
"""
bugs

TODO
    - update stairs on screen 2
"""
from curses import wrapper, newwin
import curses
import sys
from copy import copy, deepcopy
from time import sleep
from random import random, choice
from collections import defaultdict
from textwrap import wrap

start_x_loc = 30
rock = '█'
blank = ' '
HEIGHT = 16
GROUND = HEIGHT-2   # ground level
LOAD_BOARD = 999
SLP = 0.01
debug_log = open('debug', 'w')
triggered_events = []
done_events = set()
boards = []
objects = {}
timers = []


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
    fountain = '⛲' # TODO find a new unicode; doesn't work
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

BLOCKING = [rock, Type.door1, Type.door2, Type.door3, Blocks.block1, Blocks.steps_r, Blocks.steps_l, Type.platform_top, Type.door_top_block, Type.blocking]

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

    guard1 = 100
    technician1 = 101
    player = 102
    soldier1 = 103
    robobunny1 = 104
    shopkeeper1 = 105
    max = 106
    anthony = 107
    julien = 108
    soldier2 = 109
    guard2 = 110
    wally = 111
    chamonix = 112
    agen = 113

    max1 = 200
    max2 = 201
    trick_guard = 202

items_by_id = {v:k for k,v in ID.__dict__.items()}
descr_by_id = copy(items_by_id)
descr_by_id.update(
    {14: 'a jar of syrup',
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
    ID.agen: ["Did you know Dr. Funfrock installed his busts to protect and defend us? The ones that don't have pedestals are covering ancient undestructible seals that could put the entire system of governance in danger!"]
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


class Board:
    def __init__(self, loc, init_rocks=True):
        self.B = B = [mkrow() for _ in range(HEIGHT)]
        bottom = B[-1]
        if init_rocks:
            for cell in bottom:
                cell.append(rock)
        self.guards = []
        self.soldiers = []
        self.labels = []
        self.spawn_locations = {}
        self.trigger_locations = {}
        self.loc = loc

    def board_1(self):
        Item(self, Blocks.platform, 'mobile platform', Loc(15, GROUND), id=ID.platform1)
        g = Guard(self, Loc(15, GROUND), id=ID.guard1)
        self.guards = [g]

        self.put(rock, Loc(5, GROUND))
        self.put(rock, Loc(5, GROUND-1))
        for x in range(4):
            Item(self, Blocks.grill, 'grill', Loc(20+(x*4), GROUND))
        Item(self, Blocks.grill, 'grill', Loc(20+16, GROUND), id=ID.grill1)

        Item(self, Blocks.key, 'key', Loc(37,GROUND), id=ID.key1)
        c = Locker(self, Loc(40,GROUND))
        c.inv[ID.coin] += 1
        c = Locker(self, Loc(42,GROUND))
        c = Locker(self, Loc(44,GROUND))
        Item(self, Blocks.door, 'door', Loc(48,GROUND), id=ID.door1, type=Type.door1)
        Item(self, Blocks.block1, 'block', Loc(48,GROUND-1))
        MagicBall(self, Loc(50, GROUND))

        p = Player(self, Loc(start_x_loc, GROUND), id=ID.player)

        # objects[ID.player] = p
        return p

    def board_2(self):
        """Technician, alarm."""
        for x in range(5):
            row = self.B[-2-x]
            for cell in row[10+x:]:
                cell.append(rock)
        Technician(self, Loc(20, GROUND-5), id=ID.technician1)
        Item(self, Blocks.bell, 'alarm bell', Loc(25, GROUND-5), id=ID.alarm1)
        Item(self, Blocks.door, 'door', Loc(15, GROUND-5), id=ID.door1, type=Type.door1)

    def board_3(self):
        """Soldier, rubbish heap."""
        containers, crates, doors, specials = self.load_map(3)
        RoboBunny(self, specials[1], id=ID.robobunny1)
        Item(self, Blocks.grill, 'grill', specials[2], id=ID.grill2)
        s = Soldier(self, specials[3], id=ID.soldier1)
        self.soldiers.append(s)

    def board_4(self):
        self.labels.append((0,20, "𝓪𝓫𝓮 𝓸𝓵𝓭 𝓼𝓱𝓸𝓹𝓹𝓮"))    # Abe old shoppe
        containers, crates, doors, specials = self.load_map(4)
        Item(self, Blocks.platform_top, 'platform', specials[Blocks.platform_top], id=ID.platform_top1, type=Type.platform_top)
        ShopKeeper(self, specials[1], name='Abe', id=ID.shopkeeper1)
        containers[3].inv[ID.jar_syrup] = 1

    def board_5(self):
        self.labels.append((2,20, "𝓐𝓷𝓽𝓱𝓸𝓷𝔂 𝓫𝓪𝓻"))
        containers, crates, doors, specials = self.load_map(5)
        containers[2].inv[ID.key1] = 1
        Grobo(self, specials[1], id=ID.max, name='Max')
        RoboBunny(self, specials[2], id=ID.anthony, name='Anthony')

    def board_6(self):
        self.labels.append((2,20, "𝒯𝓌𝒾𝓃𝓈𝑒𝓃 𝐻𝑜𝓂𝑒"))
        containers, crates, doors, specials = self.load_map(6)
        containers[0].inv[ID.magic_ball] = 1
        containers[0].inv[ID.key1] = 1
        crates[5].id = ID.crate1
        TriggerEventLocation(self, specials[1], evt=MaxState1)
        Item(self, Blocks.grill, 'grill', specials[2], id=ID.grill4)

    def board_7(self):
        self.labels.append((10,5, "𝒯𝒽𝑒 𝐹𝑒𝓇𝓇𝓎"))
        containers, crates, doors, specials = self.load_map(7)
        julien, clone1 = specials[Blocks.elephant]
        clone1.inv[ID.key3] = [Item(self, Blocks.key, 'key', id=ID.key3, put=0), 1]
        julien.id = ID.julien
        objects[julien.id] = julien
        doors[0].type = Type.door3
        Item(self, Blocks.grill, 'grill', specials[1], id=ID.grill4)
        Item(self, Blocks.ticket_seller, 'Ticket seller booth', specials[2], id=ID.ticket_seller1)
        # invisible, with ferry id to be able to take the ferry near this tile
        Item(self, '', '', specials[3], id=ID.ferry)

    def board_8(self):
        containers, crates, doors, specials = self.load_map(8)
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
        self.load_map(9)

    def board_10(self):
        containers, crates, doors, specials = self.load_map(10)
        Grobo(self, specials[1], id=ID.wally, name='Wally')
        RoboBunny(self, specials[2], id=ID.chamonix, name='Mr. Chamonix')
        Being(self, specials[3], id=ID.agen, name='Agen', char=Blocks.monkey)

    def board_und1(self):
        containers, crates, doors, specials = self.load_map('und1')
        Item(self, Blocks.grill, 'grill', specials[1], id=ID.grill3)

    def board_sea1(self):
        specials = self.load_map('sea1')[3]
        Item(self, Blocks.ferry, 'ferry', specials[1], id=ID.ferry)

    def load_map(self, map_num, for_editor=0):
        _map = open(f'maps/{map_num}.map').readlines()
        crates = []
        containers = []
        doors = []
        specials = defaultdict(list)
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

                    elif char==Blocks.block1:
                        Item(self, Blocks.block1, 'block', loc, type=Type.door_top_block)

                    elif char==Blocks.smoke_pipe:
                        Item(self, Blocks.smoke_pipe, 'smoke pipe', loc, type=Type.ladder)

                    elif char==Blocks.fireplace:
                        Item(self, Blocks.fireplace, 'fireplace', loc)

                    elif char==Blocks.water:
                        Item(self, Blocks.water, 'water', loc, type=Type.water)

                    elif char==Blocks.stool:
                        Item(self, Blocks.stool, 'bar stool', loc)

                    elif char==Blocks.tulip:
                        Item(self, Blocks.tulip, 'tulip', loc)

                    elif char==Blocks.fountain:
                        Item(self, Blocks.fountain, 'fountain', loc)

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

                    elif char==Blocks.platform_top:
                        specials[Blocks.platform_top] = loc
                        if for_editor:
                            self.put(Blocks.platform_top, loc)

                    elif char==Blocks.steps_l:
                        self.put(Blocks.steps_l, loc)

                    elif char==Blocks.steps_r:
                        self.put(Blocks.steps_r, loc)

                    elif char==Blocks.elephant:
                        g = Grobo(self, loc)
                        specials[Blocks.elephant].append(g)

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
        win.refresh()

    def put(self, obj, loc=None):
        loc = loc or obj.loc
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
        win = newwin(len(txt), w, 5, 5)
        for y, ln in enumerate(txt):
            win.addstr(y,0, ln)
        win.getkey()
        del win

def chk_oob(loc, y=0, x=0):
    return 0 <= loc.y+y <= HEIGHT-1 and 0 <= loc.x+x <= 78

def chk_b_oob(loc, y=0, x=0):
    h = len(boards)
    w = len(boards[0])
    return 0 <= loc.y+y <= h-1 and 0 <= loc.x+x <= w-1

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


class Item(Mixin1):
    def __init__(self, B, char, name, loc=None, put=True, id=None, type=None):
        self.B, self.char, self.name, self.loc, self.id, self.type = B, char, name, loc, id, type
        self.inv = defaultdict(int)
        if id:
            objects[id] = self
        if put:
            B.put(self)

    def __repr__(self):
        return self.char

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
            self.inv[ID.coin] += 1
        elif random()>.6:
            self.inv[ID.grn_heart] += 1

class Cupboard(Item):
    def __init__(self, B, loc):
        super().__init__(B, Blocks.cupboard, 'cupboard', loc, type=Type.container)
        if random()>.5:
            self.inv[ID.coin] += 1
        elif random()>.7:
            self.inv[ID.grn_heart] += 1

class MagicBall(Item):
    def __init__(self, B, loc):
        super().__init__(B, Blocks.magic_ball, 'magic_ball', loc, id=ID.magic_ball)

class Being(Mixin1):
    stance = Stance.normal
    health = 5
    is_being = 1
    is_player = 0
    hostile = 0
    type = None
    char = None

    def __init__(self, B, loc=None, put=True, id=None, name=None, state=0, hostile=False, health=5, char='?'):
        self.B, self.id, self.loc, self.name, self.state, self.hostile, self.health = \
                B, id, loc, name, state, hostile, health

        self.char = self.char or char
        self.inv = defaultdict(int)
        self.inv[ID.coin] = 14
        self.inv[ID.key1] = 2
        if id:
            objects[id] = self
        if put:
            B.put(self)

    def __str__(self):
        return self.char

    def move_to_board(self, b_loc, loc):
        if self in self.B.get_all(self.loc):
            self.B.remove(self)
        B = boards[b_loc.y][b_loc.x]
        self.loc = loc
        B.put(self)
        self.B = B
        return B

    @property
    def fight_stance(self):
        return self.stance==Stance.fight

    @property
    def sneaky_stance(self):
        return self.stance==Stance.sneaky

    def talk(self, being, dialog=None, yesno=False):
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
            #       (13, 21, 10, -13, 57)

            print(lines, w, loc.y, offset_y, x)
            y = max(0, loc.y+offset_y)
            win = newwin(lines, w, y, x)
            win.addstr(0,0, txt + (' [Y/N]' if yesno else ''))
            if yesno:
                # TODO in some one-time dialogs, may need to detect 'no' explicitly
                k = win.getkey()
                del win
                return k in 'Yy'
            elif multichoice:
                for _ in range(10):
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
        if new and Type.door1 in B.get_types(new) and self.inv[ID.key1]:
            B.remove(B[new])    # TODO will not work if something is on top of door
            self.inv[ID.key1] -= 1
            Windows.win2.addstr(2,0, 'You open the door with your key')
            return None, None

        if new and Type.door3 in B.get_types(new) and self.inv[ID.key3]:
            B.remove(B[new])    # TODO will not work if something is on top of door
            self.inv[ID.key3] -= 1
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
            if ID.grill5 in B.get_ids(new):
                new = new.mod(0,-3)
                Windows.win2.addstr(1, 0, 'You climb through the window covered by a grill and escape to a small nook under the stairs')
            if ID.grill6 in B.get_ids(new):
                SoldierEvent2(B).go()
                return None, None

            if B.loc.x==3 and new==Loc(23,8):   # TODO use trigger event location
                triggered_events.append(ShopKeeperEvent1)

            objs = [o.type for o in B.get_all_obj(new)]
            if not fly and not Type.ladder in objs:
                # fall
                new2 = new
                while 1:
                    # TODO: these may overdraw non-blocking items; it's an ugly hack but creates a nice fall animation
                    # for now
                    Windows.win.addstr(self.loc.y, self.loc.x, ' ')
                    Windows.win.addstr(new2.y, new2.x, ' ')
                    new2 = new2.mod(1,0)
                    if getattr(B[new2], 'type', None) == Type.water:
                        triggered_events.append(DieEvent)
                        Windows.win2.addstr(1, 0, 'You fall into the water and drown...')
                        return None, None
                    if chk_oob(new2) and B.avail(new2) and not Type.ladder in B.get_types(new2):
                        # ugly hack for the fall animation
                        Windows.win.addstr(new2.y, new2.x, str(self))
                        sleep(0.05)
                        Windows.win.refresh()
                        new = new2
                    else:
                        break

            pick_up = [ID.coin, ID.key1, ID.key2, ID.key3, ID.magic_ball]
            B.remove(self)
            self.loc = new

            if self.is_player:
                top_obj = B.get_top_obj(new)
                items = B.get_all_obj(new)
                if top_obj and top_obj.type == Type.event_trigger:
                    triggered_events.append(top_obj.evt)
                for x in reversed(items):
                    if x.id == ID.grn_heart:
                        self.health = min(15, self.health+1)
                        B.remove(x)
                    elif x.id in pick_up:
                        self.inv[x.id] += 1
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
            if ID.door1 in B.get_ids(self.loc):
                triggered_events.append(AlarmEvent1)
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
                for k, val in obj.inv.items():    # TODO: create according to `qty`
                    # temp hack around all beings having some coin
                    if isinstance(val, int): continue
                    it, qty = val
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
            Windows.win2.addstr(1, 0, f'{self} moved past {ro}')
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
        locs = [self.loc]
        if chk_oob(r): locs.append(r)
        if chk_oob(l): locs.append(l)

        if c:
            items = {k:v for k,v in c.inv.items() if v}
            lst = []
            for x in items:
                self.inv[x] += c.inv[x]
                c.inv[x] = 0
                lst.append(descr_by_id[x])
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
        elif ID.max in B.get_ids(locs):
            MaxQuest().go(self)
        elif ID.chamonix in B.get_ids(locs):
            self.talk(objects[ID.chamonix])
        elif ID.agen in B.get_ids(locs):
            self.talk(objects[ID.agen])
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
                if self.inv[ID.coin]>=10:
                    self.inv[ID.ferry_ticket] = 1
                    self.inv[ID.coin] -= 10
        elif ID.ferry in B.get_ids(locs) and self.inv[ID.ferry_ticket]:
            triggered_events.append(TravelToPrincipalIslandEvent)
        else:
            loc = self.loc.mod(1,0)
            x = B[loc] # TODO won't work if something is in the platform tile
            if x and getattr(x,'id',None)==ID.platform_top1:
                PlatformEvent2(B).go()

    def get_top_item(self):
        x = self.B[self.loc]
        return None if x==blank else x

class Quest:
    pass

class MaxQuest(Quest):
    def go(self, player):
        max_ = objects[ID.max]
        if max_.state==1:
            player.talk(max_, conversations[ID.max1])
            max_.state=2
        elif max_.state==2 and player.inv[ID.wine]:
            y = player.talk(max_, 'Give wine to Max?', yesno=1)
            if y:
                player.inv[ID.wine] -= 1
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
    done = False
    once = 1
    def __init__(self, B):
        self.B = B

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

class TravelToPrincipalIslandEvent(Event):
    def go(self):
        player = objects[ID.player]
        player.inv[ID.ferry_ticket] = 0
        B = boards[1][1]
        f = objects[ID.ferry]
        for _ in range(75):
            f.move('h')
            B.draw(Windows.win)
            sleep(0.15)
        Windows.win2.addstr(2,0, 'You have taken the ferry to Principal island.')
        return player.move_to_board( Loc(7,0), Loc(7, GROUND) )

class GuardAttackEvent1(Event):
    def go(self):
        guard = objects[ID.guard1]
        if self.done: return
        guard.hostile = 1
        B = self.B
        mode = 1
        x, y = guard.loc
        platform = objects[ID.platform1]

        for _ in range(35):
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
        b_loc = Loc(2 if bi==0 else 0, 0)
        Windows.win2.addstr(2,0, 'You climb through the grill into a space that opens into an open area outside the building')
        return player.move_to_board(b_loc, loc)

class ClimbThroughGrillEvent2(Event):
    once = False
    def go(self):
        player = objects[ID.player]
        bi = self.B.loc.x
        x = 0 if bi==5 else 5
        y = 1 if bi==5 else 0
        b_loc = Loc(x, y)
        Windows.win2.addstr(2,0, 'You climb through the grill ' + ('into a strange underground area' if bi==5 else 'back into your home'))
        return player.move_to_board(b_loc, Loc(62,10))

class ClimbThroughGrillEvent3(Event):
    once = False
    def go(self):
        player = objects[ID.player]
        bi = self.B.loc.x
        x = 6 if bi==5 else 5
        b_loc = Loc(x, 0)
        Windows.win2.addstr(2,0, 'You climb through the grill into ' + ('the port area' if bi==5 else 'back to the shore near your home'))
        if player.state == 0:
            player.state = 1
        elif player.state == 1:
            player.state = 2
        return player.move_to_board(b_loc, Loc(72, GROUND))

class AlarmEvent1(Event):
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
        return pl.move_to_board(Loc(3,0), Loc(0,GROUND))

class PlatformEvent2(Event):
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
    def go(self):
        pl = objects[ID.player]
        shk = objects[ID.shopkeeper1]
        pl.talk(shk)
        timers.append(Timer(10, ShopKeeperAlarmEvent))

class ShopKeeperAlarmEvent(Event):
    def go(self):
        shk = objects[ID.shopkeeper1]
        if shk.health > 0:
            return Saves().load('start')

class DieEvent(Event):
    def go(self):
        return Saves().load('start')

class MagicBallEvent(Event):
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
    def go(self):
        pl = objects[ID.player]
        yes = pl.talk(objects[ID.anthony], 'Would you like to buy a drink for two kashes?', yesno=1)
        if yes:
            if pl.inv[ID.coin]>=2:
                pl.inv[ID.coin] -= 2
                pl.inv[ID.wine] += 1
                Windows.win2.addstr(2,0, 'You bought a glass of wine.')
            else:
                Windows.win2.addstr(2,0, "OH NO! You don't have enough kashes.. ..")

class MaxState1(Event):
    def go(self):
        objects[ID.max].state = 1


class SoldierEvent2(Event):
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
    health = 10
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
    pass

class Saves:
    saves = {}
    loaded = 0

    def save(self, name, cur_brd):
        s = {}
        s['boards'] = deepcopy(boards)
        s['beings'] = deepcopy(OtherBeings)
        s['cur_brd'] = cur_brd
        s['player'] = deepcopy(objects[ID.player])
        self.saves[name] = s

    def load(self, name):
        s = self.saves[name]
        boards[:] = s['boards']
        loc = s['player'].loc
        bl = s['cur_brd']
        B = boards[bl.y][bl.x]
        player = B[loc]
        # pdb(B, loc)
        player.B = B
        objects[ID.player] = player
        return player, B

def dist(a,b):
    return max(abs(a.loc.x - b.loc.x),
               abs(a.loc.y - b.loc.y))

def main(stdscr):
    begin_x = 0; begin_y = 0; width = 80
    win = Windows.win = newwin(HEIGHT, width, begin_y, begin_x)
    begin_x = 0; begin_y = 16; height = 6; width = 80
    win2 = Windows.win2 = newwin(height, width, begin_y, begin_x)
    B = b1 = Board(Loc(0,0))
    b2 = Board(Loc(1,0))
    b3 = Board(Loc(2,0))
    b4 = Board(Loc(3,0))
    b5 = Board(Loc(4,0))
    b6 = Board(Loc(5,0), init_rocks=0)
    b7 = Board(Loc(6,0), init_rocks=0)
    b8 = Board(Loc(7,0), init_rocks=0)
    b9 = Board(Loc(8,0), init_rocks=0)
    und1 = Board(Loc(0,1), init_rocks=0)
    sea1 = Board(Loc(1,1), init_rocks=0)

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

    b9 = Board(Loc(8,0), init_rocks=0)
    b9.board_9()
    b10 = Board(Loc(9,0), init_rocks=0)
    b10.board_10()

    boards[:] = ([b1, b2, b3, b4, b5, b6, b7, b8, b9, b10], [und1, sea1])

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
                x = 0 if k=='l' else 78     # TODO support up/down
                p_loc = Loc(x, player.loc.y)
                B = player.move_to_board(loc, p_loc)

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
        elif k == 'L':
            player, B = Saves().load('start')
            objects[ID.player] = player
        elif k == ' ':
            player.action()
        elif k == '4':
            B = player.move_to_board( Loc(3,0), Loc(35, GROUND-5) )
        elif k == '5':
            B = player.move_to_board( Loc(4,0), Loc(35, GROUND) )
        elif k == '6':
            B = player.move_to_board( Loc(5,0), Loc(35, GROUND) )
        elif k == '7':
            B = player.move_to_board( Loc(6,0), Loc(72, GROUND) )
        elif k == '8':
            B = player.move_to_board( Loc(7,0), Loc(7, GROUND) )
        elif k == '9':
            B = player.move_to_board( Loc(9,0), Loc(7, GROUND) )
        elif k == 'U':
            B = player.move_to_board( Loc(0,1), Loc(35, 10) )
        elif k == 'E':
            B.display(str(B.get_all(player.loc)))
        elif k == 'm':
            if player.inv[ID.magic_ball]:
                MagicBallEvent(B).go(player, last_dir)
        elif k == 'i':
            txt = []
            for k, n in player.inv.items():
                item = descr_by_id[k]
                txt.append(f'{item:20}{n}')
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
            if evt in done_events and evt.once:
                continue
            rv = evt(B).go()
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
        key = '[key]' if player.inv[ID.key1] else ''
        win2.addstr(0,0, f'[{STANCES[player.stance]}] [H{player.health}] [{player.inv[ID.coin]} Kashes] {key}')
        win2.refresh()


def debug(*args):
    debug_log.write(str(args) + '\n')
    debug_log.flush()
print=debug

def editor(stdscr, _map):
    begin_x = 0; begin_y = 0; width = 80
    win = newwin(HEIGHT, width, begin_y, begin_x)
    curses.curs_set(True)
    loc = Loc(40, 8)
    brush = None
    B = Board(Loc(0,0))
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
                if brush == blank:
                    B.B[loc.y][loc.x] = [blank]
                elif brush == rock:
                    if B[loc] != rock:
                        B.put(rock, loc)
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
        elif k == 'S':
            B.put(Blocks.steps_l, loc)
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
        elif k == 'G':
            B.put(Blocks.elephant, loc)
        elif k == 'p':
            B.put(Blocks.platform_top, loc)
        elif k == 'g':
            B.put(Blocks.grill, loc)
        elif k == 'F':
            B.put(Blocks.ferry, loc)
        elif k == 'O':
            B.put(Blocks.soldier, loc)
        elif k == 'A':
            B.put(Blocks.bars, loc)
        elif k == 'R':
            B.put(Blocks.rubbish, loc)
        elif k == 'r':
            B.put(Blocks.rabbit, loc)
        elif k == 'T':
            B.put(choice((Blocks.tree1, Blocks.tree2)), loc)
        elif k == 'z':
            B.put(Blocks.guardrail_m, loc)

        elif k == 'o':
            cmds = 'gm gl gr l b ob f'.split()
            cmd = ''
            BL=Blocks
            while 1:
                cmd += win.getkey()
                if cmd == 'gm':
                    B.put(BL.guardrail_m, loc)
                elif cmd == 'gl':
                    B.put(BL.guardrail_l, loc)
                elif cmd == 'gr':
                    B.put(BL.guardrail_r, loc)
                elif cmd == 'l': B.put(BL.locker, loc)
                elif cmd == 'b': B.put(BL.books, loc)
                elif cmd == 'ob': B.put(BL.open_book, loc)
                elif cmd == 't': B.put(BL.tulip, loc)
                elif cmd == 'f': B.put(BL.fountain, loc)
                elif cmd == 'm': B.put(BL.monkey, loc)
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
            return
        B.draw(win)
        tool = 'eraser' if brush==' ' else ('rock' if brush==rock else '')
        win.addstr(0,73, tool)
        win.addstr(0,0,str(loc))
        win.move(loc.y, loc.x)


if __name__ == "__main__":
    argv = sys.argv[1:]
    if first(argv) == 'ed':
        wrapper(editor, argv[1])
    else:
        wrapper(main)
