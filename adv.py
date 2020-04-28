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


class Objects:
    obj = {}
    def __getitem__(self, id):
        return self.obj.get(id)
    def __setitem__(self, id, obj):
        self.obj[id] = obj

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
    fountain = '⛲'
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
    crates = (crate1, crate2, crate3, crate4)

class Stance:
    normal = 1
    fight = 2
    sneaky = 3
STANCES = {v:k for k,v in Stance.__dict__.items()}

class Type:
    # door = 1
    platform_top = 2
    ladder = 3
    fountain = 4
    chair = 5
    door_top_block = 6
    container = 7
    door1 = 8
    crate = 9
    door2 = 10
BLOCKING = [rock, Type.door1, Type.door2, Blocks.block1, Blocks.steps_r, Blocks.steps_l, Type.platform_top, Type.door_top_block]

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

    guard1 = 100
    technician1 = 101
    player = 102
    soldier1 = 103
    robobunny1 = 104
    shopkeeper1 = 105

items_by_id = {v:k for k,v in ID.__dict__.items()}
descr_by_id = copy(items_by_id)
descr_by_id.update({14: 'a jar of syrup', 10: 'a green heart'})

conversations = {
    ID.robobunny1: ['I like to rummage through the rubbish pile.. this area is not closely watched! I hide in the garbage truck and come here when I can. You just have to be very DISCREET!'],
    ID.shopkeeper1: ['Twinsen!? I thought you were arrested?', 'They let me out early for good behaviour!', 'But.. nobody gets out of Citadel alive! I.. I.. have to call the guards.'],
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
        objects[ID.player] = p
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
        for x in range(5):
            row = self.B[-2-x]
            for cell in row[:5-x]:
                cell.append(rock)
        Item(self, Blocks.grill, 'grill', Loc(25, GROUND), id=ID.grill2)
        RoboBunny(self, Loc(50, GROUND), id=ID.robobunny1)
        Item(self, Blocks.rubbish, 'rubbish', Loc(55, GROUND), id=ID.rubbish1)
        Item(self, Blocks.rubbish, 'rubbish', Loc(56, GROUND), id=ID.rubbish1)
        Item(self, Blocks.rubbish, 'rubbish', Loc(57, GROUND), id=ID.rubbish1)
        s = Soldier(self, Loc(70, GROUND), id=ID.soldier1)
        self.soldiers.append(s)

    def board_4(self):
        B = self.B
        lev2 = 10
        loc1 = self.make_steps(Loc(2,GROUND), +1, 9)
        loc2 = self.make_steps(Loc(77,GROUND), -1, 9, Blocks.steps_l)

        row = B[lev2]
        for cell in row[loc1.x+1:loc2.x]:
            cell.append(rock)

        self.labels.append((0,20, "𝓪𝓫𝓮 𝓸𝓵𝓭 𝓼𝓱𝓸𝓹𝓹𝓮"))    # Abe old shoppe
        self.rectangle(Loc(20,1), Loc(30,5), exc=(Loc(20,3), Loc(25,5)) )
        ShopKeeper(self, Loc(21,4), id=ID.shopkeeper1)

        for x in (23,26,27,28,29):
            Item(self, Blocks.shelves, 'shelves', Loc(x,4), id=ID.shelves, type=Type.container)
        self[Loc(27,4)].inv[ID.jar_syrup] = 1

        for y in range(5, lev2):
            Item(self, Blocks.ladder, 'ladder', Loc(25,y), type=Type.ladder)

        loc = Loc(40,GROUND-4)
        self.remove(rock, loc)
        Item(self, Blocks.platform_top, 'platform', loc, id=ID.platform_top1, type=Type.platform_top)
        Item(self, Blocks.coin, 'coin', Loc(45,GROUND), id=ID.coin)
        Item(self, Blocks.grn_heart, 'grn_heart', Loc(50,GROUND), id=ID.grn_heart)
        Item(self, Blocks.grn_heart, 'grn_heart', Loc(55,GROUND), id=ID.grn_heart)

    def board_5(self):
        self.labels.append((0,20, "𝓐𝓷𝓽𝓱𝓸𝓷𝔂 𝓫𝓪𝓻"))
        self.rectangle(Loc(20,1), Loc(60,10), exc=(Loc(20,7), Loc(30,10)))
        for x in range(22,30,2):
            Item(self, Blocks.stool, 'stool', Loc(x,9))
        for y in range(10, GROUND+1):
            Item(self, Blocks.ladder, 'ladder', Loc(30,y), type=Type.ladder)
        loc1 = self.make_steps(Loc(35, 9), +1, 5)
        for x in range(loc1.x+1, 60):
            self.put(rock, Loc(x,loc1.y))
        for x in range(loc1.x+2,loc1.x+12,2):
            Item(self, Blocks.stool, 'stool', Loc(x, loc1.y-1))

    def board_6(self):
        self.labels.append((2,20, "𝒯𝓌𝒾𝓃𝓈𝑒𝓃 𝐻𝑜𝓂𝑒"))
        containers, crates, specials = self.load_map(6)
        containers[0].inv[ID.magic_ball] = 1
        containers[0].inv[ID.key1] = 1
        crates[5].id = ID.crate1

    def board_und1(self):
        containers, crates, specials = self.load_map('und1')
        Item(self, Blocks.grill, 'grill', specials[1], id=ID.grill3)

    def load_map(self, map_num):
        _map = open(f'maps/{map_num}.map').readlines()
        crates = []
        containers = []
        specials = {}
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
                        Item(self, Blocks.door, 'door', loc, type=Type.door1)
                    elif char=='D':
                        Item(self, Blocks.door, 'steel door', loc, type=Type.door2)
                    elif char=='g':
                        Item(self, Blocks.grn_heart, 'grn_heart', loc, id=ID.grn_heart)
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
                    elif char==Blocks.steps_l:
                        self.put(Blocks.steps_l, loc)
                    elif char==Blocks.steps_r:
                        self.put(Blocks.steps_r, loc)
                    elif char in '0123456789':
                        specials[int(char)] = loc
        return containers, crates, specials

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

    def get_ids(self, loc):
        return ids(self.get_all(loc))

    def get_types(self, loc):
        return types(self.get_all(loc))

    def draw(self, win):
        for y, row in enumerate(self.B):
            for x, cell in enumerate(row):
                win.addstr(y,x, str(cell[-1]))
        for y,x,txt in self.labels:
            win.addstr(y,x,txt)
        win.refresh()

    def put(self, obj, loc=None):
        loc = loc or obj.loc
        self.B[loc.y][loc.x].append(obj)

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


def chk_oob(loc, y=0, x=0):
    return 0 <= loc.y+y <= HEIGHT-1 and 0 <= loc.x+x <= 78

def chk_b_oob(loc, y=0, x=0):
    h = len(boards)
    w = len(boards[0])
    debug('chk_b_oob', loc.x, x)
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
        print("dir", dir)
        m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0))[dir]
        new = self.loc.mod(*m)
        self.B.remove(self)
        self.loc = new
        self.B.put(self)

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
    kash = 0
    type = None

    def __init__(self, B, loc=None, put=True, id=None):
        self.B = B
        self.id = id
        self.loc = loc
        self.inv = defaultdict(int)
        if id:
            objects[id] = self
        if put:
            B.put(self)

    def __str__(self):
        return self.char

    def move_to_board(self, b_loc, loc):
        print('in move_to_board')
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

    def talk(self, loc, being):
        for txt in conversations[being.id]:
            w = 78 - loc.x
            lines = (len(txt) // w) + 4
            txt = wrap(txt, w)
            txt = '\n'.join(txt)
            offset_y = lines if loc.y<8 else -lines
            win = newwin(lines, w, loc.y+offset_y, loc.x)
            win.addstr(0,0, txt)
            win.getkey()
            del win

    def _move(self, dir, fly=False):
        m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0))[dir]
        if chk_oob(self.loc, *m):
            return True, self.loc.mod(*m)
        else:
            if self.is_player and chk_b_oob(self.B.loc, *m):
                print('returning LOAD_BOARD')
                return LOAD_BOARD, self.B.loc.mod(*m)
        return 0, 0

    def move(self, dir, fly=False):
        B = self.B
        rv = self._move(dir, fly)
        if rv and (rv[0] == LOAD_BOARD):
            print('move: returning LOAD_BOARD')
            return rv
        new = rv[1]
        if new and isinstance(B[new], Being):
            being = B[new]
            if self.fight_stance or self.hostile:
                self.attack(being)
            elif being.id == ID.robobunny1:
                self.talk(new, being)
            else:
                self.switch_places()    # TODO support direction
            return True, True

        # TODO This is a little messy, doors are by type and keys are by ID
        if new and Type.door1 in B.get_types(new) and self.inv[ID.key1]:
            B.remove(B[new])    # TODO will not work if something is on top of door
            self.inv[ID.key1] -= 1
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
            if B.loc.x==3 and new==Loc(25,5):
                triggered_events.append(ShopKeeperEvent1)

            objs = [o.type for o in B.get_all_obj(new)]
            if not fly and not Type.ladder in objs:
                # fall
                new2 = new
                while 1:
                    new2 = new2.mod(1,0)
                    objs = [o.type for o in B.get_all_obj(new2)]
                    if chk_oob(new2) and B.avail(new2) and not Type.ladder in objs:
                        new = new2
                    else:
                        break

            pick_up = [ID.coin, ID.key1, ID.magic_ball]
            B.remove(self)
            self.loc = new

            if self.is_player:
                items = B.get_all(new)
                for x in reversed(items):
                    if x.id == ID.grn_heart:
                        self.health = min(15, self.health+1)
                        B.remove(x)
                    elif x.id in pick_up:
                        self.inv[x.id] += 1
                        B.remove(x)
                names = [i.name for i in B.get_all(new)]
                plural = len(names)>1
                names = ', '.join(names)
                if names:
                    a = ':' if plural else ' a'
                    Windows.win2.addstr(2,0, f'You see{a} {names}')
            self.put(new)
            if ID.door1 in B.get_ids(self.loc):
                triggered_events.append(AlarmEvent1)
            grills = set((ID.grill1, ID.grill2))
            if self.sneaky_stance and (grills & set(B.get_ids(self.loc))):
                triggered_events.append(ClimbThroughGrillEvent1)
            if self.sneaky_stance and ID.grill3 in B.get_ids(self.loc):
                ClimbThroughGrillEvent2.new = new
                triggered_events.append(ClimbThroughGrillEvent2)

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

        if isinstance(lo, Being):
            B.remove(lo)
            B.remove(self)
            loc = self.loc
            self.put(l)
            lo.put(loc)

    def action(self):
        B=self.B
        c = last( [x for x in B.get_all(self.loc) if x.type==Type.container] )
        objs = B.get_all_obj(self.loc)
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

        else:
            loc = self.loc.mod(1,0)
            x = B[loc] # TODO won't work if something is in the platform tile
            if x and getattr(x,'id',None)==ID.platform_top1:
                PlatformEvent2(B).go()

    def get_top_item(self):
        x = self.B[self.loc]
        return None if x==blank else x

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
    new = None
    def go(self):
        loc = self.new
        player = objects[ID.player]
        bi = self.B.loc.x
        x = 0 if bi==5 else 5
        y = 1 if bi==5 else 0
        b_loc = Loc(x, y)
        Windows.win2.addstr(2,0, 'You climb through the grill into a strange underground area')
        return player.move_to_board(b_loc, Loc(62,10))

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
        for _ in range(45):
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
        dir = 'j' if pl.loc.y == GROUND-5 else 'k'
        for _ in range(45):
            p.move(dir)
            pl.move(dir, fly=1)
            if pl.loc.y in (GROUND, GROUND-5):
                break
            B.draw(Windows.win)
            sleep(0.2)

class ShopKeeperEvent1(Event):
    def go(self):
        pl = objects[ID.player]
        shk = objects[ID.shopkeeper1]
        pl.talk(shk.loc, shk)
        timers.append(Timer(10, ShopKeeperAlarmEvent))

class ShopKeeperAlarmEvent(Event):
    def go(self):
        shk = objects[ID.shopkeeper1]
        if shk.health > 0:
            return Saves().load('start')

def rev_dir(dir):
    return dict(h='l',l='h',j='k',k='j')[dir]

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
    char = 's'

class Technician(Being):
    char = 't'

class RoboBunny(Being):
    char = 'r'

class ShopKeeper(Being):
    char = '🙇'

class NPCs:
    pass
class OtherBeings:
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
        player.B = B
        return player, B

class Windows:
    pass

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
    und1 = Board(Loc(0,1), init_rocks=0)

    player = b1.board_1()
    b2.board_2()
    b3.board_3()
    b4.board_4()
    b5.board_5()
    b6.board_6()
    und1.board_und1()
    boards[:] = ([b1, b2, b3, b4, b5, b6], [und1])

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
        elif k in 'hjkl':
            last_dir = k
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
        elif k == 'i':
            pass
        elif k == ' ':
            player.action()
        elif k == '4':
            B = player.move_to_board( Loc(3,0), Loc(35, GROUND-5) )
        elif k == '5':
            B = player.move_to_board( Loc(4,0), Loc(35, GROUND) )
        elif k == '6':
            B = player.move_to_board( Loc(5,0), Loc(35, GROUND) )
        elif k == 'U':
            B = player.move_to_board( Loc(0,1), Loc(35, 10) )
        elif k == 'm':
            if player.inv[ID.magic_ball]:
                MagicBallEvent(B).go(player, last_dir)

        if k != '.':
            wait_count = 0
        last_cmd = k

        B.guards = [g for g in B.guards if g.health>0]
        B.soldiers = [g for g in B.soldiers if g.health>0]
        for g in B.guards:
            if g.hostile:
                g.attack(player)
        for s in B.soldiers:
            if s.hostile or dist(s, player) <= 5:
                s.hostile = 1
                s.attack(player)

        if player.health <= 0:
            win2.addstr(1, 0, f'Hmm.. it looks like you lost the game!')
            player, B = Saves().load('start')
            objects[ID.player] = player

        for evt in triggered_events:
            debug(evt)
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
                print("triggered_events", triggered_events)
        timers[:] = [t for t in timers if t.turns>0]
        B.draw(win)
        key = '[key]' if player.inv[ID.key1] else ''
        win2.addstr(0,0, f'[{STANCES[player.stance]}] [H{player.health}] [${player.inv[ID.coin]}] {key}')
        win2.refresh()


def debug(*args):
    debug_log.write(str(args) + '\n')
    debug_log.flush()
print=debug

def editor(stdscr, _map):
    begin_x = 0; begin_y = 0; width = 80
    win = newwin(HEIGHT, width, begin_y, begin_x)
    curses.curs_set(True)
    loc = Loc(0,0)
    brush = blank
    B = Board(Loc(0,0))
    B.load_map(_map)
    B.draw(win)
    last_cmd = None
    while 1:
        k = win.getkey()
        if k=='q': return
        elif k in 'hjkl':
            m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0))[k]
            if last_cmd and last_cmd not in 'msSd0123456789':
                if brush == blank:
                    B.B[loc.y][loc.x] = [blank]
                elif brush == rock:
                    if B[loc] != rock:
                        B.put(rock, loc)
            loc = loc.mod(*m)
        elif k == ' ':
            brush = ' '
        elif k == 'r':
            brush = rock
        elif k == 's':
            B.put(Blocks.steps_r, loc)
        elif k == 'S':
            B.put(Blocks.steps_l, loc)
        elif k == 'm':
            B.put(Blocks.smoke_pipe, loc)
        elif k == 'd':
            B.put(Blocks.door, loc)
        elif k in '0123456789':
            B.put(k, loc)
        elif k == 'W':
            with open(f'maps/{_map}.map', 'w') as fp:
                for row in B.B:
                    for cell in row:
                        fp.write(str(cell[-1]))
                    fp.write('\n')
            return
        last_cmd = k
        B.draw(win)
        win.addstr(0,0,str(loc))
        win.move(loc.y, loc.x)


if __name__ == "__main__":
    argv = sys.argv[1:]
    if first(argv) == 'ed':
        wrapper(editor, argv[1])
    else:
        wrapper(main)
